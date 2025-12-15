# Babel Translation Pipeline Scripts

This folder contains the core translation pipeline scripts for processing scanned PDF documents.

## Pipeline Overview

```
┌───────────────────┐    ┌─────────────────────┐    ┌──────────────────────────┐
│  batch_mineru     │───▶│ translate_structured │───▶│ create_pdf_from_structured │
│  (OCR + Layout)   │    │  (LLM Translation)   │    │   (PDF Generation)       │
└───────────────────┘    └─────────────────────┘    └──────────────────────────┘
```

## Scripts

### 1. `batch_mineru_fixed.py`
**Purpose:** Split large PDFs into chunks and extract content using MinerU OCR.

**Features:**
- Splits large PDFs into manageable chunks (20 pages each)
- Processes via MinerU HuggingFace Space
- Extracts text, tables, formulas, and images
- Adds page markers for tracking original page numbers
- Combines results into unified markdown

**Usage:**
```bash
python batch_mineru_fixed.py /path/to/input.pdf /path/to/output_dir
```

---

### 2. `translate_structured.py`
**Purpose:** Translate extracted content to English using Mistral Large 3 675B.

**Features:**
- Uses NVIDIA API with Mistral Large 3 675B model
- Returns structured JSON output (not plain markdown)
- Preserves document structure: headings, paragraphs, tables, equations, images
- Tracks original page ranges for each chunk
- Resume capability with progress file
- Parallel processing with configurable workers

**Output Format:**
```json
{
  "elements": [
    {"type": "heading", "level": 1, "content": "Chapter Title"},
    {"type": "paragraph", "content": "Translated text..."},
    {"type": "table", "caption": "...", "headers": [...], "rows": [...]},
    {"type": "equation", "latex": "E = mc^2"},
    {"type": "image", "path": "...", "caption": "...", "description": "..."}
  ]
}
```

**Usage:**
```bash
export NVIDIA_API_KEY="your-api-key"
python translate_structured.py
```

---

### 3. `create_pdf_from_structured.py`
**Purpose:** Generate professional PDF from structured JSON translation output.

**Features:**
- Embeds images from extracted chunks
- Renders tables with proper formatting
- Converts LaTeX equations to Unicode
- Supports Greek letters, subscripts, superscripts
- Uses Arial Unicode font for full character support
- Adds page numbers and section markers
- Handles embedded JSON content gracefully

**Usage:**
```bash
python create_pdf_from_structured.py [input.json] [output.pdf]
```

---

## Dependencies

```bash
pip install pymupdf gradio_client requests reportlab certifi
```

## Configuration

Each script has configuration variables at the top of the file:

| Script | Key Config |
|--------|-----------|
| `batch_mineru_fixed.py` | `PAGES_PER_CHUNK`, output directory |
| `translate_structured.py` | `NVIDIA_API_KEY`, `MODEL`, `MAX_WORKERS` |
| `create_pdf_from_structured.py` | `INPUT_JSON`, `OUTPUT_PDF`, `IMAGE_BASE_DIR` |

## Workflow Example

```bash
# Step 1: Extract content from scanned PDF
python batch_mineru_fixed.py document.pdf ./output/

# Step 2: Translate to English
export NVIDIA_API_KEY="nvapi-..."
cd output
python translate_structured.py

# Step 3: Generate translated PDF
python create_pdf_from_structured.py \
  engine_output/translated_structured.json \
  engine_output/Translated_Document.pdf
```

## Output Files

After running the full pipeline:

```
output/
├── chunks/                  # Split PDF chunks
├── extracted_chunk_*/       # MinerU extraction results
│   ├── result.md           # Extracted markdown
│   └── images/             # Extracted images
├── combined_extracted.md    # Combined source content
└── engine_output/
    ├── structured_translation_progress.json  # Progress/resume file
    ├── translated_structured.json            # Final translation
    └── Translated_Document.pdf               # Output PDF
```

## Error Handling

- **JSON Parse Errors:** The translate script auto-fixes common JSON issues (trailing commas, missing commas)
- **Resume Support:** Translation can resume from last successful chunk if interrupted
- **Font Fallback:** PDF generation falls back to Helvetica if Arial Unicode unavailable
- **Image Not Found:** Gracefully shows placeholder if extracted images missing
