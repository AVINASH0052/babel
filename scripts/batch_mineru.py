#!/usr/bin/env python3
"""
Batch MinerU processor for large scanned PDFs.
Splits PDF into chunks and processes each through MinerU HuggingFace Space.
"""
import os
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


def split_pdf(input_path: str, output_dir: str, pages_per_chunk: int = 20) -> list[str]:
    """Split a large PDF into smaller chunks."""
    doc = fitz.open(input_path)
    total_pages = len(doc)
    
    chunks_dir = Path(output_dir) / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    
    chunk_paths = []
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
        
        chunk_paths.append(str(chunk_path))
        print(f"  Created chunk {chunk_num}: pages {start_page+1}-{end_page}")
    
    doc.close()
    print(f"✓ Split into {len(chunk_paths)} chunks of {pages_per_chunk} pages each")
    return chunk_paths


def process_chunk_mineru(
    client: Client,
    chunk_path: str,
    output_dir: str,
    chunk_num: int,
    max_retries: int = 3
) -> dict:
    """Process a single chunk through MinerU."""
    
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
            if zip_path and os.path.exists(zip_path):
                extract_dir = Path(output_dir) / f"extracted_chunk_{chunk_num:03d}"
                extract_dir.mkdir(parents=True, exist_ok=True)
                
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(str(extract_dir))
                
                # Find markdown files in extracted content
                for md_file in extract_dir.rglob("*.md"):
                    with open(md_file, 'r', encoding='utf-8') as f:
                        extracted_content += f.read() + "\n\n"
            
            # Use markdown_text if no extracted content
            final_content = extracted_content if extracted_content else markdown_text
            
            return {
                "chunk_num": chunk_num,
                "chunk_path": chunk_path,
                "success": True,
                "markdown": final_content,
                "zip_path": zip_path,
                "layout_pdf": layout_pdf
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
                    "success": False,
                    "error": str(e),
                    "markdown": ""
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
    
    # Split PDF into chunks
    print(f"\nSplitting PDF into {pages_per_chunk}-page chunks...")
    chunk_paths = split_pdf(input_path, output_dir, pages_per_chunk)
    
    # Filter chunks based on start/end
    if end_chunk is None:
        end_chunk = len(chunk_paths)
    
    chunks_to_process = chunk_paths[start_chunk-1:end_chunk]
    print(f"\nProcessing chunks {start_chunk} to {end_chunk} ({len(chunks_to_process)} chunks)")
    
    # Process each chunk
    results = []
    combined_markdown = ""
    
    for i, chunk_path in enumerate(chunks_to_process):
        chunk_num = start_chunk + i
        
        # Check if chunk was already processed
        chunk_result_file = output_path / f"chunk_{chunk_num:03d}_result.json"
        if chunk_result_file.exists():
            print(f"\n[{chunk_num}/{end_chunk}] Skipping {Path(chunk_path).name} (already processed)")
            with open(chunk_result_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
            results.append(result)
            if result.get("success"):
                combined_markdown += f"\n\n## Chunk {chunk_num}\n\n"
                combined_markdown += result.get("markdown", "")
            continue
        
        print(f"\n[{chunk_num}/{end_chunk}] Processing {Path(chunk_path).name}...")
        
        result = process_chunk_mineru(client, chunk_path, output_dir, chunk_num)
        results.append(result)
        
        if result["success"]:
            print(f"  ✓ Success - extracted {len(result['markdown'])} chars")
            combined_markdown += f"\n\n## Chunk {chunk_num}\n\n"
            combined_markdown += result["markdown"]
        else:
            print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
        
        # Save individual chunk result for resume capability
        chunk_result_file = output_path / f"chunk_{chunk_num:03d}_result.json"
        with open(chunk_result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Save progress after each chunk
        progress_file = output_path / "progress.json"
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump({
                "last_chunk": chunk_num,
                "total_chunks": len(chunk_paths),
                "successful": sum(1 for r in results if r["success"]),
                "failed": sum(1 for r in results if not r["success"])
            }, f, indent=2)
        
        # Small delay between chunks to avoid rate limiting
        if i < len(chunks_to_process) - 1:
            time.sleep(5)
    
    # Save combined markdown
    combined_file = output_path / "combined_extracted.md"
    with open(combined_file, 'w', encoding='utf-8') as f:
        f.write(f"# Extracted Content from {Path(input_path).name}\n")
        f.write(f"Processed on: {datetime.now().isoformat()}\n\n")
        f.write(combined_markdown)
    
    # Save results summary
    summary = {
        "input_file": input_path,
        "total_chunks": len(chunk_paths),
        "processed_chunks": len(results),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
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
