# Spey MK202 Engine Translation Project

## Project Overview

This project translates a **441-page scanned Chinese technical PDF** (Spey MK202 Engine Design and Test Data, Volume 2) into English using AI-powered OCR and translation.

### Document Details
- **Original Document**: 斯贝MK202发动机设计、试验资料选编 第2分册 (Spey MK202 Engine Design and Test Data Compilation, Volume 2)
- **Pages**: 441 pages
- **Size**: 71 MB
- **Type**: Scanned PDF (no text layer)
- **Language**: Chinese → English

---

## Pipeline Architecture

The translation pipeline consists of 3 main stages:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Stage 1: OCR   │───▶│ Stage 2: Trans  │───▶│ Stage 3: PDF    │
│  (MinerU)       │    │ (Mistral 675B)  │    │ (ReportLab)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Stage 1: OCR Extraction (`batch_mineru.py`)
- **Tool**: MinerU via HuggingFace Space (opendatalab/MinerU)
- **Method**: Batch processing (5 pages per chunk)
- **Output**: 89 chunks, 581,738 characters extracted
- **Features**: 
  - Handles scanned PDFs with no text layer
  - Extracts images and text layout
  - Preserves mathematical formulas

### Stage 2: Translation (`translate_mistral.py`)
- **Model**: Mistral Large 3 675B (`mistralai/mistral-large-3-675b-instruct-2512`)
- **API**: NVIDIA NIM API
- **Features**:
  - Translates Chinese text to English
  - Analyzes technical diagrams and figures (up to 10 images per batch)
  - Preserves technical terminology
  - Maintains mathematical expressions in LaTeX format

### Stage 3: PDF Generation (`create_clean_pdf.py`)
- **Library**: ReportLab
- **Features**:
  - Converts LaTeX math to Unicode (subscripts, superscripts, Greek letters)
  - Professional document formatting
  - Clean text-only output

---

## Output Files

Located in `/Outputs/`:

| File | Size | Description |
|------|------|-------------|
| `extracted_chinese.md` | 900 KB | OCR-extracted Chinese text |
| `translated_english.md` | 1.06 MB | Complete English translation |
| `Spey_MK202_Engine_Clean.pdf` | 985 KB | Final formatted PDF |

---

## Technical Implementation

### Math Rendering
LaTeX expressions are converted to Unicode for proper display:

| LaTeX | Unicode |
|-------|---------|
| `\(W_{c}\)` | Wc |
| `\(T_{01}\)` | T₀₁ |
| `\(\pi_{c}\)` | πc |
| `\(N D^3\)` | N D³ |
| `\(V \propto N D^3\)` | V ∝ N D³ |

### Supported Symbols
- **Subscripts**: ₀₁₂₃₄₅₆₇₈₉ₐₑᵢₒᵣᵤᵥₓₙₘ
- **Superscripts**: ⁰¹²³⁴⁵⁶⁷⁸⁹ⁿⁱ⁺⁻
- **Greek Letters**: α β γ δ ε η θ λ μ ν π ρ σ τ φ χ ψ ω
- **Math Symbols**: × · ± ≤ ≥ ≠ ≈ ∝ ∞ ∂ √ →

---

## How to Run

### Prerequisites
```bash
pip install gradio_client reportlab openai
```

### Environment Variables
```bash
export HF_TOKEN="your_huggingface_token"
export NVIDIA_API_KEY="your_nvidia_api_key"
```

### Step 1: OCR Extraction
```bash
python scripts/batch_mineru.py "input.pdf" ./output 5
```

### Step 2: Translation
```bash
python scripts/translate_mistral.py
```
(Edit the script to set INPUT_DIR and OUTPUT_FILE paths)

### Step 3: PDF Generation
```bash
python scripts/create_clean_pdf.py
```
(Edit the script to set INPUT_MD and OUTPUT_PDF paths)

---

## Statistics

| Metric | Value |
|--------|-------|
| Total Pages | 441 |
| OCR Chunks | 89 |
| Characters Extracted | 581,738 |
| Translation Chunks | 90 |
| Images Analyzed | 779 |
| Final PDF Size | 985 KB |
| Processing Time | ~3 hours |

---

## Models Used

| Purpose | Model | Provider |
|---------|-------|----------|
| OCR | MinerU | HuggingFace (opendatalab) |
| Translation + Image Analysis | Mistral Large 3 675B | NVIDIA NIM |

---

## Project Structure

```
babel-extreme-project/
├── scripts/
│   ├── batch_mineru.py      # OCR extraction
│   ├── translate_mistral.py # Translation with image analysis
│   └── create_clean_pdf.py  # PDF generation
├── Outputs/
│   ├── extracted_chinese.md    # OCR output
│   ├── translated_english.md   # English translation
│   └── Spey_MK202_Engine_Clean.pdf  # Final PDF
├── test/
│   └── input/
│       └── 斯贝MK202发动机...pdf  # Original document
└── README_TRANSLATION.md
```

---

## Author

**Avinash**  
Date: December 14, 2025

---

## License

This project is for educational and research purposes.
