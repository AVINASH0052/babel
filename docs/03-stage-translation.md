# Stage 3: Translation Engine (The "Linguist")

## Purpose

Translate extracted text while maintaining context, terminology consistency, and technical accuracy.

---

## Component Architecture

```python
class TranslationEngine:
    """
    Context-aware translation with glossary enforcement.
    
    Responsibilities:
    - Translate text blocks with document context
    - Translate diagram labels via VLM
    - Maintain terminology glossary across pages
    - Handle formula surrounding text
    - Provide confidence scores
    """
    
    def __init__(self, config: TranslationConfig):
        self.llm = config.llm_backend       # 'deepseek' | 'openai' | 'ollama'
        self.vlm = config.vlm_backend       # 'qwen2.5-vl' | 'internvl2'
        self.source_lang = config.source_lang
        self.target_lang = config.target_lang
        self.glossary = Glossary()          # Session-wide term consistency
        
    def translate_text(self, element: Element, context: DocumentContext) -> TranslatedElement:
        pass
        
    def translate_diagram(self, image: Image, element: Element) -> DiagramTranslation:
        pass
```

---

## Translation Strategy

### Text Block Translation (LLM)

```python
def build_translation_prompt(element: Element, context: DocumentContext) -> str:
    """
    Constructs context-aware prompt for LLM translation.
    """
    return f"""
You are a technical translator specializing in {context.domain} documents.

## Document Context
- Document Type: {context.document_type}  # e.g., "Mechanical Engineering Textbook"
- Current Section: {context.current_section}  # e.g., "Chapter 3: Gear Systems"
- Previous Paragraphs Summary: {context.previous_summary}

## Glossary (Use these exact translations)
{context.glossary.to_markdown_table()}

## Element Context
- Element Type: {element.type.value}  # e.g., "caption"
- Nearby Elements: {context.get_nearby_elements(element.id)}

## Translation Task
Source Language: {context.source_lang}
Target Language: {context.target_lang}

Source Text:
```
{element.content}
```

## Instructions
1. Translate the source text maintaining technical accuracy
2. Use glossary terms exactly as specified
3. Preserve any inline LaTeX (e.g., $x^2$) without translation
4. Maintain formatting (bullet points, numbered lists)
5. For captions, keep reference numbers (e.g., "Figure 3.2")

## Output Format
Return ONLY the translated text, no explanations.
"""
```

---

### Diagram Label Translation (VLM)

```python
def build_vlm_prompt(element: Element) -> str:
    """
    Prompt for Vision-Language Model to extract and translate diagram labels.
    """
    return f"""
Analyze this technical diagram from an engineering document.

## Task
1. Identify ALL text labels, annotations, and legends in the image
2. For each text element, provide:
   - Original text (exactly as shown)
   - Translated text (to {self.target_lang})
   - Bounding box coordinates (x1, y1, x2, y2 as percentages 0-100)
   - Font size estimate (small/medium/large)
   - Text color (hex code or name)

## Important
- Include dimension labels (e.g., "50mm", "2.5 inches")
- Include part callouts (e.g., "A", "B", "Item 1")
- Include legend entries
- DO NOT translate measurement units
- DO NOT translate standard symbols (Ω, μ, etc.)

## Output Format (JSON)
{{
  "labels": [
    {{
      "original": "ギアボックス",
      "translated": "Gearbox",
      "bbox": {{"x1": 45.2, "y1": 30.1, "x2": 55.8, "y2": 35.4}},
      "font_size": "medium",
      "color": "#000000"
    }}
  ],
  "confidence": 0.92
}}
"""
```

---

## Glossary Management

```python
class Glossary:
    """
    Maintains consistent terminology across entire document.
    
    Features:
    - Auto-learns terms from first occurrence
    - User can pre-load domain glossary
    - Exports for review
    """
    
    def __init__(self):
        self.terms: Dict[str, str] = {}  # source → target
        self.occurrences: Dict[str, List[str]] = {}  # term → page numbers
        
    def add_term(self, source: str, target: str, page: int):
        if source not in self.terms:
            self.terms[source] = target
            self.occurrences[source] = []
        self.occurrences[source].append(page)
        
    def get_translation(self, source: str) -> Optional[str]:
        return self.terms.get(source)
        
    def to_markdown_table(self) -> str:
        """For injection into LLM prompts."""
        lines = ["| Source | Target |", "|--------|--------|"]
        for src, tgt in self.terms.items():
            lines.append(f"| {src} | {tgt} |")
        return "\n".join(lines)
```

---

## Technology Selection

| Component | Primary | Fallback | Notes |
|-----------|---------|----------|-------|
| **LLM (Translation)** | DeepSeek-V3 API | Llama 3.3 70B (Ollama) | Context window: 128K+ tokens |
| **VLM (Diagrams)** | Qwen2.5-VL-72B | InternVL2-26B | Open-source, vision-capable |
| **Embedding (Glossary)** | text-embedding-3-small | BGE-M3 | For fuzzy term matching |

---

## Next Stage

→ [Stage 4: Reconstruction](./04-stage-reconstruction.md)
