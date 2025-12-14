#!/usr/bin/env python3
"""Create clean PDF with proper math rendering. No images."""

import re
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

INPUT_MD = "/Users/avinash/Desktop/project/minerU/engine_output/translated_english_mistral.md"
OUTPUT_PDF = "/Users/avinash/Desktop/project/minerU/engine_output/Spey_MK202_Engine_Clean.pdf"

SUBSCRIPTS = {'0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅','6':'₆','7':'₇','8':'₈','9':'₉',
    'a':'ₐ','e':'ₑ','i':'ᵢ','o':'ₒ','r':'ᵣ','u':'ᵤ','v':'ᵥ','x':'ₓ','n':'ₙ','m':'ₘ',
    'p':'ₚ','s':'ₛ','k':'ₖ','l':'ₗ','t':'ₜ','h':'ₕ','j':'ⱼ','+':'₊','-':'₋','=':'₌'}

SUPERSCRIPTS = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹',
    'n':'ⁿ','i':'ⁱ','+':'⁺','-':'⁻','=':'⁼','a':'ᵃ','b':'ᵇ','c':'ᶜ','d':'ᵈ','e':'ᵉ',
    'f':'ᶠ','g':'ᵍ','h':'ʰ','j':'ʲ','k':'ᵏ','l':'ˡ','m':'ᵐ','o':'ᵒ','p':'ᵖ','r':'ʳ',
    's':'ˢ','t':'ᵗ','u':'ᵘ','v':'ᵛ','w':'ʷ','x':'ˣ','y':'ʸ','z':'ᶻ'}

def to_sub(t): return ''.join(SUBSCRIPTS.get(c,c) for c in str(t))
def to_sup(t): return ''.join(SUPERSCRIPTS.get(c,c) for c in str(t))

def format_math(math):
    if not math: return ""
    greek = {r'\alpha':'α',r'\beta':'β',r'\gamma':'γ',r'\delta':'δ',r'\epsilon':'ε',
        r'\eta':'η',r'\theta':'θ',r'\lambda':'λ',r'\mu':'μ',r'\nu':'ν',r'\pi':'π',
        r'\rho':'ρ',r'\sigma':'σ',r'\tau':'τ',r'\phi':'φ',r'\chi':'χ',r'\psi':'ψ',
        r'\omega':'ω',r'\Gamma':'Γ',r'\Delta':'Δ',r'\Sigma':'Σ',r'\Omega':'Ω'}
    for k,v in greek.items(): math = math.replace(k,v)
    sym = {r'\times':'×',r'\cdot':'·',r'\pm':'±',r'\leq':'≤',r'\geq':'≥',r'\neq':'≠',
        r'\approx':'≈',r'\propto':'∝',r'\infty':'∞',r'\partial':'∂',r'\sqrt':'√',
        r'\rightarrow':'→',r'\left(':'(',r'\right)':')',r'\,':' ',r'\;':' '}
    for k,v in sym.items(): math = math.replace(k,v)
    math = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}',r'(\1)/(\2)',math)
    math = re.sub(r'_\{([^}]+)\}',lambda m:to_sub(m.group(1)),math)
    math = re.sub(r'_([a-zA-Z0-9])',lambda m:to_sub(m.group(1)),math)
    math = re.sub(r'\^\{([^}]+)\}',lambda m:to_sup(m.group(1)),math)
    math = re.sub(r'\^([a-zA-Z0-9])',lambda m:to_sup(m.group(1)),math)
    math = re.sub(r'\\text\{([^}]+)\}',r'\1',math)
    math = re.sub(r'\\[a-zA-Z]+','',math)
    math = re.sub(r'[{}]','',math)
    return math.strip()

def proc_math(text):
    if not text: return ""
    text = re.sub(r'\\\[(.*?)\\\]',lambda m:' '+format_math(m.group(1))+' ',text,flags=re.DOTALL)
    text = re.sub(r'\\\((.+?)\\\)',lambda m:format_math(m.group(1)),text)
    return text

def create_styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle(name='T',parent=s['Title'],fontSize=22,spaceAfter=30,alignment=TA_CENTER,textColor=colors.HexColor('#1a365d')))
    s.add(ParagraphStyle(name='H1',parent=s['Heading1'],fontSize=16,spaceBefore=18,spaceAfter=10,textColor=colors.HexColor('#2c5282')))
    s.add(ParagraphStyle(name='H2',parent=s['Heading2'],fontSize=13,spaceBefore=14,spaceAfter=8,textColor=colors.HexColor('#2b6cb0')))
    s.add(ParagraphStyle(name='H3',parent=s['Heading3'],fontSize=11,spaceBefore=10,spaceAfter=6,textColor=colors.HexColor('#3182ce')))
    s.add(ParagraphStyle(name='B',parent=s['Normal'],fontSize=10,leading=14,alignment=TA_JUSTIFY,spaceBefore=3,spaceAfter=3))
    s.add(ParagraphStyle(name='F',parent=s['Normal'],fontSize=9,textColor=colors.HexColor('#4a5568'),backColor=colors.HexColor('#edf2f7'),borderWidth=1,borderColor=colors.HexColor('#cbd5e0'),borderPadding=6,spaceBefore=6,spaceAfter=6))
    return s

def clean(t):
    if not t: return ""
    t = t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    t = re.sub(r'\*\*([^*]+)\*\*',r'\1',t)
    t = re.sub(r'\*([^*]+)\*',r'\1',t)
    t = re.sub(r'`([^`]+)`',r'[\1]',t)
    return t

def parse_tbl(lines):
    rows = []
    for l in lines:
        if l.strip().startswith('|') and not re.match(r'^\|[\s\-:|]+\|$',l):
            rows.append([c.strip() for c in l.strip().split('|')[1:-1]])
    return rows

def mk_tbl(data,st):
    if not data: return None
    cl = [[Paragraph(proc_math(clean(c)),st['B']) for c in r] for r in data]
    nc = len(cl[0]) if cl else 1
    cw = (A4[0]-1.5*inch)/nc
    t = Table(cl,colWidths=[cw]*nc)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e2e8f0')),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#cbd5e0')),('FONTSIZE',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    return t

def proc_md(content,st):
    el = []
    lines = content.split('\n')
    i = 0
    tl = []
    in_t = False
    while i < len(lines):
        l = lines[i].rstrip()
        s = l.strip()
        if not s:
            if in_t and tl:
                t = mk_tbl(parse_tbl(tl),st)
                if t: el.append(t); el.append(Spacer(1,8))
                tl = []
                in_t = False
            i += 1
            continue
        if s.startswith('|'):
            in_t = True
            tl.append(s)
            i += 1
            continue
        elif in_t:
            t = mk_tbl(parse_tbl(tl),st)
            if t: el.append(t); el.append(Spacer(1,8))
            tl = []
            in_t = False
        if s.startswith('!['):
            m = re.match(r'!\[([^\]]*)\]\(',s)
            if m and m.group(1): el.append(Paragraph(f"[Figure: {clean(m.group(1))}]",st['F']))
            i += 1
            continue
        tx = proc_math(clean(s))
        if s.startswith('# ') and not s.startswith('## '): el.append(Paragraph(proc_math(clean(s[2:])),st['T']))
        elif s.startswith('## '): el.append(Spacer(1,8)); el.append(Paragraph(proc_math(clean(s[3:])),st['H1']))
        elif s.startswith('### '): el.append(Paragraph(proc_math(clean(s[4:])),st['H2']))
        elif s.startswith('#### '): el.append(Paragraph(proc_math(clean(s[5:])),st['H3']))
        elif s.startswith('---'): el.append(Spacer(1,6))
        elif s.startswith('- ') or s.startswith('* '): el.append(Paragraph(f"  • {proc_math(clean(s[2:]))}",st['B']))
        elif re.match(r'^\d+\.\s',s):
            n = re.match(r'^(\d+)\.',s).group(1)
            el.append(Paragraph(f"  {n}. {proc_math(clean(re.sub(r'^\\d+\\.\\s','',s)))}",st['B']))
        elif tx: el.append(Paragraph(tx,st['B']))
        i += 1
    return el

def add_pg(c,d):
    c.saveState()
    c.setFont('Helvetica',9)
    c.setFillColor(colors.HexColor('#718096'))
    c.drawCentredString(A4[0]/2,20*mm,f"Page {c.getPageNumber()}")
    c.restoreState()

def create_pdf():
    print("="*60)
    print("CREATING CLEAN PDF WITH MATH")
    print("="*60)
    with open(INPUT_MD,'r',encoding='utf-8') as f: content = f.read()
    print(f"Content: {len(content):,} chars")
    print("\nMath samples:")
    for s in [r"\(W_{c}\)",r"\(T_{01}\)",r"\(\pi_{c}\)",r"\(N D^3\)",r"\(V \propto N D^3\)"]:
        print(f"  {s} -> {proc_math(s)}")
    st = create_styles()
    print("\nProcessing...")
    el = proc_md(content,st)
    print(f"Elements: {len(el)}")
    doc = SimpleDocTemplate(OUTPUT_PDF,pagesize=A4,rightMargin=0.6*inch,leftMargin=0.6*inch,
        topMargin=0.6*inch,bottomMargin=0.6*inch)
    doc.build(el,onFirstPage=add_pg,onLaterPages=add_pg)
    print(f"\nOutput: {OUTPUT_PDF}")
    print(f"Size: {os.path.getsize(OUTPUT_PDF)/1024/1024:.2f} MB")

if __name__ == "__main__": create_pdf()
