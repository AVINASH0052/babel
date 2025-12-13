# Stage 2: Structure Extraction (The "Brain")

## Purpose

Analyze page images to identify and classify all document elements: text blocks, tables, formulas, images, and their spatial relationships.

---

## Component Architecture

```python
class StructureExtractor:
    """
    Extracts semantic structure from page images.
    
    Produces:
    - Text blocks with coordinates and content
    - Tables with cell structure (rows, columns, merged cells)
    - Formulas as LaTeX strings with positions
    - Image regions as cropped files with captions
    - Reading order and parent-child relationships
    """
    
    def __init__(self, config: ExtractionConfig):
        self.layout_engine = config.layout_engine  # 'mineru' | 'surya'
        self.ocr_engine = config.ocr_engine        # 'mineru' | 'paddleocr'
        self.formula_engine = config.formula_engine  # 'mineru' | 'nougat'
        
    def extract(self, page: PageImage) -> PageStructure:
        """Returns structured representation of page content."""
        pass
```

---

## The MinerU Advantage

**MinerU (Magic-PDF)** is the primary extraction engine because it provides:

| Capability | How It Works | Why It Matters |
|------------|--------------|----------------|
| **Layout Analysis** | Transformer-based document understanding (LayoutLMv3-style) | Classifies regions as text/table/figure/formula |
| **Formula → LaTeX** | Dedicated math recognition model | `E=mc²` becomes `$E=mc^2$`, not garbled OCR |
| **Table Structure** | Grid line detection + cell content extraction | Preserves row/column logic for invisible-border tables |
| **Image Segmentation** | Separates figures from surrounding text | Enables targeted diagram translation |
| **Reading Order** | Understands multi-column layouts | Correct text flow, not left-to-right pixel order |

---

## Extraction Pipeline

```
INPUT: PageImage (enhanced)
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  2.1 LAYOUT ANALYSIS                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Model: MinerU / LayoutLMv3                              │    │
│  │                                                          │    │
│  │ Detects bounding boxes for:                              │    │
│  │ • TEXT_BLOCK: Paragraphs, headings, captions            │    │
│  │ • TABLE: Tabular data regions                           │    │
│  │ • FORMULA: Mathematical expressions                      │    │
│  │ • FIGURE: Images, diagrams, charts                       │    │
│  │ • HEADER/FOOTER: Page numbers, running titles            │    │
│  └─────────────────────────────────────────────────────────┘    │
│         │                                                        │
│         ├─────────────────┬─────────────────┬──────────────────┐ │
│         ▼                 ▼                 ▼                  ▼ │
│  ┌───────────┐     ┌───────────┐     ┌───────────┐    ┌─────────┐│
│  │ 2.2 TEXT  │     │ 2.3 TABLE │     │2.4 FORMULA│    │2.5 IMAGE││
│  │ REGIONS   │     │ REGIONS   │     │ REGIONS   │    │ REGIONS ││
│  └───────────┘     └───────────┘     └───────────┘    └─────────┘│
│       │                 │                 │                │     │
│       ▼                 ▼                 ▼                ▼     │
│  ┌───────────┐     ┌───────────┐     ┌───────────┐    ┌─────────┐│
│  │ OCR Text  │     │ Cell      │     │ LaTeX     │    │ Crop &  ││
│  │ Extraction│     │ Extraction│     │ Conversion│    │ Store   ││
│  │           │     │ (row/col) │     │           │    │         ││
│  └───────────┘     └───────────┘     └───────────┘    └─────────┘│
│       │                 │                 │                │     │
│       └─────────────────┴─────────────────┴────────────────┘     │
│                                   │                               │
│                                   ▼                               │
│  OUTPUT: PageStructure                                           │
│  • elements: List[Element] with type, bbox, content              │
│  • reading_order: List[int] (element indices in read sequence)   │
│  • images: Dict[id → cropped_image_path]                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Structures

```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Tuple

class ElementType(Enum):
    TEXT_BLOCK = "text_block"
    HEADING = "heading"
    TABLE = "table"
    FORMULA = "formula"
    FIGURE = "figure"
    CAPTION = "caption"
    HEADER = "header"
    FOOTER = "footer"
    LIST_ITEM = "list_item"

@dataclass
class BoundingBox:
    """Normalized coordinates (0-1) relative to page dimensions."""
    x1: float
    y1: float
    x2: float
    y2: float
    
    def to_pixels(self, width: int, height: int) -> Tuple[int, int, int, int]:
        return (
            int(self.x1 * width),
            int(self.y1 * height),
            int(self.x2 * width),
            int(self.y2 * height)
        )

@dataclass
class TableCell:
    row: int
    col: int
    row_span: int
    col_span: int
    content: str
    is_header: bool

@dataclass
class TableStructure:
    rows: int
    cols: int
    cells: List[TableCell]
    has_visible_borders: bool

@dataclass
class Element:
    id: str
    type: ElementType
    bbox: BoundingBox
    content: str                      # OCR text or LaTeX
    confidence: float                 # OCR/detection confidence
    table_structure: Optional[TableStructure] = None
    image_path: Optional[str] = None  # For FIGURE elements
    caption_id: Optional[str] = None  # Links figure to caption

@dataclass
class PageStructure:
    page_number: int
    width: int
    height: int
    elements: List[Element]
    reading_order: List[str]  # Element IDs in reading sequence
    
    def get_translatable_text(self) -> List[Tuple[str, str]]:
        """Returns (element_id, text_content) for translation."""
        pass
```

---

## Fallback Strategy

```
PRIMARY: MinerU
    │
    ├── If formula detection fails → Fallback: Nougat (Meta)
    │
    ├── If OCR quality low → Fallback: Surya (line-level)
    │
    └── If table structure breaks → Fallback: PaddleOCR PP-Structure
```

---

## Next Stage

→ [Stage 3: Translation](./03-stage-translation.md)
