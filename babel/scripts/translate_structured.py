#!/usr/bin/env python3
"""
Structured Translation Script using Mistral Large 3 675B
Returns JSON-structured output for reliable PDF generation.

Key improvements:
- Model returns structured JSON instead of markdown
- Tables as proper data structures
- Images with explicit paths, captions, descriptions
- Equations isolated with original LaTeX
- Paragraphs, headings, lists clearly typed
"""

import os
import sys
import json
import base64
import re
import time
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from typing import Optional

# Configuration
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
MODEL = "mistralai/mistral-large-3-675b-instruct-2512"
API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MAX_WORKERS = 3
MAX_IMAGES_PER_REQUEST = 10

progress_lock = Lock()


# ============================================================================
# Structured Output Schema
# ============================================================================

ELEMENT_TYPES = """
Element types in the JSON output:

1. "heading" - Section/chapter headings
   {
     "type": "heading",
     "level": 1-6,
     "content": "Translated heading text"
   }

2. "paragraph" - Regular text paragraphs
   {
     "type": "paragraph",
     "content": "Translated paragraph text..."
   }

3. "table" - Tabular data
   {
     "type": "table",
     "caption": "Table caption if any",
     "headers": ["Column1", "Column2", ...],
     "rows": [
       ["Cell1", "Cell2", ...],
       ["Cell1", "Cell2", ...]
     ]
   }

4. "equation" - Mathematical formulas (keep LaTeX intact)
   {
     "type": "equation",
     "latex": "\\frac{a}{b} = c",
     "inline": false,
     "description": "Optional description of what the equation represents"
   }

5. "image" - Figure/diagram reference
   {
     "type": "image",
     "path": "extracted_chunk_XXX/images/filename.jpg",
     "caption": "Figure caption translated to English",
     "description": "Technical description of what the image shows"
   }

6. "list" - Bulleted or numbered lists
   {
     "type": "list",
     "ordered": true/false,
     "items": ["Item 1", "Item 2", ...]
   }

7. "code" - Code blocks or technical specifications
   {
     "type": "code",
     "content": "Technical specification text"
   }
"""


# ============================================================================
# API Functions
# ============================================================================

def encode_image(image_path: str) -> str:
    """Encode image to base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_image_mime_type(image_path: str) -> str:
    """Get MIME type based on file extension."""
    ext = Path(image_path).suffix.lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }
    return mime_types.get(ext, "image/jpeg")


def call_mistral_api(messages: list, max_tokens: int = 8192) -> Optional[str]:
    """Call Mistral API."""
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.1,
        "top_p": 0.95
    }
    
    for attempt in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            elif response.status_code == 429:
                wait_time = (attempt + 1) * 20
                print(f"      Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"      API error {response.status_code}: {response.text[:200]}")
                time.sleep(5)
                continue
                
        except Exception as e:
            print(f"      Error: {e}")
            time.sleep(5)
            continue
    
    return None


# ============================================================================
# Image Handling
# ============================================================================

def find_chunk_images(chunk_num: int, output_dir: str) -> list:
    """Find all images for a chunk."""
    chunk_dir = Path(output_dir) / f"extracted_chunk_{chunk_num:03d}" / "images"
    images = []
    
    if chunk_dir.exists():
        for img_file in sorted(chunk_dir.glob("*")):
            if img_file.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                images.append({
                    "path": str(img_file),
                    "filename": img_file.name,
                    "relative_path": f"extracted_chunk_{chunk_num:03d}/images/{img_file.name}"
                })
    
    return images


def extract_image_refs_from_text(text: str) -> list:
    """Extract image references from markdown text."""
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    matches = re.findall(pattern, text)
    return [{"caption": m[0], "path": m[1]} for m in matches]


# ============================================================================
# Structured Translation
# ============================================================================

def build_structured_prompt(chunk_text: str, chunk_num: int, images: list, image_refs: list) -> str:
    """Build prompt for structured JSON output."""
    
    prompt = f"""You are translating a Chinese technical document about the Spey MK202 aircraft engine to English.

=== TASK ===
Translate the Chinese text below and return a structured JSON response.

=== OUTPUT FORMAT ===
Return ONLY valid JSON with this structure:
{{
  "elements": [
    // Array of content elements in order
  ],
  "summary": "Brief 1-sentence summary of this section"
}}

{ELEMENT_TYPES}

=== CRITICAL RULES ===

1. **TRANSLATE** all Chinese text to English accurately
2. **PRESERVE** technical terminology, numbers, units exactly
3. **KEEP LaTeX INTACT** in equations - do not convert \\frac, \\sigma, etc.
4. **IMAGE PATHS** - Use these exact paths for any images:
"""
    
    # Add image path mappings
    if images:
        prompt += "\n   Available images in this chunk:\n"
        for img in images:
            prompt += f"   - {img['relative_path']}\n"
    
    if image_refs:
        prompt += "\n   Image references found in text (use these paths):\n"
        for ref in image_refs:
            prompt += f"   - Caption: '{ref['caption']}' -> Path: {ref['path']}\n"
    
    prompt += f"""
5. **TABLES** - Convert to proper headers/rows arrays, translate content
6. **LISTS** - Keep as structured items array
7. **ORDER** - Maintain the exact order of elements as in source

=== CHINESE TEXT (Chunk {chunk_num}) ===
---
{chunk_text}
---

Return the JSON response:"""

    return prompt


def translate_chunk_structured(chunk_num: int, chunk_text: str, output_dir: str, 
                                start_page: int = None, end_page: int = None) -> dict:
    """Translate a chunk and return structured output."""
    
    # Find images
    images = find_chunk_images(chunk_num, output_dir)
    image_refs = extract_image_refs_from_text(chunk_text)
    
    # Build message content
    content = []
    
    # Text prompt
    prompt = build_structured_prompt(chunk_text, chunk_num, images, image_refs)
    content.append({"type": "text", "text": prompt})
    
    # Add images for visual analysis
    images_to_process = images[:MAX_IMAGES_PER_REQUEST]
    for img in images_to_process:
        try:
            img_data = encode_image(img["path"])
            mime_type = get_image_mime_type(img["path"])
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{img_data}"}
            })
        except Exception as e:
            print(f"      Warning: Could not load image {img['path']}: {e}")
    
    messages = [{"role": "user", "content": content}]
    
    # Call API
    result = call_mistral_api(messages)
    
    if not result:
        return {
            "chunk_num": chunk_num,
            "success": False,
            "error": "API call failed",
            "elements": [],
            "raw_response": None
        }
    
    # Parse JSON response
    try:
        # Try to extract JSON from response (model might include extra text)
        json_match = re.search(r'\{[\s\S]*\}', result)
        if json_match:
            json_str = json_match.group()
            
            # Fix common JSON escape issues from LLM output
            def fix_escapes(s):
                def escape_handler(match):
                    char_after = match.group(1)
                    if char_after in ('"', '\\', '/', 'b', 'f', 'n', 'r', 't'):
                        return '\\' + char_after
                    if char_after == 'u':
                        return '\\u'
                    return '\\\\' + char_after
                return re.sub(r'\\(.)', escape_handler, s)
            
            # Fix common JSON syntax issues from LLM
            def fix_json_syntax(s):
                # Remove trailing commas before } or ]
                s = re.sub(r',(\s*[}\]])', r'\1', s)
                # Add missing commas between } and { or } and "
                s = re.sub(r'\}(\s*)\{', r'},\1{', s)
                s = re.sub(r'\}(\s*)"', r'},\1"', s)
                # Add missing commas between ] and { or ] and "
                s = re.sub(r'\](\s*)\{', r'],\1{', s)
                s = re.sub(r'\](\s*)"', r'],\1"', s)
                # Add missing commas between string values: "..." "..."
                s = re.sub(r'"(\s+)"(?=[a-zA-Z_])', r'",\1"', s)
                return s
            
            # Apply fixes
            json_str_fixed = fix_escapes(json_str)
            json_str_fixed = fix_json_syntax(json_str_fixed)
            
            try:
                parsed = json.loads(json_str_fixed)
            except json.JSONDecodeError:
                # Try more aggressive fixes
                # Sometimes LLM outputs unquoted keys
                json_str_fixed = re.sub(r'(\{|\,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_str_fixed)
                parsed = json.loads(json_str_fixed)
            
            # Build page range string
            original_pages = None
            if start_page and end_page:
                original_pages = f"{start_page}-{end_page}" if start_page != end_page else str(start_page)
            
            return {
                "chunk_num": chunk_num,
                "success": True,
                "original_pages": original_pages,
                "elements": parsed.get("elements", []),
                "summary": parsed.get("summary", ""),
                "images_available": len(images),
                "images_processed": len(images_to_process),
                "raw_response": result
            }
        else:
            # Fallback: treat entire response as a paragraph
            original_pages = None
            if start_page and end_page:
                original_pages = f"{start_page}-{end_page}" if start_page != end_page else str(start_page)
            
            return {
                "chunk_num": chunk_num,
                "success": True,
                "original_pages": original_pages,
                "elements": [{"type": "paragraph", "content": result}],
                "summary": "",
                "images_available": len(images),
                "images_processed": len(images_to_process),
                "raw_response": result,
                "parse_warning": "Could not parse JSON, used raw text"
            }
    except json.JSONDecodeError as e:
        # Even after fixes, still failed - use raw text
        return {
            "chunk_num": chunk_num,
            "success": True,
            "elements": [{"type": "paragraph", "content": result}],
            "summary": "",
            "images_available": len(images),
            "images_processed": len(images_to_process),
            "raw_response": result,
            "parse_warning": f"JSON parse error: {e}"
        }


# ============================================================================
# Progress Management
# ============================================================================

def load_progress(progress_file: str) -> dict:
    """Load translation progress."""
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"completed_chunks": [], "translations": {}}


def save_progress(progress_file: str, progress: dict):
    """Save translation progress."""
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def parse_chunks_from_markdown(content: str) -> list:
    """Parse combined markdown into chunks."""
    # Match both formats: (Pages X-Y) and (Original Pages X-Y)
    chunk_pattern = r'## Chunk (\d+)(?: \((?:Original )?Pages (\d+)-(\d+)\))?'
    
    chunks = []
    parts = re.split(chunk_pattern, content)
    
    if parts[0].strip():
        chunks.append({"num": 0, "text": parts[0].strip(), "start_page": None, "end_page": None})
    
    i = 1
    while i < len(parts):
        if i + 3 < len(parts):
            chunk_num = int(parts[i])
            start_page = int(parts[i+1]) if parts[i+1] else None
            end_page = int(parts[i+2]) if parts[i+2] else None
            chunk_text = parts[i + 3].strip() if i + 3 < len(parts) else ""
            
            if chunk_text:
                chunks.append({
                    "num": chunk_num,
                    "text": chunk_text,
                    "start_page": start_page,
                    "end_page": end_page
                })
            i += 4
        else:
            break
    
    return chunks


# ============================================================================
# Main Translation Function
# ============================================================================

def translate_document_structured(input_file: str, output_dir: str):
    """Main translation function with structured output."""
    
    print(f"Loading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Total content: {len(content)} characters")
    
    # Parse chunks
    chunks = parse_chunks_from_markdown(content)
    print(f"Found {len(chunks)} chunks to translate")
    
    # Count images
    total_images = sum(len(find_chunk_images(c["num"], output_dir)) for c in chunks)
    print(f"Total images available: {total_images}")
    
    # Progress tracking
    progress_file = os.path.join(output_dir, "structured_translation_progress.json")
    output_file = os.path.join(output_dir, "translated_structured.json")
    
    progress = load_progress(progress_file)
    completed_chunks = set(progress.get("completed_chunks", []))
    translations = progress.get("translations", {})
    
    if completed_chunks:
        print(f"Resuming: {len(completed_chunks)}/{len(chunks)} chunks done")
    
    chunks_to_translate = [c for c in chunks if c["num"] not in completed_chunks]
    
    print(f"\n{'='*60}")
    print(f"Model: {MODEL}")
    print(f"Chunks to translate: {len(chunks_to_translate)}")
    print(f"Output format: Structured JSON")
    print(f"{'='*60}\n")
    
    def process_chunk(chunk):
        chunk_num = chunk["num"]
        chunk_text = chunk["text"]
        start_page = chunk.get("start_page")
        end_page = chunk.get("end_page")
        images = find_chunk_images(chunk_num, output_dir)
        
        page_info = f" [pages {start_page}-{end_page}]" if start_page and end_page else ""
        print(f"  [Chunk {chunk_num:02d}]{page_info} Translating ({len(chunk_text)} chars, {len(images)} images)...")
        
        result = translate_chunk_structured(chunk_num, chunk_text, output_dir, start_page, end_page)
        
        if result["success"]:
            with progress_lock:
                translations[str(chunk_num)] = result
                completed_chunks.add(chunk_num)
                progress["completed_chunks"] = list(completed_chunks)
                progress["translations"] = translations
                save_progress(progress_file, progress)
            
            elem_count = len(result.get("elements", []))
            warning = " ⚠ " + result.get("parse_warning", "") if result.get("parse_warning") else ""
            print(f"  [Chunk {chunk_num:02d}] ✓ Done ({elem_count} elements){warning}")
            return result
        else:
            print(f"  [Chunk {chunk_num:02d}] ✗ Failed: {result.get('error', 'Unknown')}")
            return None
    
    # Process chunks
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_chunk, chunk): chunk for chunk in chunks_to_translate}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                chunk = futures[future]
                print(f"  [Chunk {chunk['num']}] Error: {e}")
    
    # Compile final structured output
    print("\nCompiling structured output...")
    
    all_elements = []
    total_element_counts = {
        "heading": 0, "paragraph": 0, "table": 0,
        "equation": 0, "image": 0, "list": 0, "code": 0
    }
    
    for chunk in sorted(chunks, key=lambda x: x["num"]):
        chunk_num = chunk["num"]
        if str(chunk_num) in translations:
            chunk_data = translations[str(chunk_num)]
            elements = chunk_data.get("elements", [])
            
            # Add chunk marker
            if chunk_num > 0:
                page_info = ""
                if chunk.get("start_page") and chunk.get("end_page"):
                    page_info = f" (Pages {chunk['start_page']}-{chunk['end_page']})"
                
                all_elements.append({
                    "type": "section_marker",
                    "chunk_num": chunk_num,
                    "page_info": page_info
                })
            
            # Add elements
            for elem in elements:
                all_elements.append(elem)
                elem_type = elem.get("type", "unknown")
                if elem_type in total_element_counts:
                    total_element_counts[elem_type] += 1
    
    # Save structured output
    final_output = {
        "metadata": {
            "source_file": input_file,
            "total_chunks": len(chunks),
            "translated_chunks": len(completed_chunks),
            "total_images": total_images,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        },
        "element_counts": total_element_counts,
        "elements": all_elements
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print("STRUCTURED TRANSLATION COMPLETE!")
    print(f"{'='*60}")
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Translated: {len(completed_chunks)}")
    print(f"  Total elements: {len(all_elements)}")
    print(f"  Element breakdown:")
    for etype, count in total_element_counts.items():
        if count > 0:
            print(f"    - {etype}: {count}")
    print(f"  Output: {output_file}")
    
    return output_file


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    if not NVIDIA_API_KEY:
        print("Error: NVIDIA_API_KEY environment variable not set")
        sys.exit(1)
    
    input_file = "/Users/avinash/Desktop/project/minerU/engine_output/combined_extracted.md"
    output_dir = "/Users/avinash/Desktop/project/minerU/engine_output"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    translate_document_structured(input_file, output_dir)
