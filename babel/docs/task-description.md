# BabelExtreme: Scanned Document Translation Pipeline

## Overview

**Mission:** Build a robust, open-source pipeline for translating **image-only scanned PDFs** (no extractable text layer) into fully translated, layout-preserved, publication-grade documents.

**Target Use Case:** Complex engineering books with diagrams, formulas, tables, and precise technical layouts where existing tools (BabelDOC, pdf2zh) fail to produce consistent, high-quality results.

---

> [!IMPORTANT]
> **Core Principle: Preserve Non-Text Elements Intact**
> 
> This pipeline treats **visual fidelity as sacrosanct**. The translated document must be visually indistinguishable from the original except for the language of the text. All non-text elements are transferred unchanged.

---

## Core Preservation Philosophy

Translation of scanned documents is fundamentally different from translation of editable text. In a scanned engineering book, the **visual layout IS the content**. A formula's position relative to its explanation, a diagram's relationship to its caption, a table's grid structure—these are not cosmetic details. They carry meaning.

### What Gets Translated vs. What Gets Preserved

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DOCUMENT ELEMENTS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   🔄 TRANSLATED                          🔒 PRESERVED INTACT                 │
│   ─────────────                          ──────────────────                  │
│   • Body text (paragraphs)               • Photographs                       │
│   • Headings & titles                    • Technical drawings (lines/shapes) │
│   • Captions & labels                    • Graph axes & gridlines            │
│   • Table cell content                   • Table borders & structure         │
│   • Figure annotations                   • Chart visual elements (bars/pies) │
│   • Footnotes                            • Schematics & circuit diagrams     │
│   • Index entries                        • Maps & floor plans                │
│   • Mathematical variable names*         • Equation layout & symbols         │
│                                                                              │
│   * Only descriptive names like "velocity" are translated;                   │
│     symbolic variables (x, y, α, β) remain unchanged                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Element-by-Element Preservation Rules

#### 📷 Images & Photographs

| Aspect | Handling |
|--------|----------|
| **Resolution** | Preserved at original DPI (no downsampling) |
| **Color Space** | Maintained (RGB, CMYK, Grayscale) |
| **Position** | Exact (x, y) coordinates from original |
| **Dimensions** | Width and height unchanged |
| **Embedded Text** | Identified → translated → overlaid (original pixels untouched beneath) |
| **Alt Text / Captions** | Translated separately, placed at original caption position |

**Philosophy**: A photograph is irreplaceable source material. Even if it contains text (e.g., a photo of a sign), we overlay translated text rather than edit pixels.

#### 📊 Tables

| Aspect | Handling |
|--------|----------|
| **Grid Structure** | Row count, column count, cell boundaries preserved exactly |
| **Merged Cells** | Detected and replicated in output |
| **Borders & Lines** | Line styles, weights, colors maintained |
| **Cell Backgrounds** | Shading and colors preserved |
| **Cell Padding** | Spacing between text and borders maintained |
| **Cell Content** | Text extracted → translated → re-inserted with matching alignment |
| **Numeric Data** | Numbers preserved exactly (no localization of decimals unless requested) |

**Philosophy**: A table is a **data structure**, not just formatted text. Corrupting the grid structure would destroy the semantic relationship between headers and values.

#### 📐 Technical Diagrams & Schematics

| Aspect | Handling |
|--------|----------|
| **Vector Elements** | Lines, shapes, arrows preserved as-is |
| **Connection Points** | Junction markers, nodes unchanged |
| **Shading & Fills** | Gradients, hatching, patterns maintained |
| **Annotations** | Text labels identified by VLM, translated, overlaid |
| **Legend Boxes** | Border and background preserved, text translated |
| **Dimension Lines** | Arrow styles preserved, measurement text translated |
| **Symbols** | Electrical, chemical, mechanical symbols untouched |

**Philosophy**: A schematic is a **precise technical specification**. Moving a line by even one pixel could change the meaning of a circuit or mechanical assembly.

#### 📈 Charts & Graphs

| Aspect | Handling |
|--------|----------|
| **Data Visualization** | Bars, lines, pie slices, scatter points unchanged |
| **Axes** | Gridlines, tick marks preserved; axis labels translated |
| **Legend** | Color swatches preserved; legend text translated |
| **Title** | Translated |
| **Data Labels** | Value annotations on chart elements translated |
| **Scale** | Numeric scale values preserved exactly |

**Philosophy**: Charts encode quantitative data visually. The bar heights, line slopes, and pie angles ARE the data—touching them would falsify the document.

#### ➗ Mathematical Formulas & Equations

| Aspect | Handling |
|--------|----------|
| **Symbolic Notation** | Variables (x, y, z, α, β, Σ) never translated |
| **Operators** | +, −, ×, ÷, =, ∫, ∂ preserved |
| **Structure** | Fractions, superscripts, subscripts, matrices unchanged |
| **Descriptive Terms** | Words like "where" or "such that" translated |
| **Equation Numbers** | Preserved (e.g., "(Eq. 3.2)") |
| **Rendering** | Extracted as LaTeX, re-rendered at original position |

**Philosophy**: Mathematics is a universal language. Translating "∫" to a word would be incorrect. We only translate the surrounding prose.

### The "No Pixel Left Behind" Guarantee

Every pixel of non-text content in the source document must appear in the output:

```
SOURCE PDF                              OUTPUT PDF
┌─────────────────────┐                 ┌─────────────────────┐
│  [Japanese Text]    │                 │  [English Text]     │  ← Translated
│                     │                 │                     │
│  ┌───────────────┐  │                 │  ┌───────────────┐  │
│  │  ▓▓▓ Photo ▓▓▓│  │   ────────▶     │  │  ▓▓▓ Photo ▓▓▓│  │  ← Identical
│  └───────────────┘  │                 │  └───────────────┘  │
│                     │                 │                     │
│  ┌─┬─┬─┐            │                 │  ┌─┬─┬─┐            │
│  │A│B│C│ Table      │   ────────▶     │  │A│B│C│ Table      │  ← Structure preserved
│  ├─┼─┼─┤            │                 │  ├─┼─┼─┤            │     Content translated
│  │1│2│3│            │                 │  │1│2│3│            │
│  └─┴─┴─┘            │                 │  └─┴─┴─┘            │
│                     │                 │                     │
│     ┌──[図3]        │                 │     ┌──[Fig3]       │  ← Label translated
│     │  ○──●         │   ────────▶     │     │  ○──●         │     Diagram identical
│     │  │  │         │                 │     │  │  │         │
│     └──┴──┘         │                 │     └──┴──┘         │
└─────────────────────┘                 └─────────────────────┘
```

### Why This Matters for Engineering Documents

Engineering books contain **mission-critical information**. A translated maintenance manual for an aircraft, a medical device specification, or a power plant schematic cannot have:

- **Missing diagrams**: "Figure 12 shows the emergency shutoff valve" → but Figure 12 is missing
- **Corrupted tables**: A dosage table where columns have shifted
- **Mangled schematics**: A wiring diagram where label positions don't match their connection points
- **Lost formulas**: Stress calculations that became garbled during OCR

> [!WARNING]
> **Failure Mode to Avoid**: Many translation tools "flatten" documents—re-rendering everything as new text/images. This approach:
> - Loses image quality (recompression artifacts)
> - Breaks table alignment
> - Disconnects labels from their diagram positions
> - Can introduce OCR errors into numeric data
>
> **Our approach preserves originals and only overlays translations.**

---

## The Problem

### Why Standard Tools Fail

| Tool | Limitation |
|------|------------|
| **BabelDOC / pdf2zh** | Expects standard document structure (paragraphs, headers). Struggles with text embedded in artwork, gradients, or complex layouts. Breaks the link between diagrams and their captions. **Often corrupts or loses images entirely.** |
| **Standard OCR (Tesseract)** | Reads text line-by-line without understanding 2D spatial relationships. Cannot preserve structure or handle multi-column layouts. |
| **Google Translate / DeepL APIs** | No layout awareness. Returns translated text without positional context. Mangles mathematical notation (e.g., `x²` → `x2`). |

### The Input Challenge

Our input documents are:
- **Scanned PDFs** containing only flat raster images (no text layer)
- **Complex engineering content**: formulas, tables, technical diagrams with labels
- **Precise layouts** that must be preserved exactly
- **Mixed media**: text, equations, charts, schematics, photographs

> [!CAUTION]
> **Non-Negotiable Requirements:**
> - All **images** (photos, diagrams, schematics) must appear in the output at their original positions and quality
> - All **tables** must retain their structure (rows, columns, merged cells) with only cell text translated
> - All **charts/graphs** must be preserved with only labels/legends translated
> - **No content loss**: Every visual element from the source must exist in the output

---

## The "Nuclear" Pipeline Architecture

Based on deep analysis of state-of-the-art document AI, we require a **multi-stage pipeline** that treats structure extraction and translation as separate, specialized concerns.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PDF Ingest    │────▶│ Structure       │────▶│  Translation    │────▶│ Reconstruction  │
│   & Pre-proc    │     │ Extraction      │     │  Engine         │     │ & Export        │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │                       │
   OpenCV/Pillow          MinerU/Surya            LLM (Llama 3/          Typst/LaTeX
   Deskewing              LayoutLM                DeepSeek/GPT)          ReportLab
   Denoising              Qwen2.5-VL              NLLB-200               Font Matching
```

---

## Pipeline Components (Detailed)

### Stage 1: Ingestion & Pre-processing

**Purpose:** Prepare raw scanned images for optimal OCR and layout analysis.

| Component | Technology | Function |
|-----------|------------|----------|
| PDF → Image | `pdf2image` / `PyMuPDF` | Extract each page as high-resolution PNG |
| Deskewing | `OpenCV` | Correct rotation/skew from scanning |
| Denoising | `OpenCV` / `Pillow` | Remove scan artifacts, improve contrast |
| Enhancement | `Real-ESRGAN` (optional) | Upscale low-resolution scans |

**Output:** Clean, aligned, high-resolution page images.

---

### Stage 2: Structure Extraction (The "Brain")

**Purpose:** Understand the document's semantic structure—not just text, but what each element *is* and where it belongs.

#### 2A: Document Layout Analysis

| Component | Technology | Function |
|-----------|------------|----------|
| **Primary OCR + Layout** | **MinerU (Magic-PDF)** | Extracts text, formulas (as LaTeX), tables, and images with coordinates |
| Alternative OCR | `Surya` (VikParuchuri) | Superior line-level detection for poor-quality scans |
| Fallback OCR | `PaddleOCR PP-Structure` | Robust multi-language support |

**MinerU Advantages for Engineering Docs:**
- Converts mathematical formulas to **LaTeX** (not mangled OCR text)
- Reconstructs **table logic** (row/column relationships) even with invisible gridlines
- Outputs **structured Markdown** with clear separation of text, formulas, and image references

#### 2B: Diagram & Chart Analysis (Vision-Language Model)

**The Problem:** Standard OCR cannot read text labels inside technical schematics, flowcharts, or annotated diagrams.

> [!NOTE]
> **Images Are Sacred**: The diagram *image itself* is never modified or regenerated. We only identify text labels, translate them, and overlay the translations. The underlying graphic remains pixel-perfect from the original.

| Component | Technology | Function |
|-----------|------------|----------|
| **Vision-Language Model** | **Qwen2.5-VL** / InternVL2 | Identifies and extracts text labels from complex diagrams |
| Diagram Parsing | Custom prompting | Returns JSON: `{original_text, translated_text, x, y, width, height}` |

**Workflow:**
1. MinerU identifies regions classified as "Image" or "Figure"
2. These regions are cropped and sent to Qwen2.5-VL
3. VLM prompt: *"Identify all text labels in this technical drawing. Return as JSON with original text, coordinates, and bounding box dimensions."*
4. **Original image is preserved intact**
5. Extracted labels are translated and re-rendered as overlay text on the preserved image

---

### Stage 3: Translation Engine (The "Linguist")

**Purpose:** Context-aware, terminology-consistent translation that understands technical content.

| Component | Technology | Function |
|-----------|------------|----------|
| **Primary LLM** | **DeepSeek-V3** / Llama 3.3 70B | Context-aware translation with technical domain knowledge |
| Fallback | `NLLB-200` (Meta) | Open-source multilingual model (200 languages) |
| Glossary Enforcement | Custom RAG | Ensures consistent terminology (e.g., "stator" translated identically on page 1 and page 50) |

**Context-Aware Translation Strategy:**

```python
# Instead of translating isolated sentences, send structured metadata:
prompt = """
Translate this text block from a mechanical engineering textbook.
Source Language: Japanese
Target Language: English

Context:
- This is a CAPTION for Figure 3.2
- Previous section discussed "gear ratios"
- Technical domain: Automotive transmission systems

Text to translate:
{text_block}

Maintain formal technical tone. Preserve any equation references (e.g., "Eq. 3.1").
"""
```

**Session Memory:** Maintain a document-wide glossary to ensure term consistency across all pages.

---

### Stage 4: Reconstruction & Export (The "Typesetter")

**Purpose:** Re-render the translated content into a publication-quality PDF that mirrors the original layout.

#### 4A: Text Reconstruction

| Component | Technology | Function |
|-----------|------------|----------|
| **Typesetting Engine** | **Typst** (modern) / LaTeX | Compile translated Markdown into formatted PDF |
| Font Matching | `fonttools` / heuristics | Analyze original font (serif/sans, weight) and select closest match |
| Adaptive Sizing | Custom algorithm | Adjust font size/kerning when translated text is longer/shorter |

**Why Typst over Inpainting:**
- **Inpainting** (erasing old text, painting new) introduces visual artifacts
- **Re-typesetting** creates crisp, vector-perfect text that looks native
- Mathematical formulas render perfectly from LaTeX source

#### 4B: Diagram & Image Handling

> [!IMPORTANT]
> **Preservation-First Approach**: The original image/diagram is the foundation. We modify *only* the text label regions—everything else (lines, colors, shading, graphics) remains untouched.

| Method | Technology | Use Case |
|--------|------------|----------|
| **Pass-Through** | Direct copy | Images with no embedded text (photos, pure graphics) |
| **Label Replacement** | `Pillow` + font rendering | Simple labels on clean backgrounds |
| **Inpainting + Overlay** | `LaMa` / Stable Diffusion | Labels on complex/textured backgrounds |

**Workflow:**
1. **Images without text** → Direct transfer to output (no processing)
2. **Images with text labels**:
   - Use LaMa to "erase" *only* the text label regions
   - Render translated text at exact coordinates from VLM output
   - Composite translated labels onto the preserved original image
3. Insert processed images into Typst document at original positions

#### 4C: Table Preservation

> [!NOTE]
> Tables are **not re-rendered from scratch**. The original table structure (borders, cell dimensions, merged cells, background colors) is preserved. Only the text content within each cell is replaced with its translation.

| Aspect | Handling |
|--------|----------|
| **Grid Structure** | Preserved from original (row/column layout intact) |
| **Cell Styling** | Borders, colors, alignment maintained |
| **Cell Content** | Text extracted → translated → re-inserted at same position |
| **Merged Cells** | Detected and respected during reconstruction |

---

## Data Flow Summary

```
INPUT: Scanned PDF (image-only)
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: INGESTION                                             │
│  • PDF → High-res PNG pages                                     │
│  • Deskew, denoise, enhance                                     │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2: STRUCTURE EXTRACTION                                  │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │ MinerU          │    │ Qwen2.5-VL      │                     │
│  │ • Text blocks   │    │ • Diagram labels│                     │
│  │ • LaTeX formulas│    │ • Chart text    │                     │
│  │ • Table grids   │    │ • Schematic     │                     │
│  │ • Image regions │    │   annotations   │                     │
│  └────────┬────────┘    └────────┬────────┘                     │
│           │                      │                               │
│           └──────────┬───────────┘                               │
│                      ▼                                           │
│           Structured Markdown + Diagram JSON                     │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 3: TRANSLATION                                           │
│  • LLM with context (document type, section, previous terms)    │
│  • Glossary consistency enforcement                             │
│  • Technical domain awareness                                   │
│                                                                  │
│  OUTPUT: Translated Markdown + Translated Diagram Labels        │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 4: RECONSTRUCTION                                        │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │ Typst/LaTeX     │    │ LaMa + Pillow   │                     │
│  │ • Text pages    │    │ • Diagram labels│                     │
│  │ • Formulas      │    │   replacement   │                     │
│  │ • Tables        │    │                 │                     │
│  └────────┬────────┘    └────────┬────────┘                     │
│           │                      │                               │
│           └──────────┬───────────┘                               │
│                      ▼                                           │
│              Final PDF Assembly                                  │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
OUTPUT: Translated PDF (selectable text, preserved layout)
```

---

## Technology Stack Summary

| Layer | Component | Primary Tech | Fallback |
|-------|-----------|--------------|----------|
| **Ingestion** | PDF Processing | `PyMuPDF` | `pdf2image` |
| **Ingestion** | Image Enhancement | `OpenCV` | `Pillow` |
| **Vision** | Layout Analysis | **MinerU** | `Surya`, `PaddleOCR` |
| **Vision** | Diagram Understanding | **Qwen2.5-VL** | `InternVL2`, `GPT-4V` |
| **Translation** | LLM | **DeepSeek-V3** | `Llama 3.3`, `NLLB-200` |
| **Cleaning** | Text Inpainting | **LaMa** | `Stable Diffusion Inpaint` |
| **Reconstruction** | Typesetting | **Typst** | `LaTeX`, `ReportLab` |
| **Output** | PDF Assembly | `PyMuPDF` | `WeasyPrint` |

---

## Quality Requirements

### Must Have

#### Content Preservation (Non-Negotiable)
- [ ] **Image Integrity**: All images appear in output at original positions, dimensions, and quality
- [ ] **Table Structure**: Row/column grid preserved exactly—only cell text content changes
- [ ] **Chart/Graph Fidelity**: Visual elements (bars, lines, axes) untouched—only labels translated
- [ ] **No Content Loss**: Every visual element from source exists in output

#### Translation Quality
- [ ] **Formula Integrity**: All mathematical expressions preserved as LaTeX, rendered correctly
- [ ] **Table Logic**: Row/column relationships maintained, not just visual alignment
- [ ] **Diagram Labels**: All text inside schematics translated and re-rendered at correct positions
- [ ] **Terminology Consistency**: Same term translated identically throughout document
- [ ] **Selectable Text**: Output PDF has real text layer, not just images
- [ ] **Layout Fidelity**: Margins, columns, spacing match original within 5%

### Nice to Have
- [ ] **Batch Processing**: Handle entire books (100+ pages) in single run
- [ ] **Progress Tracking**: Real-time status for long-running jobs
- [ ] **Quality Confidence Scores**: Flag low-confidence translations for human review
- [ ] **Incremental Updates**: Allow re-translation of specific pages without full reprocessing

---

## Compute Requirements

| Component | VRAM Requirement | Notes |
|-----------|------------------|-------|
| MinerU | 8GB+ | CPU-capable but slow |
| Qwen2.5-VL (7B) | 16GB | Quantized versions available |
| DeepSeek-V3 | API / 40GB+ | Recommend API for consistency |
| LaMa | 4GB | Lightweight inpainting |
| **Total (Local)** | **24GB+ VRAM** | Or use cloud APIs |

**Recommended Setup:**
- **Development**: NVIDIA RTX 4090 (24GB) or cloud GPU (A100)
- **Production**: API-based (DeepSeek, OpenAI) + local lightweight models

---

## Success Criteria

A translation is considered successful when:

1. **Human Review**: A native speaker of the target language can read the translated document without confusion
2. **Technical Accuracy**: All formulas, units, and technical terms are correctly translated
3. **Visual Quality**: The translated PDF is indistinguishable from a professionally typeset document
4. **Consistency**: Terminology is consistent across the entire document
5. **Completeness**: No text (including diagram labels) is left untranslated

---

## Project Deliverables

1. **`babelextreme/` Python Package**
   - Modular pipeline with swappable components
   - CLI for batch processing
   - Configuration via YAML/TOML

2. **Documentation**
   - Installation guide
   - API reference
   - Configuration options
   - Troubleshooting guide

3. **Evaluation Suite**
   - Test PDFs (engineering, scientific, mixed-media)
   - Metrics: BLEU score, layout similarity, formula accuracy
   - Benchmark against BabelDOC/Linnk.ai

---

## References

- [MinerU (Magic-PDF)](https://github.com/opendatalab/MinerU) - Structure extraction
- [Surya](https://github.com/VikParuchuri/surya) - Advanced OCR
- [Qwen2.5-VL](https://github.com/QwenLM/Qwen2.5-VL) - Vision-language model
- [LaMa](https://github.com/saic-mdal/lama) - Image inpainting
- [Typst](https://github.com/typst/typst) - Modern typesetting
- [DeepSeek](https://www.deepseek.com/) - Translation LLM
