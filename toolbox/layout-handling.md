# Layout Handling in OCR Tools

> **Preserving Structure in Scanned Documents**

Layout preservation means keeping the original structure intact—text blocks, tables, images, columns, equations, and formatting—rather than dumping everything into a flat text blob. Linnk.ai does this well with AI-driven rebuilding, but open-source tools vary wildly.

> [!NOTE]
> Expect to script pipelines (e.g., Python) for integration. No one-tool wonders here.

---

## Tool Comparison Matrix

| Tool | Tables | Equations | Handwriting | Multi-Column | Overall |
|------|--------|-----------|-------------|--------------|---------|
| **PaddleOCR** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | **Best** |
| **olmOCR** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | **Best** |
| **docTR** | ⭐⭐ | ⭐ | ⭐ | ⭐⭐ | Good |
| **Tesseract** | ⭐ | ⭐ | ⭐ | ⭐ | Basic |
| **Docling** | ⭐⭐ | ⭐ | ⭐ | ⭐⭐ | Limited |

---

## Detailed Tool Analysis

### Tesseract OCR

**Layout Handling:** Basic page segmentation via `--psm` flags.

| Aspect | Details |
|--------|---------|
| **Modes** | `--psm 3` (auto), `--psm 4` (columns), etc. |
| **Output** | Text with bounding boxes (hOCR format) |
| **Tables** | ❌ Weak—text often gets jumbled |
| **Multi-column** | ❌ Struggles without tweaks |
| **Accuracy** | 70-80% for complex layouts |

**Wrappers:**
- `OCRmyPDF` - Adds searchable text layer while retaining some structure
- `pdfplumber` - Needed for table extraction

> [!WARNING]
> Okay for basic printed text, but requires ~80% effort in post-processing for complex layouts.

---

### PaddleOCR

**Layout Handling:** Top-tier with **PP-Structure** module.

| Aspect | Details |
|--------|---------|
| **Detection** | Tables (→ Excel/HTML), key-value pairs, text blocks, images |
| **Order** | Preserves reading order and formatting |
| **Warped Scans** | ✅ Handles distortion well |
| **Accuracy** | 90%+ on structured docs |
| **Output** | Structured JSON with coordinates & confidence |

**Strengths:**
- Fast on GPU
- 80+ languages
- Industrial-grade for invoices/forms
- Custom trainable for domain-specific layouts

**Weaknesses:**
- Heavier setup (PaddlePaddle dependency)
- CPU mode slower for large batches
- Less accurate on pure handwriting without fine-tuning

> [!TIP]
> **Closest to Linnk.ai's structure rebuild.** If layout is your priority, start here.

---

### docTR

**Layout Handling:** Transformer-based, two-stage detection + recognition.

| Stage | Model | Function |
|-------|-------|----------|
| Detection | DB-ResNet | Bounding boxes |
| Recognition | CRNN | Text extraction |

| Aspect | Details |
|--------|---------|
| **Excels At** | Forms, receipts, structured docs |
| **Output** | JSON/XML with reading order |
| **Benchmarks** | High on FUNSD/CORD |
| **Languages** | Strong English/French; expandable |

**Limitations:**
- Weaker on non-Latin scripts
- Not as table-focused as PaddleOCR
- Heavy handwriting struggles

> Solid for layout-aware OCR if your docs are form-like. Pairs well with translation libs.

---

### olmOCR (AllenAI)

**Layout Handling:** Vision-language model (Qwen-2-VL base) tuned for scanned PDFs.

| Aspect | Details |
|--------|---------|
| **Tables** | ✅ Outputs as Markdown |
| **Equations** | ✅ LaTeX format |
| **Handwriting** | ✅ Strong support |
| **Reading Order** | ✅ Fully preserved |
| **Output** | Markdown/XML |

**Strengths:**
- Excellent for handwriting and equations
- Lightweight for bulk CPU operations
- Handles complex academic/professional docs

**Limitations:**
- Newer tool, less battle-tested
- May need GPU for speed on large files

> [!TIP]
> **Great for preserving nuanced layouts in scans.** Ideal if your docs have math or handwritten notes.

---

### Docling (IBM)

**Layout Handling:** Markdown conversion with whitespace-driven preservation.

| Aspect | Details |
|--------|---------|
| **Preserves** | Text blocks, lists, basic structure |
| **OCR Backend** | EasyOCR (default), swappable with Tesseract |
| **Images** | ❌ Struggles |
| **Handwriting** | ❌ Poor |
| **Output** | Human-readable Markdown |

**Limitations:**
- Rigid syntax limits complex representations
- Poor for marginalia or free-form layouts
- OCR weaknesses require manual cleanup

> Decent for simple layout preservation in text-heavy docs. Overrated for full scanned fidelity.

---

## Other Notable Tools

| Tool | Specialty |
|------|-----------|
| **OCRFlux** | Layout-aware for multi-column/tables; evolving |
| **Datalab Marker** | End-to-end to JSON/Markdown, strong structured extraction |
| **pdf-document-layout-analysis** (HURIDOCS) | Segments PDFs into texts/titles/pictures/tables |

---

## Summary Recommendations

| Use Case | Recommended Tool |
|----------|------------------|
| **Complex scans, tables, forms** | PaddleOCR (PP-Structure) |
| **Academic docs, equations, handwriting** | olmOCR |
| **Simple forms/receipts** | docTR |
| **Basic printed text** | Tesseract + post-processing |
| **Markdown-focused workflows** | Docling |

> [!IMPORTANT]
> **PaddleOCR and olmOCR are your best bets** for robust layout handling without heavy tweaking. Combine with translation (LibreTranslate) and summarization (Hugging Face) for a full Linnk.ai alternative.
>
> Accuracy tanks on poor scans across the board—test on your files.
