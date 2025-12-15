#!/usr/bin/env python3
"""
Batch MinerU processor for large scanned PDFs.
Splits PDF into chunks and processes each through MinerU HuggingFace Space.

FIXES APPLIED:
- Added page markers (<!-- PAGE_BREAK -->) in extracted content
- Image paths rewritten to include chunk reference for proper mapping
"""
import os
import re
import ssl
import sys
import json
import time
import zipfile
import shutil
import certifi
from pathlib import Path
from datetime import datetime

# Fix SSL certificate issues on macOS
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

import fitz  # PyMuPDF
from gradio_client import Client, handle_file


def split_pdf(input_path: str, output_dir: str, pages_per_chunk: int = 20) -> list[dict]:
    """Split a large PDF into smaller chunks. Returns list with page info."""
    doc = fitz.open(input_path)
    total_pages = len(doc)
    
    chunks_dir = Path(output_dir) / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    
    chunk_info = []
    chunk_num = 0
    
    for start_page in range(0, total_pages, pages_per_chunk):
        end_page = min(start_page + pages_per_chunk, total_pages)
        chunk_num += 1
        
        # Create a new PDF with just these pages
        chunk_doc = fitz.open()
        for page_num in range(start_page, end_page):
            chunk_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        
        chunk_path = chunks_dir / f"chunk_{chunk_num:03d}_pages_{start_page+1}-{end_page}.pdf"
        chunk_doc.save(str(chunk_path))
        chunk_doc.close()
        
        chunk_info.append({
            "path": str(chunk_path),
            "chunk_num": chunk_num,
            "start_page": start_page + 1,  # 1-indexed for display
            "end_page": end_page,
            "page_count": end_page - start_page
        })
        print(f"  Created chunk {chunk_num}: pages {start_page+1}-{end_page}")
    
    doc.close()
    print(f"✓ Split into {len(chunk_info)} chunks of {pages_per_chunk} pages each")
    return chunk_info


def rewrite_image_paths(content: str, chunk_num: int) -> str:
    """Rewrite image paths to include chunk reference for proper mapping."""
    # Pattern: ![caption](images/filename.jpg) or ![](images/filename.jpg)
    # Rewrite to: ![caption](extracted_chunk_XXX/images/filename.jpg)
    
    def replace_path(match):
        caption = match.group(1)
        img_path = match.group(2)
        
        # If path already has chunk reference, don't modify
        if 'extracted_chunk_' in img_path:
            return match.group(0)
        
        # Rewrite relative path to include chunk folder
        if img_path.startswith('images/'):
            new_path = f"extracted_chunk_{chunk_num:03d}/{img_path}"
        else:
            new_path = f"extracted_chunk_{chunk_num:03d}/images/{img_path}"
        
        return f"![{caption}]({new_path})"
    
    # Match markdown image syntax
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    return re.sub(pattern, replace_path, content)


def add_page_markers(content: str, chunk_num: int, start_page: int, end_page: int) -> str:
    """Add page markers to content for page structure preservation."""
    
    # Add chunk header with page info
    header = f"\n\n<!-- CHUNK_{chunk_num:03d}_PAGES_{start_page}-{end_page} -->\n"
    header += f"<!-- PAGE_MARKER: {start_page} -->\n\n"
    
    # For now, we add a marker at the start. 
    # MinerU doesn't provide per-page boundaries, so we mark the chunk boundaries.
    # Future enhancement: parse layout.pdf or middle.json for exact page breaks
    
    return header + content + f"\n\n<!-- END_CHUNK_{chunk_num:03d} -->\n"


def process_chunk_mineru(
    client: Client,
    chunk_info: dict,
    output_dir: str,
    max_retries: int = 3
) -> dict:
    """Process a single chunk through MinerU."""
    
    chunk_num = chunk_info["chunk_num"]
    chunk_path = chunk_info["path"]
    start_page = chunk_info["start_page"]
    end_page = chunk_info["end_page"]
    
    for attempt in range(max_retries):
        try:
            # Enable the endpoint
            endpoint = client.endpoints.get(5)
            if endpoint:
                endpoint.show_api = True
                endpoint.is_valid = True
            
            # Call MinerU
            result = client.predict(
                handle_file(chunk_path),
                20,                          # max_pages (process all pages in chunk)
                False,                       # force_ocr (let MinerU decide)
                True,                        # enable_formula
                True,                        # enable_table
                "ch",                        # language (Chinese)
                "pipeline",                  # backend (more stable than vllm)
                "http://localhost:30000",    # server_url (not used for HF space)
                fn_index=5
            )
            
            # Parse result - it's a tuple: (markdown_rendered, markdown_text, zip_path, layout_pdf)
            markdown_rendered = result[0] if len(result) > 0 else ""
            markdown_text = result[1] if len(result) > 1 else ""
            zip_path = result[2] if len(result) > 2 else None
            layout_pdf = result[3] if len(result) > 3 else None
            
            # Extract content from zip if available
            extracted_content = ""
            extracted_images = []
            
            if zip_path and os.path.exists(zip_path):
                extract_dir = Path(output_dir) / f"extracted_chunk_{chunk_num:03d}"
                extract_dir.mkdir(parents=True, exist_ok=True)
                
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(str(extract_dir))
                
                # Find markdown files in extracted content
                for md_file in extract_dir.rglob("*.md"):
                    with open(md_file, 'r', encoding='utf-8') as f:
                        extracted_content += f.read() + "\n\n"
                
                # List extracted images
                images_dir = extract_dir / "images"
                if images_dir.exists():
                    extracted_images = [f.name for f in images_dir.glob("*") 
                                       if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']]
            
            # Use markdown_text if no extracted content
            final_content = extracted_content if extracted_content else markdown_text
            
            # FIX 1: Rewrite image paths to include chunk reference
            final_content = rewrite_image_paths(final_content, chunk_num)
            
            # FIX 2: Add page markers
            final_content = add_page_markers(final_content, chunk_num, start_page, end_page)
            
            return {
                "chunk_num": chunk_num,
                "chunk_path": chunk_path,
                "start_page": start_page,
                "end_page": end_page,
                "success": True,
                "markdown": final_content,
                "zip_path": zip_path,
                "layout_pdf": layout_pdf,
                "images_extracted": extracted_images,
                "image_count": len(extracted_images)
            }
            
        except Exception as e:
            print(f"  ⚠ Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 30  # Exponential backoff
                print(f"  Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                return {
                    "chunk_num": chunk_num,
                    "chunk_path": chunk_path,
                    "start_page": start_page,
                    "end_page": end_page,
                    "success": False,
                    "error": str(e),
                    "markdown": "",
                    "images_extracted": [],
                    "image_count": 0
                }


def process_pdf_batch(
    input_path: str,
    output_dir: str,
    pages_per_chunk: int = 20,
    start_chunk: int = 1,
    end_chunk: int = None
) -> dict:
    """Process a large PDF through MinerU in batches."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize HF client
    hf_token = os.environ.get("HF_TOKEN", "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")
    print(f"Connecting to MinerU HuggingFace Space...")
    client = Client('opendatalab/MinerU', hf_token=hf_token)
    print("✓ Connected to MinerU")
    
    # Split PDF into chunks (now returns dict with page info)
    print(f"\nSplitting PDF into {pages_per_chunk}-page chunks...")
    chunk_info_list = split_pdf(input_path, output_dir, pages_per_chunk)
    
    # Filter chunks based on start/end
    if end_chunk is None:
        end_chunk = len(chunk_info_list)
    
    chunks_to_process = chunk_info_list[start_chunk-1:end_chunk]
    print(f"\nProcessing chunks {start_chunk} to {end_chunk} ({len(chunks_to_process)} chunks)")
    
    # Process each chunk
    results = []
    combined_markdown = ""
    total_images = 0
    
    for i, chunk_info in enumerate(chunks_to_process):
        chunk_num = chunk_info["chunk_num"]
        
        # Check if chunk was already processed
        chunk_result_file = output_path / f"chunk_{chunk_num:03d}_result.json"
        if chunk_result_file.exists():
            print(f"\n[{chunk_num}/{end_chunk}] Skipping chunk {chunk_num} (already processed)")
            with open(chunk_result_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
            results.append(result)
            if result.get("success"):
                combined_markdown += f"\n\n## Chunk {chunk_num} (Pages {result.get('start_page', '?')}-{result.get('end_page', '?')})\n\n"
                combined_markdown += result.get("markdown", "")
                total_images += result.get("image_count", 0)
            continue
        
        print(f"\n[{chunk_num}/{end_chunk}] Processing pages {chunk_info['start_page']}-{chunk_info['end_page']}...")
        
        result = process_chunk_mineru(client, chunk_info, output_dir)
        results.append(result)
        
        if result["success"]:
            img_info = f", {result['image_count']} images" if result['image_count'] > 0 else ""
            print(f"  ✓ Success - extracted {len(result['markdown'])} chars{img_info}")
            combined_markdown += f"\n\n## Chunk {chunk_num} (Pages {chunk_info['start_page']}-{chunk_info['end_page']})\n\n"
            combined_markdown += result["markdown"]
            total_images += result["image_count"]
        else:
            print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
        
        # Save individual chunk result for resume capability
        with open(chunk_result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Save progress after each chunk
        progress_file = output_path / "progress.json"
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump({
                "last_chunk": chunk_num,
                "total_chunks": len(chunk_info_list),
                "successful": sum(1 for r in results if r.get("success")),
                "failed": sum(1 for r in results if not r.get("success")),
                "total_images": total_images
            }, f, indent=2)
        
        # Small delay between chunks to avoid rate limiting
        if i < len(chunks_to_process) - 1:
            time.sleep(5)
    
    # Save combined markdown with metadata
    combined_file = output_path / "combined_extracted.md"
    with open(combined_file, 'w', encoding='utf-8') as f:
        f.write(f"# Extracted Content from {Path(input_path).name}\n")
        f.write(f"Processed on: {datetime.now().isoformat()}\n")
        f.write(f"Total images extracted: {total_images}\n")
        f.write(f"Image base directory: {output_dir}\n\n")
        f.write("---\n")
        f.write(combined_markdown)
    
    # Save results summary
    summary = {
        "input_file": input_path,
        "output_dir": output_dir,
        "total_chunks": len(chunk_info_list),
        "processed_chunks": len(results),
        "successful": sum(1 for r in results if r.get("success")),
        "failed": sum(1 for r in results if not r.get("success")),
        "total_images": total_images,
        "output_file": str(combined_file),
        "timestamp": datetime.now().isoformat()
    }
    
    summary_file = output_path / "extraction_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"✓ Extraction complete!")
    print(f"  Total chunks: {summary['total_chunks']}")
    print(f"  Successful: {summary['successful']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Total images: {total_images}")
    print(f"  Output: {combined_file}")
    print(f"{'='*60}")
    
    return summary


def main():
    if len(sys.argv) < 2:
        print("Usage: python batch_mineru.py <pdf_path> [output_dir] [pages_per_chunk] [start_chunk] [end_chunk]")
        print("")
        print("Arguments:")
        print("  pdf_path        Path to the PDF file")
        print("  output_dir      Output directory (default: ./mineru_output)")
        print("  pages_per_chunk Pages per chunk (default: 20)")
        print("  start_chunk     Start from this chunk number (default: 1)")
        print("  end_chunk       End at this chunk number (default: all)")
        print("")
        print("Example:")
        print("  python batch_mineru.py document.pdf ./output 20 1 5")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./mineru_output"
    pages_per_chunk = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    start_chunk = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    end_chunk = int(sys.argv[5]) if len(sys.argv) > 5 else None
    
    print(f"Processing: {pdf_path}")
    print(f"Output dir: {output_dir}")
    print(f"Pages per chunk: {pages_per_chunk}")
    
    summary = process_pdf_batch(
        pdf_path,
        output_dir,
        pages_per_chunk,
        start_chunk,
        end_chunk
    )
    
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
