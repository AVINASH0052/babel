# Stage 1: Ingestion & Pre-Processing

## Purpose

Convert raw scanned PDF pages into clean, high-resolution images optimized for OCR and layout analysis.

---

## Component Architecture

```python
class IngestionPipeline:
    """
    Converts PDF → optimized page images with metadata.
    
    Responsibilities:
    - PDF parsing and page extraction
    - Image quality enhancement (deskew, denoise)
    - Resolution normalization
    - Metadata extraction (page count, dimensions, DPI)
    """
    
    def __init__(self, config: IngestionConfig):
        self.pdf_backend = config.pdf_backend  # 'pymupdf' | 'pdf2image'
        self.target_dpi = config.target_dpi    # Default: 300
        self.enable_enhancement = config.enable_enhancement
        
    def process(self, pdf_path: Path) -> List[PageImage]:
        """Returns list of processed page images with metadata."""
        pass
```

---

## Technology Selection

| Component | Primary | Fallback | Selection Criteria |
|-----------|---------|----------|-------------------|
| **PDF Parsing** | `PyMuPDF (fitz)` | `pdf2image` | Speed, memory efficiency, metadata preservation |
| **Deskewing** | `OpenCV` | `deskew` | Sub-degree accuracy for scanned documents |
| **Denoising** | `OpenCV (fastNlMeans)` | `scikit-image` | Preserve text edges while removing scanner artifacts |
| **Enhancement** | `Real-ESRGAN` | None | Optional 4x upscaling for low-DPI scans |

---

## Pre-Processing Pipeline

```
INPUT: Scanned PDF (image-only, no text layer)
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  1.1 PDF EXTRACTION                                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Extract each page as raster image                     │    │
│  │ • Detect native resolution (DPI)                        │    │
│  │ • Upscale if < 300 DPI (Real-ESRGAN optional)           │    │
│  │ • Output format: PNG (lossless) or TIFF                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│         │                                                        │
│         ▼                                                        │
│  1.2 GEOMETRIC CORRECTION                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Deskew: Hough transform line detection                │    │
│  │ • Crop: Remove black borders from scanning              │    │
│  │ • Perspective: Correct keystoning (rare)                │    │
│  └─────────────────────────────────────────────────────────┘    │
│         │                                                        │
│         ▼                                                        │
│  1.3 IMAGE ENHANCEMENT                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Denoise: Remove scanner noise (preserve text edges)   │    │
│  │ • Contrast: Adaptive histogram equalization             │    │
│  │ • Binarization: Optional for pure B&W documents         │    │
│  └─────────────────────────────────────────────────────────┘    │
│         │                                                        │
│         ▼                                                        │
│  OUTPUT: List[PageImage] with metadata                          │
│  • page_number, dimensions, dpi, skew_angle_corrected           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Configuration Schema

```yaml
ingestion:
  pdf_backend: "pymupdf"
  target_dpi: 300
  max_dimension: 4096  # Prevent OOM on very large pages
  
  preprocessing:
    deskew:
      enabled: true
      max_angle: 10  # Degrees; beyond this, flag for review
      
    denoise:
      enabled: true
      strength: 10  # OpenCV fastNlMeans parameter
      
    enhance:
      upscale_threshold_dpi: 200  # Upscale if source DPI below this
      upscaler: "real_esrgan"     # Optional neural upscaling
```

---

## Next Stage

→ [Stage 2: Extraction](./02-stage-extraction.md)
