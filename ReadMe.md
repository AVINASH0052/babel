# BabelExtreme

> **Open-source scanned document translation pipeline**

Translate image-only PDFs while preserving layout, tables, diagrams, and formulas. Built for engineering books and technical documents where existing tools fail.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## The Problem

Scanned PDFs have no selectable text—just images. Standard tools either:
- ❌ Lose images and diagrams
- ❌ Break table structure  
- ❌ Mangle mathematical formulas
- ❌ Disconnect labels from diagrams

**BabelExtreme preserves everything.** Only the text changes; visuals stay pixel-perfect.

---

## How It Works

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  INGESTION   │───▶│  EXTRACTION  │───▶│ TRANSLATION  │───▶│RECONSTRUCTION│
│  PDF→Images  │    │  OCR+Layout  │    │  LLM + VLM   │    │  Typst→PDF   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

1. **Ingestion** — Extract pages as high-res images, deskew, enhance
2. **Extraction** — MinerU detects text, tables, formulas, diagrams
3. **Translation** — LLM translates text; VLM handles diagram labels
4. **Reconstruction** — Overlay translations on preserved originals

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Preservation-First** | Images, diagrams, tables transfer unchanged |
| **Formula Support** | LaTeX extraction → perfect math rendering |
| **Diagram Labels** | VLM extracts & translates text in schematics |
| **200+ Languages** | Via NLLB-200 / DeepSeek / Llama |
| **Offline Capable** | Full local mode with open-source models |

---

## Tech Stack

| Component | Primary | Fallback |
|-----------|---------|----------|
| **OCR + Layout** | MinerU | PaddleOCR, Surya |
| **Vision-Language** | Qwen2.5-VL | InternVL2 |
| **Translation** | DeepSeek-V3 | Llama 3.3 70B |
| **Reconstruction** | Typst | LaTeX |
| **Inpainting** | LaMa | — |

---

## Quick Start

```bash
# Test MinerU extraction
pip install magic-pdf
magic-pdf -p input.pdf -o output/

# Check output.md for:
# ✓ Formulas as LaTeX
# ✓ Tables with structure
# ✓ Images separated
```

---

## Documentation

| Section | Link |
|---------|------|
| **Quick Overview** | [docs/task-descript-short.md](docs/task-descript-short.md) |
| **Full Requirements** | [docs/task-description.md](docs/task-description.md) |
| **Architecture** | [docs/README.md](docs/README.md) |
| **Tool Comparisons** | [toolbox/README.md](toolbox/README.md) |

---

## Project Structure

```
babel-extreme/
├── docs/                    # Architecture & design docs
│   ├── 00-overview.md       # Design principles
│   ├── 01-04-stage-*.md     # Pipeline stages
│   ├── task-description.md  # Full requirements
│   └── verification.md      # Scanned doc proof
└── toolbox/                 # OCR/layout tool guides
    ├── ocr-for-scans.md
    └── layout-handling.md
```

---

## Status

🚧 **Design Phase** — Architecture documented, implementation pending.

---

## License

MIT
