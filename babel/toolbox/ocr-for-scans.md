# OCR for Scanned Documents

> **Core Capability for Non-Grabbable Text**

This is the foundation for handling images/PDFs without selectable text. These tools extract text via optical character recognition, often with better results on clean scans than handwriting or complex layouts.

---

## Primary Tools

### Tesseract OCR

**The gold standard open-source engine** (from Google, but fully OSS).

| Aspect | Details |
|--------|---------|
| **Languages** | 100+ supported |
| **Text Types** | Printed, handwritten, tables, layouts |
| **Python** | `pytesseract` bindings |
| **Accuracy** | 80-95% on good scans |
| **Notes** | Needs preprocessing for noisy docs. Combine with `pdf2image` for scanned PDFs. Not as "smart" as Linnk.ai's AI rebuild, but free and extensible. |

```bash
pip install pytesseract pdf2image
```

---

### PaddleOCR

**From Baidu, highly accurate for multilingual text** (including Chinese/Asian scripts).

| Aspect | Details |
|--------|---------|
| **Strengths** | Better than Tesseract for curved/distorted text or dense layouts |
| **Hardware** | Runs on CPU/GPU |
| **Accuracy** | 90%+ on real-world docs |
| **Pipeline** | Supports end-to-end processing |
| **Notes** | Easy to script for batch processing |

```bash
pip install paddlepaddle paddleocr
```

---

### docTR

**Python library using deep learning** for text detection and recognition.

| Aspect | Details |
|--------|---------|
| **Specialty** | Document-specific tasks (invoices, forms) |
| **Integration** | Integrates well with other tools |
| **Accuracy** | Rivals commercial options on structured docs |
| **Notes** | If your scans have tables/equations, this edges out Tesseract |

```bash
pip install python-doctr
```

---

### olmOCR (AllenAI)

**Specialized for converting PDFs** (scanned or not) to text while preserving structure.

| Aspect | Details |
|--------|---------|
| **Preserves** | Reading order, tables, equations, handwriting |
| **Output** | Clean Markdown/XML |
| **Runs** | Locally, open-source |
| **Notes** | Handles complex academic/professional docs better than basic OCR. Comparable to Linnk.ai's structure preservation, but no built-in translation/summarization—add those separately. |

---

## Niche Alternatives

| Tool | Best For |
|------|----------|
| **EasyOCR** | Simple, multilingual (quick setup) |
| **GOT-OCR** | Handwriting recognition |

> [!NOTE]
> Expect to script these tools (e.g., via Python) for automation. No drag-and-drop UI out of the box.
