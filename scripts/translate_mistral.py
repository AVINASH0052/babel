#!/usr/bin/env python3
"""
Unified Translation Script using Mistral Large 3 675B
- Translates Chinese text to English
- Analyzes images (up to 10 per request)
- Uses single model for everything
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

# Configuration
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
MODEL = "mistralai/mistral-large-3-675b-instruct-2512"
API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MAX_WORKERS = 2  # Parallel chunk processing
MAX_IMAGES_PER_REQUEST = 10

# Lock for thread-safe progress saving
progress_lock = Lock()


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


def call_mistral_api(messages: list, max_tokens: int = 4096) -> str:
    """Call Mistral API with text and/or images."""
    
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
            response = requests.post(API_URL, headers=headers, json=payload, timeout=180)
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            elif response.status_code == 429:
                # Rate limited - wait and retry
                wait_time = (attempt + 1) * 15
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


def find_chunk_images(chunk_num: int, output_dir: str) -> list:
    """Find all images for a chunk."""
    chunk_dir = Path(output_dir) / f"extracted_chunk_{chunk_num:03d}" / "images"
    images = []
    
    if chunk_dir.exists():
        for img_file in sorted(chunk_dir.glob("*")):
            if img_file.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                images.append(str(img_file))
    
    return images


def translate_chunk_with_images(chunk_num: int, chunk_text: str, output_dir: str) -> dict:
    """Translate a chunk's text and analyze its images using Mistral."""
    
    # Find images for this chunk
    images = find_chunk_images(chunk_num, output_dir)
    
    # Build the message content
    content = []
    
    # Limit to MAX_IMAGES_PER_REQUEST
    images_to_process = images[:MAX_IMAGES_PER_REQUEST] if images else []
    
    # Build prompt
    prompt = f"""You are translating a Chinese technical document about the Spey MK202 aircraft engine to English.

TASK: Translate the following Chinese text to English accurately. Preserve:
- All technical terminology (engine parts, measurements, specifications)
- Numerical values and units exactly as shown
- Table structures (use markdown tables)
- Mathematical formulas and equations
- Figure/image references
- Section headings and structure

"""
    
    if images_to_process:
        prompt += f"""
This section contains {len(images_to_process)} figure(s)/diagram(s). After translating the text:
1. Provide a brief technical description of each image
2. Note any Chinese text visible in the images and translate it
3. Describe graphs, schematics, or data shown

"""
    
    prompt += f"""CHINESE TEXT TO TRANSLATE:
---
{chunk_text}
---

Provide the complete English translation:"""
    
    # Add text prompt
    content.append({"type": "text", "text": prompt})
    
    # Add images if any
    for img_path in images_to_process:
        try:
            img_data = encode_image(img_path)
            mime_type = get_image_mime_type(img_path)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{img_data}"
                }
            })
        except Exception as e:
            print(f"      Warning: Could not load image {img_path}: {e}")
    
    messages = [{"role": "user", "content": content}]
    
    # Call API
    result = call_mistral_api(messages, max_tokens=8192)
    
    return {
        "chunk_num": chunk_num,
        "original_text": chunk_text,
        "translated_text": result,
        "images_processed": len(images_to_process),
        "total_images": len(images)
    }


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
    """Parse the combined markdown into chunks."""
    # Split by chunk headers
    chunk_pattern = r'## Chunk (\d+)'
    
    chunks = []
    parts = re.split(chunk_pattern, content)
    
    # First part is pre-chunk content (if any)
    if parts[0].strip():
        chunks.append({"num": 0, "text": parts[0].strip()})
    
    # Remaining parts are (chunk_num, chunk_content) pairs
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            chunk_num = int(parts[i])
            chunk_text = parts[i + 1].strip()
            if chunk_text:
                chunks.append({"num": chunk_num, "text": chunk_text})
    
    return chunks


def translate_document(input_file: str, output_dir: str):
    """Main translation function."""
    
    # Load extracted markdown
    print(f"Loading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Total content: {len(content)} characters")
    
    # Parse into chunks
    chunks = parse_chunks_from_markdown(content)
    print(f"Found {len(chunks)} chunks to translate")
    
    # Count total images
    total_images = 0
    for chunk in chunks:
        images = find_chunk_images(chunk["num"], output_dir)
        total_images += len(images)
    print(f"Total images to analyze: {total_images}")
    
    # Progress file
    progress_file = os.path.join(output_dir, "mistral_translation_progress.json")
    output_file = os.path.join(output_dir, "translated_english_mistral.md")
    
    # Load existing progress
    progress = load_progress(progress_file)
    completed_chunks = set(progress.get("completed_chunks", []))
    translations = progress.get("translations", {})
    
    if completed_chunks:
        print(f"Resuming: {len(completed_chunks)}/{len(chunks)} chunks already done")
    
    # Find chunks to translate
    chunks_to_translate = [c for c in chunks if c["num"] not in completed_chunks]
    
    print(f"\n{'='*60}")
    print(f"Model: {MODEL}")
    print(f"Chunks to translate: {len(chunks_to_translate)}")
    print(f"Parallel workers: {MAX_WORKERS}")
    print(f"{'='*60}\n")
    
    def process_chunk(chunk):
        chunk_num = chunk["num"]
        chunk_text = chunk["text"]
        images = find_chunk_images(chunk_num, output_dir)
        
        img_str = f" + {len(images)} images" if images else ""
        print(f"  [Chunk {chunk_num:02d}] Translating ({len(chunk_text)} chars{img_str})...")
        
        result = translate_chunk_with_images(chunk_num, chunk_text, output_dir)
        
        if result["translated_text"]:
            with progress_lock:
                translations[str(chunk_num)] = result["translated_text"]
                completed_chunks.add(chunk_num)
                progress["completed_chunks"] = list(completed_chunks)
                progress["translations"] = translations
                save_progress(progress_file, progress)
            
            img_info = f", {result['images_processed']} images analyzed" if result['images_processed'] > 0 else ""
            print(f"  [Chunk {chunk_num:02d}] ✓ Done ({len(result['translated_text'])} chars{img_info})")
            print(f"      Progress: {len(completed_chunks)}/{len(chunks)} ({100*len(completed_chunks)/len(chunks):.1f}%)")
            return result
        else:
            print(f"  [Chunk {chunk_num:02d}] ✗ Failed")
            return None
    
    # Process chunks with parallel workers
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_chunk, chunk): chunk for chunk in chunks_to_translate}
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                chunk = futures[future]
                print(f"  [Chunk {chunk['num']}] Error: {e}")
    
    # Compile final output
    print("\nCompiling final translated document...")
    
    final_content = []
    final_content.append("# Spey MK202 Engine Design and Test Data Compilation - Volume 2\n")
    final_content.append("## Translated from Chinese to English using Mistral Large 3 675B\n")
    final_content.append(f"## Translation includes analysis of {total_images} technical figures\n\n")
    final_content.append("---\n\n")
    
    # Sort chunks by number and compile
    for chunk in sorted(chunks, key=lambda x: x["num"]):
        chunk_num = chunk["num"]
        if str(chunk_num) in translations:
            if chunk_num > 0:
                final_content.append(f"\n---\n\n## Section {chunk_num} (Pages {(chunk_num-1)*5 + 1}-{chunk_num*5})\n\n")
            final_content.append(translations[str(chunk_num)])
            final_content.append("\n\n")
    
    # Save final output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("".join(final_content))
    
    print(f"\n{'='*60}")
    print("TRANSLATION COMPLETE!")
    print(f"{'='*60}")
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Translated: {len(completed_chunks)}")
    print(f"  Images analyzed: {total_images}")
    print(f"  Output: {output_file}")
    
    return output_file


if __name__ == "__main__":
    if not NVIDIA_API_KEY:
        print("Error: NVIDIA_API_KEY environment variable not set")
        sys.exit(1)
    
    # Default paths
    input_file = "/Users/avinash/Desktop/project/minerU/engine_output/combined_extracted.md"
    output_dir = "/Users/avinash/Desktop/project/minerU/engine_output"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    translate_document(input_file, output_dir)
