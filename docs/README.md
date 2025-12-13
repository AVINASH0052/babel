# BabelExtreme Documentation

> **Scanned Document Translation Pipeline**

Translates image-only PDFs while preserving layout, images, tables, and formulas.

---

## Quick Start

| Document | Description |
|----------|-------------|
| [Task Description (Short)](./task-descript-short.md) | 8-paragraph overview for apprentices |
| [Task Description (Full)](./task-description.md) | Comprehensive technical requirements |
| [Verification](./verification.md) | Proof this works for scanned documents |

---

## Architecture

| Document | Description |
|----------|-------------|
| [Overview](./00-overview.md) | Design principles & pipeline diagram |
| [Stage 1: Ingestion](./01-stage-ingestion.md) | PDF → image extraction |
| [Stage 2: Extraction](./02-stage-extraction.md) | OCR & layout analysis |
| [Stage 3: Translation](./03-stage-translation.md) | LLM/VLM translation |
| [Stage 4: Reconstruction](./04-stage-reconstruction.md) | PDF assembly |
| [Cross-Cutting](./05-cross-cutting.md) | Error handling & parallelism |
| [Deployment](./06-deployment.md) | Docker & CLI |
| [References](./07-references.md) | External tool links |

---

## Research

| Document | Description |
|----------|-------------|
| [Linnk.ai Analysis](./linnk-reconstruction.md) | How to rebuild Linnk.ai |

---

## Toolbox

See [toolbox/README.md](../toolbox/README.md) for OCR and layout tool comparisons.
