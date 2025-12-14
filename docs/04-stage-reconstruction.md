# Stage 4: Reconstruction (The "Typesetter")

## Purpose

Assemble translated content back into a publication-quality PDF that mirrors the original layout.

---

## Component Architecture

```python
class Reconstructor:
    """
    Rebuilds PDF from translated structured content.
    
    Responsibilities:
    - Render text at original positions with translated content
    - Overlay translated labels on preserved diagrams
    - Reconstruct tables with translated cell content
    - Render LaTeX formulas
    - Assemble final PDF with selectable text layer
    """
    
    def __init__(self, config: ReconstructionConfig):
        self.typesetter = config.typesetter  # 'typst' | 'latex' | 'reportlab'
        self.font_matcher = FontMatcher()
        self.image_handler = ImageHandler()
        
    def reconstruct(self, 
                    original_pages: List[PageImage],
                    structures: List[PageStructure],
                    translations: List[TranslatedPage]) -> bytes:
        """Returns PDF bytes."""
        pass
```

---

## Reconstruction Pipeline

```
INPUT: Original Pages + Translated Structures
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  4.1 ELEMENT CLASSIFICATION                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ For each element, determine reconstruction strategy:    │    │
│  │                                                          │    │
│  │ • PASS_THROUGH: Images without text → direct copy       │    │
│  │ • TEXT_REPLACE: Text blocks → render translated text    │    │
│  │ • TABLE_REBUILD: Tables → reconstruct grid + content    │    │
│  │ • FORMULA_RENDER: LaTeX → typeset at position           │    │
│  │ • DIAGRAM_OVERLAY: Figures → inpaint + overlay labels   │    │
│  └─────────────────────────────────────────────────────────┘    │
│         │                                                        │
│         ▼                                                        │
│  4.2 FONT ANALYSIS & MATCHING                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Analyze original text pixels for font characteristics │    │
│  │ • Detect: Serif/Sans, Weight, Style, Size               │    │
│  │ • Match to available digital fonts                       │    │
│  │ • Calculate size adjustment for text length changes      │    │
│  └─────────────────────────────────────────────────────────┘    │
│         │                                                        │
│         ▼                                                        │
│  4.3 TEXT LENGTH COMPENSATION                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Problem: German text is ~30% longer than English        │    │
│  │                                                          │    │
│  │ Solutions (in order of preference):                      │    │
│  │ 1. Reduce font size (max 15% reduction)                  │    │
│  │ 2. Tighten character spacing (kerning)                   │    │
│  │ 3. Allow text to flow to next line (if block)            │    │
│  │ 4. Flag for human review if none work                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│         │                                                        │
│         ▼                                                        │
│  4.4 DIAGRAM LABEL RENDERING                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ For each diagram with translated labels:                 │    │
│  │                                                          │    │
│  │ 1. PRESERVE original image (no modifications to pixels) │    │
│  │ 2. For labels on simple backgrounds:                     │    │
│  │    → Render translated text directly over original       │    │
│  │ 3. For labels on complex backgrounds:                    │    │
│  │    → LaMa inpainting to erase original label region      │    │
│  │    → Render translated text on cleaned region            │    │
│  │ 4. Composite all label layers onto preserved image       │    │
│  └─────────────────────────────────────────────────────────┘    │
│         │                                                        │
│         ▼                                                        │
│  4.5 PAGE ASSEMBLY                                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Layer composition (bottom to top):                       │    │
│  │                                                          │    │
│  │ ┌─────────────────────────────────────────────────────┐ │    │
│  │ │ Layer 1: Background (original page as image base)   │ │    │
│  │ ├─────────────────────────────────────────────────────┤ │    │
│  │ │ Layer 2: Preserved elements (unchanged diagrams)    │ │    │
│  │ ├─────────────────────────────────────────────────────┤ │    │
│  │ │ Layer 3: Translated text (positioned precisely)     │ │    │
│  │ ├─────────────────────────────────────────────────────┤ │    │
│  │ │ Layer 4: Diagram label overlays                     │ │    │
│  │ ├─────────────────────────────────────────────────────┤ │    │
│  │ │ Layer 5: Rendered formulas                          │ │    │
│  │ └─────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────┘    │
│         │                                                        │
│         ▼                                                        │
│  OUTPUT: Final PDF with selectable text layer                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Selection

| Component | Primary | Fallback | Notes |
|-----------|---------|----------|-------|
| **Typesetting** | Typst | LaTeX (via latexmk) | Typst: 10x faster compilation |
| **PDF Assembly** | PyMuPDF | ReportLab | Direct layer control |
| **Inpainting** | LaMa | Simple background fill | LaMa for complex textures |
| **Font Rendering** | Pillow + FreeType | Cairo | Subpixel rendering |

---

## Next

→ [Cross-Cutting Concerns](./05-cross-cutting.md)
