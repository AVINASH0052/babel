#!/usr/bin/env python3
"""
Create PDF from structured JSON translation output.

This script reads the JSON output from translate_structured.py and
generates a professional PDF with:
- Proper image embedding
- Clean table rendering
- Math equation formatting
- Correct heading hierarchy
- Page structure preservation
"""

import json
import os
import re
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Unicode-capable fonts
try:
    pdfmetrics.registerFont(TTFont('ArialUnicode', '/Library/Fonts/Arial Unicode.ttf'))
    UNICODE_FONT = 'ArialUnicode'
except:
    try:
        pdfmetrics.registerFont(TTFont('ArialUnicode', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
        UNICODE_FONT = 'ArialUnicode'
    except:
        UNICODE_FONT = 'Helvetica'
        print("Warning: Arial Unicode not found, some characters may not display correctly")

# Configuration
INPUT_JSON = "/Users/avinash/Desktop/project/minerU/engine_output/translated_structured.json"
OUTPUT_PDF = "/Users/avinash/Desktop/project/minerU/engine_output/Spey_MK202_Structured.pdf"
IMAGE_BASE_DIR = "/Users/avinash/Desktop/project/minerU/engine_output"

# Page dimensions
PAGE_WIDTH, PAGE_HEIGHT = A4
CONTENT_WIDTH = PAGE_WIDTH - 1.2 * inch

# Unicode character maps for math
# Note: Not all letters have Unicode subscript versions - use HTML <sub> for those
SUBSCRIPTS = {
    '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
    '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
    'a': 'ₐ', 'e': 'ₑ', 'i': 'ᵢ', 'o': 'ₒ', 'r': 'ᵣ',
    'u': 'ᵤ', 'v': 'ᵥ', 'x': 'ₓ', 'n': 'ₙ', 'm': 'ₘ',
    'p': 'ₚ', 's': 'ₛ', 'k': 'ₖ', 'l': 'ₗ', 't': 'ₜ',
    'h': 'ₕ', 'j': 'ⱼ', '+': '₊', '-': '₋', '=': '₌',
    # These don't have true Unicode subscripts - leave as-is for HTML fallback
}

SUPERSCRIPTS = {
    '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
    'n': 'ⁿ', 'i': 'ⁱ', '+': '⁺', '-': '⁻', '=': '⁼',
    'a': 'ᵃ', 'b': 'ᵇ', 'c': 'ᶜ', 'd': 'ᵈ', 'e': 'ᵉ',
    'f': 'ᶠ', 'g': 'ᵍ', 'h': 'ʰ', 'j': 'ʲ', 'k': 'ᵏ',
    'l': 'ˡ', 'm': 'ᵐ', 'o': 'ᵒ', 'p': 'ᵖ', 'r': 'ʳ',
    's': 'ˢ', 't': 'ᵗ', 'u': 'ᵘ', 'v': 'ᵛ', 'w': 'ʷ',
    'x': 'ˣ', 'y': 'ʸ', 'z': 'ᶻ'
}


def to_subscript(text):
    """Convert text to subscript - keep unsupported chars as regular text."""
    result = []
    for c in str(text):
        lc = c.lower()
        if c in SUBSCRIPTS:
            result.append(SUBSCRIPTS[c])
        elif lc in SUBSCRIPTS:
            result.append(SUBSCRIPTS[lc])
        else:
            # No Unicode subscript exists - keep original character
            # This prevents hollow squares for M, T, P, C, etc.
            result.append(c)
    return ''.join(result)


def to_superscript(text):
    """Convert text to superscript - keep unsupported chars as regular text."""
    result = []
    for c in str(text):
        lc = c.lower()
        if c in SUPERSCRIPTS:
            result.append(SUPERSCRIPTS[c])
        elif lc in SUPERSCRIPTS:
            result.append(SUPERSCRIPTS[lc])
        else:
            # No Unicode superscript exists - keep original character
            result.append(c)
    return ''.join(result)


def format_latex(latex: str) -> str:
    """Convert LaTeX to Unicode representation."""
    if not latex:
        return ""
    
    # Greek letters
    greek = {
        r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ',
        r'\epsilon': 'ε', r'\eta': 'η', r'\theta': 'θ', r'\lambda': 'λ',
        r'\mu': 'μ', r'\nu': 'ν', r'\pi': 'π', r'\rho': 'ρ',
        r'\sigma': 'σ', r'\tau': 'τ', r'\phi': 'φ', r'\chi': 'χ',
        r'\psi': 'ψ', r'\omega': 'ω',
        r'\Gamma': 'Γ', r'\Delta': 'Δ', r'\Theta': 'Θ', r'\Lambda': 'Λ',
        r'\Sigma': 'Σ', r'\Phi': 'Φ', r'\Psi': 'Ψ', r'\Omega': 'Ω'
    }
    for k, v in greek.items():
        latex = latex.replace(k, v)
    
    # Operators and symbols
    symbols = {
        r'\times': '×', r'\cdot': '·', r'\div': '÷',
        r'\pm': '±', r'\mp': '∓',
        r'\leq': '≤', r'\geq': '≥', r'\neq': '≠', r'\ne': '≠',
        r'\approx': '≈', r'\equiv': '≡', r'\propto': '∝',
        r'\infty': '∞', r'\partial': '∂', r'\nabla': '∇',
        r'\rightarrow': '→', r'\leftarrow': '←', r'\Rightarrow': '⇒',
        r'\to': '→', r'\sum': 'Σ', r'\prod': 'Π', r'\int': '∫',
        r'\left(': '(', r'\right)': ')', r'\left[': '[', r'\right]': ']',
        r'\left\{': '{', r'\right\}': '}', r'\left': '', r'\right': '',
        r'\,': ' ', r'\;': ' ', r'\:': ' ', r'\!': '',
        r'\quad': '  ', r'\qquad': '    ',
        r'\cdots': '⋯', r'\ldots': '…', r'\dots': '…',
    }
    for k, v in symbols.items():
        latex = latex.replace(k, v)
    
    # Handle nested fractions - run multiple times
    for _ in range(5):
        # Match \frac with balanced braces (simplified - handle nested by iteration)
        latex = re.sub(r'\\frac\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', r'(\1)/(\2)', latex)
    
    # sqrt with optional power
    latex = re.sub(r'\\sqrt\[([^\]]+)\]\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', r'(\2)^(1/\1)', latex)
    for _ in range(3):
        latex = re.sub(r'\\sqrt\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', r'√(\1)', latex)
    
    # Subscripts - handle nested
    for _ in range(5):
        latex = re.sub(r'_\{([^{}]+)\}', lambda m: to_subscript(m.group(1)), latex)
    latex = re.sub(r'_([a-zA-Z0-9])', lambda m: to_subscript(m.group(1)), latex)
    
    # Superscripts - handle nested
    for _ in range(5):
        latex = re.sub(r'\^\{([^{}]+)\}', lambda m: to_superscript(m.group(1)), latex)
    latex = re.sub(r'\^([a-zA-Z0-9])', lambda m: to_superscript(m.group(1)), latex)
    
    # Text commands
    latex = re.sub(r'\\text\{([^}]*)\}', r'\1', latex)
    latex = re.sub(r'\\mathrm\{([^}]*)\}', r'\1', latex)
    latex = re.sub(r'\\textbf\{([^}]*)\}', r'\1', latex)
    latex = re.sub(r'\\textit\{([^}]*)\}', r'\1', latex)
    
    # Clean up remaining LaTeX commands
    latex = re.sub(r'\\[a-zA-Z]+\s*', '', latex)
    
    # Clean up braces
    latex = re.sub(r'[{}]', '', latex)
    latex = re.sub(r'\s+', ' ', latex)
    
    return latex.strip()


def escape_xml(text: str) -> str:
    """Escape XML special characters."""
    if not text:
        return ""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def process_inline_latex(text: str) -> str:
    r"""Process inline LaTeX expressions in text and convert to Unicode.
    
    Handles both \( ... \) and $ ... $ inline math notation.
    """
    if not text:
        return ""
    
    # Process \( ... \) inline math - use greedy match for content with braces
    def replace_inline(match):
        latex = match.group(1)
        return format_latex(latex)
    
    # Replace \( ... \) patterns - allow any content including braces
    text = re.sub(r'\\\(\s*(.*?)\s*\\\)', replace_inline, text)
    
    # Replace \[ ... \] display math patterns
    text = re.sub(r'\\\[\s*(.*?)\s*\\\]', replace_inline, text)
    
    # Replace $ ... $ patterns (but not $$)
    text = re.sub(r'(?<!\$)\$([^$]+)\$(?!\$)', replace_inline, text)
    
    # Also handle any remaining raw LaTeX commands that weren't in delimiters
    # This catches stray \frac, \sqrt etc that appear without delimiters
    text = format_latex(text)
    
    return text


def is_raw_json_content(text: str) -> bool:
    """Check if text appears to be raw unparsed JSON that shouldn't be rendered."""
    if not text or not isinstance(text, str):
        return False
    # Check for JSON-like patterns that indicate unparsed structured data
    json_indicators = [
        '"elements":', '"type":', '"headers":', '"rows":',
        '{"type":', '[{"type":', 
        'Here is the structured JSON', '```json',
    ]
    # Count how many indicators are present
    matches = sum(1 for ind in json_indicators if ind in text)
    # If multiple JSON indicators or very long with JSON patterns, it's raw JSON
    if matches >= 2:
        return True
    if len(text) > 500 and matches >= 1:
        return True
    return False


def parse_embedded_json(text: str) -> list:
    """
    Parse embedded JSON from text and return list of element dicts.
    Handles JSON wrapped in markdown code blocks or raw JSON.
    """
    if not text:
        return []
    
    elements = []
    
    # Try to extract JSON from markdown code block
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find raw JSON object or array
        # Look for { "elements": [...] } pattern
        json_match = re.search(r'\{\s*"elements"\s*:\s*\[[\s\S]*\]\s*\}', text)
        if json_match:
            json_str = json_match.group(0)
        else:
            # Try just the array
            json_match = re.search(r'\[\s*\{[\s\S]*\}\s*\]', text)
            if json_match:
                json_str = json_match.group(0)
            else:
                return []
    
    try:
        # Parse the JSON
        parsed = json.loads(json_str)
        
        # Handle {"elements": [...]} format
        if isinstance(parsed, dict) and "elements" in parsed:
            elements = parsed["elements"]
        # Handle direct array format
        elif isinstance(parsed, list):
            elements = parsed
        
        return elements if isinstance(elements, list) else []
    except json.JSONDecodeError:
        # Try fixing common JSON issues
        try:
            # Remove trailing commas
            fixed = re.sub(r',(\s*[}\]])', r'\1', json_str)
            # Add missing commas
            fixed = re.sub(r'\}(\s*)\{', r'},\1{', fixed)
            fixed = re.sub(r'\}(\s*)"', r'},\1"', fixed)
            
            parsed = json.loads(fixed)
            if isinstance(parsed, dict) and "elements" in parsed:
                return parsed["elements"]
            elif isinstance(parsed, list):
                return parsed
        except:
            pass
        
        return []


def extract_text_from_raw_json(text: str) -> str:
    """Extract readable text content from raw JSON-like strings as fallback."""
    if not text:
        return ""
    
    extracted_parts = []
    
    # Extract "content": "..." values (longer content first)
    content_matches = re.findall(r'"content"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
    for match in content_matches:
        try:
            unescaped = match.replace('\\"', '"').replace('\\n', ' ').replace('\\\\', '\\')
            # Only keep substantial text content
            if len(unescaped) > 20 and not unescaped.strip().startswith('{'):
                extracted_parts.append(unescaped.strip())
        except:
            pass
    
    # Extract "caption": "..." values  
    caption_matches = re.findall(r'"caption"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
    for match in caption_matches:
        try:
            unescaped = match.replace('\\"', '"').replace('\\n', ' ').replace('\\\\', '\\')
            if len(unescaped) > 5:
                extracted_parts.append(unescaped.strip())
        except:
            pass
    
    # Deduplicate while preserving order
    seen = set()
    unique_parts = []
    for p in extracted_parts:
        if p not in seen:
            seen.add(p)
            unique_parts.append(p)
    
    return '\n\n'.join(unique_parts)


def format_content(text) -> str:
    """Process text content: handle inline LaTeX then escape XML."""
    if not text:
        return ""
    
    # Handle non-string types (dicts, lists, etc.)
    if isinstance(text, dict):
        # Extract content from dict - try common keys
        text = text.get('content', '') or text.get('text', '') or str(text)
    elif not isinstance(text, str):
        text = str(text)
    
    # If it looks like raw JSON, try to extract readable content from it
    if is_raw_json_content(text):
        extracted = extract_text_from_raw_json(text)
        if extracted:
            text = extracted
        else:
            # Can't extract anything meaningful - skip this garbage
            return ""
    
    # First process LaTeX to Unicode
    text = process_inline_latex(text)
    
    # Remove any remaining backslash-letter sequences (unprocessed LaTeX)
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    
    # Clean up empty braces and brackets
    text = re.sub(r'\{\s*\}', '', text)
    text = re.sub(r'\[\s*\]', '', text)
    
    # Remove stray backslashes before parentheses
    text = text.replace('\\(', '(').replace('\\)', ')')
    text = text.replace('\\[', '[').replace('\\]', ']')
    
    # Then escape XML special characters
    text = escape_xml(text)
    return text


def find_image(image_path: str) -> str:
    """Find actual image file."""
    if os.path.isabs(image_path) and os.path.exists(image_path):
        return image_path
    
    full_path = os.path.join(IMAGE_BASE_DIR, image_path)
    if os.path.exists(full_path):
        return full_path
    
    filename = os.path.basename(image_path)
    for chunk_dir in sorted(Path(IMAGE_BASE_DIR).glob("extracted_chunk_*")):
        potential = chunk_dir / "images" / filename
        if potential.exists():
            return str(potential)
    
    return None


def create_styles():
    """Create paragraph styles."""
    styles = getSampleStyleSheet()
    
    # Headings - use Unicode font
    for level, (size, color) in enumerate([
        (20, '#1a365d'), (16, '#2c5282'), (14, '#2b6cb0'),
        (12, '#3182ce'), (11, '#4299e1'), (10, '#63b3ed')
    ], 1):
        styles.add(ParagraphStyle(
            name=f'H{level}',
            parent=styles['Heading1'],
            fontName=UNICODE_FONT,
            fontSize=size,
            spaceBefore=14 if level <= 2 else 10,
            spaceAfter=8 if level <= 2 else 6,
            textColor=colors.HexColor(color)
        ))
    
    # Body - use Unicode font for Greek letters, subscripts etc
    styles.add(ParagraphStyle(
        name='Body',
        parent=styles['Normal'],
        fontName=UNICODE_FONT,
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceBefore=4,
        spaceAfter=4
    ))
    
    # Math equation - use Unicode font for Greek letters, subscripts
    styles.add(ParagraphStyle(
        name='Equation',
        parent=styles['Normal'],
        fontName=UNICODE_FONT,
        fontSize=11,
        leading=16,
        alignment=TA_CENTER,
        spaceBefore=10,
        spaceAfter=10,
        textColor=colors.HexColor('#1a202c'),
        backColor=colors.HexColor('#f7fafc'),
        borderPadding=8
    ))
    
    # Image caption
    styles.add(ParagraphStyle(
        name='Caption',
        parent=styles['Normal'],
        fontName=UNICODE_FONT,
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#4a5568'),
        spaceBefore=4,
        spaceAfter=8
    ))
    
    # Image description
    styles.add(ParagraphStyle(
        name='ImageDesc',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#718096'),
        fontName=UNICODE_FONT,
        leftIndent=20,
        rightIndent=20,
        spaceBefore=2,
        spaceAfter=10
    ))
    
    # Image placeholder
    styles.add(ParagraphStyle(
        name='ImagePlaceholder',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#a0aec0'),
        backColor=colors.HexColor('#edf2f7'),
        borderWidth=1,
        borderColor=colors.HexColor('#cbd5e0'),
        borderPadding=8,
        spaceBefore=8,
        spaceAfter=8
    ))
    
    # Table cell - use Unicode font
    styles.add(ParagraphStyle(
        name='TableCell',
        parent=styles['Normal'],
        fontName=UNICODE_FONT,
        fontSize=9,
        leading=11
    ))
    
    # List item - use Unicode font
    styles.add(ParagraphStyle(
        name='ListItem',
        parent=styles['Normal'],
        fontName=UNICODE_FONT,
        fontSize=10,
        leading=13,
        leftIndent=20,
        spaceBefore=2,
        spaceAfter=2
    ))
    
    # Code/spec
    styles.add(ParagraphStyle(
        name='CodeBlock',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Courier',
        backColor=colors.HexColor('#f7fafc'),
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=6
    ))
    
    # Section marker - shows original page range
    styles.add(ParagraphStyle(
        name='SectionMarker',
        parent=styles['Normal'],
        fontSize=11,
        fontName=UNICODE_FONT,
        textColor=colors.HexColor('#2d3748'),
        backColor=colors.HexColor('#e2e8f0'),
        borderPadding=8,
        spaceBefore=20,
        spaceAfter=10,
        alignment=TA_CENTER
    ))
    
    return styles


def render_element(element: dict, styles: dict, stats: dict) -> list:
    """Render a single element to PDF flowables."""
    flowables = []
    elem_type = element.get("type", "unknown")
    
    # Heading
    if elem_type == "heading":
        level = min(element.get("level", 1), 6)
        content = format_content(element.get("content", ""))
        if content:
            flowables.append(Paragraph(content, styles[f'H{level}']))
    
    # Paragraph - check for embedded JSON first
    elif elem_type == "paragraph":
        raw_content = element.get("content", "")
        
        # Check if this paragraph contains embedded JSON that should be parsed
        if isinstance(raw_content, str) and is_raw_json_content(raw_content):
            # Try to parse and render embedded JSON elements
            embedded_elements = parse_embedded_json(raw_content)
            if embedded_elements:
                # Recursively render each embedded element
                for sub_elem in embedded_elements:
                    if isinstance(sub_elem, dict):
                        sub_flowables = render_element(sub_elem, styles, stats)
                        flowables.extend(sub_flowables)
            else:
                # Fallback: extract text content from the JSON
                extracted = extract_text_from_raw_json(raw_content)
                if extracted:
                    # Split into paragraphs and render each
                    for para in extracted.split('\n\n'):
                        para = para.strip()
                        if para:
                            formatted = format_content(para) if not is_raw_json_content(para) else ""
                            if formatted:
                                flowables.append(Paragraph(formatted, styles['Body']))
        else:
            # Normal paragraph
            content = format_content(raw_content)
            if content:
                flowables.append(Paragraph(content, styles['Body']))
    
    # Equation
    elif elem_type == "equation":
        latex = element.get("latex", "")
        formatted = format_latex(latex)
        if formatted:
            flowables.append(Paragraph(formatted, styles['Equation']))
            stats['equations'] += 1
        
        # Optional description
        desc = element.get("description", "")
        if desc:
            flowables.append(Paragraph(f"<i>{format_content(desc)}</i>", styles['Caption']))
    
    # Table
    elif elem_type == "table":
        headers = element.get("headers", [])
        rows = element.get("rows", [])
        caption = element.get("caption", "")
        
        if headers or rows:
            # Build table data
            table_data = []
            
            if headers:
                header_row = [Paragraph(f"<b>{format_content(h)}</b>", styles['TableCell']) for h in headers]
                table_data.append(header_row)
            
            for row in rows:
                table_row = [Paragraph(format_content(str(cell)), styles['TableCell']) for cell in row]
                table_data.append(table_row)
            
            if table_data:
                num_cols = max(len(row) for row in table_data)
                col_width = (CONTENT_WIDTH - 0.2 * inch) / num_cols
                
                table = Table(table_data, colWidths=[col_width] * num_cols)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                
                if caption:
                    flowables.append(Paragraph(f"<b>{format_content(caption)}</b>", styles['Caption']))
                
                flowables.append(table)
                flowables.append(Spacer(1, 10))
                stats['tables'] += 1
    
    # Image
    elif elem_type == "image":
        path = element.get("path", "")
        caption = element.get("caption", "")
        description = element.get("description", "")
        
        actual_path = find_image(path)
        
        if actual_path:
            try:
                img = Image(actual_path)
                
                # Scale to fit
                max_width = CONTENT_WIDTH
                max_height = PAGE_HEIGHT * 0.4
                
                if img.drawWidth > max_width:
                    ratio = max_width / img.drawWidth
                    img.drawWidth = max_width
                    img.drawHeight *= ratio
                
                if img.drawHeight > max_height:
                    ratio = max_height / img.drawHeight
                    img.drawHeight = max_height
                    img.drawWidth *= ratio
                
                flowables.append(img)
                stats['images_embedded'] += 1
                
            except Exception as e:
                flowables.append(Paragraph(
                    f"[Image Error: {escape_xml(str(e))}]",
                    styles['ImagePlaceholder']
                ))
                stats['images_failed'] += 1
        else:
            flowables.append(Paragraph(
                f"[Image not found: {escape_xml(path)}]",
                styles['ImagePlaceholder']
            ))
            stats['images_missing'] += 1
        
        if caption:
            flowables.append(Paragraph(f"<b>{format_content(caption)}</b>", styles['Caption']))
        
        if description:
            flowables.append(Paragraph(format_content(description), styles['ImageDesc']))
    
    # List
    elif elem_type == "list":
        items = element.get("items", [])
        ordered = element.get("ordered", False)
        
        for idx, item in enumerate(items, 1):
            prefix = f"{idx}." if ordered else "•"
            flowables.append(Paragraph(
                f"{prefix} {format_content(item)}",
                styles['ListItem']
            ))
    
    # Code/specification
    elif elem_type == "code":
        content = element.get("content", "")
        if content:
            flowables.append(Paragraph(escape_xml(content), styles['CodeBlock']))
    
    # Section marker - shows original page range from source document
    elif elem_type == "section_marker":
        chunk_num = element.get("chunk_num", 0)
        page_info = element.get("page_info", "")
        flowables.append(PageBreak())
        # Format section header - avoid emoji that may not render in all fonts
        if page_info:
            marker_text = f"— Section {chunk_num} —<br/><font size='10'>Content from Original Document{page_info}</font>"
        else:
            marker_text = f"— Section {chunk_num} —"
        flowables.append(Paragraph(marker_text, styles['SectionMarker']))
    
    return flowables


def add_page_number(canvas, doc):
    """Add page number to each page."""
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.HexColor('#718096'))
    canvas.drawCentredString(PAGE_WIDTH / 2, 20 * mm, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def create_pdf_from_structured(input_json: str = INPUT_JSON, output_pdf: str = OUTPUT_PDF):
    """Create PDF from structured JSON."""
    
    print("=" * 60)
    print("CREATING PDF FROM STRUCTURED JSON")
    print("=" * 60)
    
    # Load JSON
    print(f"\nInput: {input_json}")
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both flat elements format and chunked format
    if "chunks" in data:
        # Chunked format from translation progress
        chunks = data.get("chunks", [])
        elements = []
        for chunk in chunks:
            chunk_num = chunk.get("chunk_num", 0)
            original_pages = chunk.get("original_pages", "")
            # Add section marker at start of each chunk (except first)
            if chunk_num > 0:
                page_info = f" (Pages {original_pages})" if original_pages else ""
                elements.append({
                    "type": "section_marker",
                    "chunk_num": chunk_num,
                    "page_info": page_info
                })
            # Add all elements from this chunk
            elements.extend(chunk.get("elements", []))
        total_chunks = len(chunks)
    else:
        # Flat format with metadata
        metadata = data.get("metadata", {})
        elements = data.get("elements", [])
        total_chunks = metadata.get('total_chunks', 'N/A')
    
    print(f"Total elements: {len(elements)}")
    print(f"Source chunks: {total_chunks}")
    
    # Create styles
    styles = create_styles()
    
    # Track statistics
    stats = {
        'images_embedded': 0,
        'images_missing': 0,
        'images_failed': 0,
        'tables': 0,
        'equations': 0
    }
    
    # Render elements
    print("\nRendering elements...")
    flowables = []
    
    # Add title
    flowables.append(Paragraph(
        "Spey MK202 Engine Design and Test Data Compilation",
        styles['H1']
    ))
    flowables.append(Paragraph(
        "Volume 2 - Translated from Chinese",
        styles['H2']
    ))
    flowables.append(Spacer(1, 20))
    
    # Process each element
    for element in elements:
        element_flowables = render_element(element, styles, stats)
        flowables.extend(element_flowables)
    
    print(f"Generated {len(flowables)} PDF flowables")
    print(f"  - Images embedded: {stats['images_embedded']}")
    print(f"  - Images missing: {stats['images_missing']}")
    print(f"  - Tables: {stats['tables']}")
    print(f"  - Equations: {stats['equations']}")
    
    # Build PDF
    print("\nBuilding PDF...")
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.8 * inch
    )
    
    doc.build(flowables, onFirstPage=add_page_number, onLaterPages=add_page_number)
    
    # Report
    file_size = os.path.getsize(output_pdf) / (1024 * 1024)
    
    print(f"\n{'=' * 60}")
    print("PDF CREATION COMPLETE!")
    print(f"{'=' * 60}")
    print(f"  Output: {output_pdf}")
    print(f"  Size: {file_size:.2f} MB")
    print(f"  Images: {stats['images_embedded']} embedded, {stats['images_missing']} missing")
    print(f"  Tables: {stats['tables']}")
    print(f"  Equations: {stats['equations']}")


if __name__ == "__main__":
    import sys
    
    input_json = INPUT_JSON
    output_pdf = OUTPUT_PDF
    
    if len(sys.argv) > 1:
        input_json = sys.argv[1]
    if len(sys.argv) > 2:
        output_pdf = sys.argv[2]
    
    create_pdf_from_structured(input_json, output_pdf)
