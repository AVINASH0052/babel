# Babel-LunarTech

> **The 9/10 Document Translation System**

<div align="center">
  <h2>🌍 Translate Books Brilliantly</h2>
</div>

---

## Overview

**Babel-LunarTech** is a production-grade document translation system developed by LunarTech in collaboration with Google Cloud, OpenAI, and BabelDOC. It translates entire books and technical documents while preserving formatting, structure, and layout with near-perfect fidelity.

### What It Does (9/10)

| ✅ Handles | ❌ Cannot Handle |
|-----------|-----------------|
| Born-digital PDFs | **Scanned documents** |
| Tables with structure | Image-only PDFs |
| Figures in correct positions | PDFs without text layer |
| Multi-column layouts | Handwritten content |
| Mathematical formulas | Text embedded in images |
| Headers/footers | Diagram labels |
| 22 languages | — |

---

## Core Capabilities

### ✅ Preserves Formatting

Unlike basic translation tools that output flat text, Babel-LunarTech maintains:

- **Page layout** — Margins, columns, spacing
- **Typography** — Fonts, sizes, styles
- **Tables** — Row/column structure, merged cells, borders
- **Figures** — Images appear in their original positions
- **Headers/Footers** — Page numbers, running titles

### ✅ Context-Aware Translation

Babel doesn't translate sentence-by-sentence. It:

1. **Extracts terminology** first for document-wide consistency
2. **Groups text into logical blocks** (paragraphs, captions)
3. **Sends context to GPT-4o** — knows if "bank" means river or money
4. **Maintains glossary** — "stator" translated identically on page 1 and page 50

### ✅ Supported Formats

| Format | Support |
|--------|---------|
| PDF (born-digital) | ✅ Full |
| DOCX | ✅ Full |
| PDF (scanned) | ❌ Not supported |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BABEL-LUNARTECH PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│   │   UPLOAD     │────▶│   BABELDOC   │────▶│   DOWNLOAD   │                │
│   │   (Web UI)   │     │   ENGINE     │     │   (PDF)      │                │
│   └──────────────┘     └──────────────┘     └──────────────┘                │
│                               │                                              │
│                               ▼                                              │
│              ┌────────────────────────────────┐                              │
│              │        BABELDOC CORE           │                              │
│              │                                │                              │
│              │  1. Layout Analysis            │                              │
│              │     └─ Detect structure        │                              │
│              │                                │                              │
│              │  2. Term Extraction            │                              │
│              │     └─ Build glossary          │                              │
│              │                                │                              │
│              │  3. Contextual Translation     │                              │
│              │     └─ GPT-4o with context     │                              │
│              │                                │                              │
│              │  4. Reconstruction             │                              │
│              │     └─ Inject into layout      │                              │
│              └────────────────────────────────┘                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | HTML/CSS/JS Dashboard |
| **Backend** | FastAPI (Python) |
| **Translation** | OpenAI GPT-4o |
| **Core Engine** | BabelDOC |
| **Infrastructure** | Google Cloud |

---

## Supported Languages

22 languages with high-quality translation:

| | | |
|:---:|:---:|:---:|
| English | Chinese (中文) | Hindi (हिन्दी) |
| Arabic (العربية) | Russian (Русский) | Armenian (Հայdelays) |
| Japanese (日本語) | German (Deutsch) | Dutch (Nederlands) |
| Italian (Italiano) | French (Français) | Spanish (Español) |
| Portuguese (Português) | Korean (한국어) | Turkish (Türkçe) |
| Polish (Polski) | Vietnamese (Tiếng Việt) | Ukrainian (Українська) |
| Romanian (Română) | Thai (ไทย) | Javanese (Jawa) |
| Punjabi (ਪੰਜਾਬੀ) | | |

---

## The Missing 10%: Scanned Documents

Babel-LunarTech excels at born-digital PDFs but **cannot process scanned documents**:

### The Gap

| Input Type | Babel-LunarTech | Needed |
|------------|-----------------|--------|
| PDF with text layer | ✅ Works | — |
| PDF = images only | ❌ Fails | OCR + Layout |
| Text in diagrams | ❌ Ignored | VLM extraction |
| Handwritten notes | ❌ Fails | Specialized OCR |

### Why It Fails on Scans

1. **No text layer** — BabelDOC expects extractable text
2. **No OCR** — Cannot read text from images
3. **No VLM** — Cannot understand diagram labels
4. **Layout detection** assumes structured PDF, not rasterized pages

---

## Enter BabelExtreme

**BabelExtreme** extends Babel-LunarTech to handle the missing 10%:

| Feature | Babel-LunarTech | BabelExtreme |
|---------|-----------------|--------------|
| Born-digital PDFs | ✅ | ✅ |
| Scanned PDFs | ❌ | ✅ |
| OCR | ❌ | MinerU + PaddleOCR |
| Diagram labels | ❌ | Qwen2.5-VL |
| Formula recovery | Basic | LaTeX extraction |
| Offline mode | ❌ | ✅ |

**BabelExtreme = Babel-LunarTech + Scanned Document Support**

---

## Usage

```bash
# Navigate to backend
cd Babel-LunarTech/handex-backend-antigravity

# Install dependencies
pip install fastapi uvicorn python-multipart openai

# Set API key
$env:OPENAI_API_KEY="your-key"

# Start server
python server.py

# Access dashboard
# http://localhost:8000/dashboard/index.html
```

---

## Summary

| Aspect | Rating |
|--------|--------|
| **Born-digital translation** | ⭐⭐⭐⭐⭐ |
| **Layout preservation** | ⭐⭐⭐⭐⭐ |
| **Context awareness** | ⭐⭐⭐⭐⭐ |
| **Table handling** | ⭐⭐⭐⭐⭐ |
| **Scanned documents** | ❌ |
| **Diagram labels** | ❌ |

> **Overall: 9/10** — Exceptional for born-digital documents. Requires BabelExtreme for scanned content.

---

<div align="center">
  <sub>Built with ❤️ by LunarTech</sub>
</div>
