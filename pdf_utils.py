import re
import requests
import warnings
import sys
from io import StringIO
from pathlib import Path
from fpdf import FPDF
from datetime import datetime

warnings.filterwarnings('ignore')

class WarningFilter(StringIO):
    def write(self, s):
        if 'DeprecationWarning' not in s and 'RuntimeWarning' not in s:
            super().write(s)

_old_stderr = sys.stderr
sys.stderr = StringIO()

PDF_DIR = "pdf"
MARGIN_LEFT = 15
PAGE_WIDTH = 210
PAGE_HEIGHT = 297
CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT * 2  # 180mm


# ─────────────────────────────────────────────
# Unicode sanitization helper
# ─────────────────────────────────────────────

def _clean_unicode_for_latin1(value) -> str:
    # Safely convert unicode characters to latin-1 equivalents for standard PDF fonts.
    if isinstance(value, list):
        value = ", ".join(str(x) for x in value)
    if value is None:
        return ""
    text = str(value)
    replacements = {
        '\u2018': "'", '\u2019': "'",  # Smart single quotes
        '\u201c': '"', '\u201d': '"',  # Smart double quotes
        '\u2013': '-', '\u2014': '-',  # En/Em dashes
        '\u2212': '-',                 # Minus sign
        '\u00a0': ' ',                 # Non-breaking space
        '\u2026': '...',               # Ellipsis
    }
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)
    return text.encode('latin-1', 'replace').decode('latin-1')


def sanitize(nom: str) -> str:
    # Remove characters unsafe for filenames.
    return re.sub(r'[^a-zA-Z0-9_-]', '', nom.strip().replace(" ", "_"))


# ─────────────────────────────────────────────
# PDF generation (livret / mémoire format)
# ─────────────────────────────────────────────

def init_pdf_dossier():
    Path(PDF_DIR).mkdir(exist_ok=True)


class AcademicPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 9)
            self.set_text_color(100, 100, 100)
            self.cell(0, 8, 'Visual Search Engine -- Academic Analysis Report', 0, 0, 'L')
            self.set_draw_color(200, 200, 200)
            self.set_line_width(0.2)
            self.line(MARGIN_LEFT, 20, PAGE_WIDTH - MARGIN_LEFT, 20)
            self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(100, 100, 100)
        self.set_draw_color(220, 220, 220)
        self.set_line_width(0.2)
        self.line(MARGIN_LEFT, PAGE_HEIGHT - 17, PAGE_WIDTH - MARGIN_LEFT, PAGE_HEIGHT - 17)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')


def _ensure_h_space(pdf, needed=5):
    # Move to next line if not enough horizontal space.
    if pdf.get_x() + needed > PAGE_WIDTH - MARGIN_LEFT:
        pdf.ln(pdf.font_size_pt * 1.5)
        pdf.set_x(MARGIN_LEFT)


def _render_link_block(pdf, title, items, url_fn, label_fn):
    # Render a titled block of links into the PDF.
    pdf.set_x(MARGIN_LEFT)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(26, 33, 62)
    pdf.cell(CONTENT_WIDTH, 7, _clean_unicode_for_latin1(title), 0, 1, 'L')
    pdf.ln(1)
    pdf.set_text_color(0, 0, 0)
    for i, r in enumerate(items[:8], 1):
        url = url_fn(r) or ''
        label = label_fn(r)
        label = _clean_unicode_for_latin1(label)
        _ensure_h_space(pdf, 12)
        pdf.set_x(MARGIN_LEFT)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(CONTENT_WIDTH, 5, f"[{i}] {label}", 0, 1, 'L')
        if url:
            _ensure_h_space(pdf, 8)
            pdf.set_x(MARGIN_LEFT)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(0, 152, 219)
            short = (url[:75] + '...') if len(url) > 75 else url
            pdf.cell(CONTENT_WIDTH, 5, short, link=url)
            pdf.set_text_color(0, 0, 0)
        pdf.ln(3)


def _section_title(pdf, num, title):
    # Render a section title with number and an accent line.
    pdf.set_x(MARGIN_LEFT)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(26, 33, 62)  # Dark Navy
    heading_text = f"{num}. {title}" if num else title
    pdf.cell(CONTENT_WIDTH, 9, _clean_unicode_for_latin1(heading_text), 0, 1, 'L')
    
    # Underline accent bar
    pdf.set_draw_color(0, 201, 167)  # Teal
    pdf.set_line_width(0.6)
    pdf.line(MARGIN_LEFT, pdf.get_y(), PAGE_WIDTH - MARGIN_LEFT, pdf.get_y())
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)


def _subsection_title(pdf, title):
    # Render a subsection title.
    pdf.set_x(MARGIN_LEFT)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(26, 33, 62)
    pdf.cell(CONTENT_WIDTH, 7, _clean_unicode_for_latin1(title), 0, 1, 'L')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)


def generer_pdf_discussion(
    analyse: dict,
    image_path: str,
    resultats_web: list,
    resultats_images: list,
    resultats_videos: list,
):
    # Generate an academic-style PDF booklet from the analysis and search results.
    # Structure:
    # - Cover page with colored top banner
    # - Table of Contents
    # - Introduction
    # - Detailed Characteristics (Formatted as Table)
    # - Description and Development
    # - Illustrations (downloaded images)
    # - Educational Section (Q&A)
    # - Conclusion
    # - Bibliography
    init_pdf_dossier()

    nom = analyse.get("nom_exact") or analyse.get("objet_principal", "Unknown")
    nom_propre = nom.strip().replace(" ", "_").replace("/", "-")
    file_path = f"{PDF_DIR}/{nom_propre}.pdf"

    pdf = AcademicPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ── Cover page ─────────────────────────────
    pdf.add_page()
    
    # Draw dark blue top banner
    pdf.set_fill_color(26, 33, 62)
    pdf.rect(0, 0, PAGE_WIDTH, 75, 'F')
    
    pdf.set_y(22)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(CONTENT_WIDTH, 8, "VISUAL ANALYSIS & WEB RESEARCH REPORT", 0, 1, 'C')
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "B", 26)
    pdf.cell(CONTENT_WIDTH, 12, _clean_unicode_for_latin1(nom).upper(), 0, 1, 'C')
    
    pdf.ln(4)
    pdf.set_text_color(0, 201, 167)  # Teal accent
    pdf.set_font("Helvetica", "B", 11)
    theme_label = analyse.get('discussion_theme', nom) or nom
    pdf.cell(CONTENT_WIDTH, 8, f"THEME: {_clean_unicode_for_latin1(theme_label).upper()}", 0, 1, 'C')
    
    # Reset text color
    pdf.set_text_color(0, 0, 0)
    pdf.ln(25)

    if Path(image_path).exists():
        img_w = 95
        x_pos = (PAGE_WIDTH - img_w) / 2
        pdf.image(image_path, x=x_pos, w=img_w)
        pdf.ln(25)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(CONTENT_WIDTH, 6, f"Generated on: {datetime.now().strftime('%d %B %Y -- %H:%M')}", 0, 1, 'C')

    # ── Table of Contents ──────────────────────
    pdf.add_page()
    _section_title(pdf, "", "Table of Contents")
    toc_items = [
        "1. Documentary Synopsis",
        "2. Detailed Characteristics",
        "3. Documentaire",
        "4. Illustrations",
        "5. Documentary Trivia & Facts",
        "6. Conclusion",
        "7. Bibliography & References",
    ]
    for item in toc_items:
        pdf.set_x(MARGIN_LEFT)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(CONTENT_WIDTH, 7, item, 0, 1, 'L')
    pdf.ln(4)

    # ── 1. Introduction ─────────────────────────
    pdf.add_page()
    _section_title(pdf, "1", "Documentary Synopsis")
    pdf.set_x(MARGIN_LEFT)
    pdf.set_font("Helvetica", "I", 12)
    pdf.set_text_color(50, 50, 50)
    intro_txt = analyse.get("introduction", analyse.get("description", ""))
    pdf.multi_cell(CONTENT_WIDTH, 8, _clean_unicode_for_latin1(intro_txt))
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    # ── 2. Detailed Characteristics (Table) ─────
    _section_title(pdf, "2", "Detailed Characteristics")
    pdf.ln(2)

    # Set up table header
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(26, 33, 62)
    pdf.set_text_color(255, 255, 255)
    pdf.set_draw_color(200, 200, 200)
    pdf.cell(55, 8, "Characteristic", 1, 0, 'L', True)
    pdf.cell(CONTENT_WIDTH - 55, 8, "Value", 1, 1, 'L', True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)

    # Collect data rows
    charac_rows = [
        ("Object Principal", analyse.get("objet_principal", "--")),
        ("Exact Name", analyse.get("nom_exact", "--")),
        ("Category", analyse.get("categorie", "--")),
        ("Dominant Colors", ", ".join(analyse.get("couleurs_dominantes", []))),
        ("Visual Style", analyse.get("style", "--")),
        ("Attributes", ", ".join(analyse.get("attributs", []))),
    ]

    caracs = analyse.get("caracteristiques_detaillees", {})
    if caracs:
        for k, v in caracs.items():
            if v:
                label = k.replace("_", " ").title()
                charac_rows.append((label, v))

    # Draw table rows
    fill = False
    for label, val in charac_rows:
        if fill:
            pdf.set_fill_color(242, 245, 248)  # soft gray/blue tint
        else:
            pdf.set_fill_color(255, 255, 255)

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(55, 8, _clean_unicode_for_latin1(label), 1, 0, 'L', True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(CONTENT_WIDTH - 55, 8, _clean_unicode_for_latin1(val), 1, 1, 'L', True)
        fill = not fill

    pdf.ln(6)

    # ── 3. Documentaire ──────────
    pdf.add_page()
    _section_title(pdf, "3", "Documentaire")
    pdf.set_x(MARGIN_LEFT)
    pdf.set_font("Helvetica", "", 11)
    dev_txt = analyse.get("developpement", analyse.get("description", ""))
    pdf.multi_cell(CONTENT_WIDTH, 7, _clean_unicode_for_latin1(dev_txt))
    pdf.ln(6)

    # ── 4. Illustrations ────────────────────────
    _section_title(pdf, "4", "Illustrations")
    pdf.ln(2)

    img_dir = Path(PDF_DIR) / "images"
    img_dir.mkdir(exist_ok=True)

    for i, r in enumerate(resultats_images[:5], 1):
        url = (r.get('url') or r.get('href') or '').strip()
        titre = r.get('titre') or r.get('title') or f"Illustration {i}"
        titre = _clean_unicode_for_latin1(titre)
        chemin = r.get('chemin', '') or ''

        if chemin and Path(chemin).exists():
            pdf.set_x(MARGIN_LEFT)
            pdf.set_font("Helvetica", "I", 10)
            pdf.cell(CONTENT_WIDTH, 5, f"Figure {i}: {titre}", 0, 1, 'L')
            max_w = 95
            try:
                from PIL import Image as PILImage
                with PILImage.open(chemin) as pil_img:
                    pil_img.load()
                    ratio = pil_img.height / pil_img.width
                    h = max_w * ratio
                pdf.image(str(chemin), x=(PAGE_WIDTH - max_w) / 2, w=max_w, h=h)
                pdf.ln(3)
            except Exception:
                pdf.set_x(MARGIN_LEFT)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(0, 152, 219)
                pdf.cell(CONTENT_WIDTH, 5, url or chemin, link=url or chemin)
                pdf.set_text_color(0, 0, 0)
                pdf.ln(4)
        elif url:
            pdf.set_x(MARGIN_LEFT)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(CONTENT_WIDTH, 6, f"[{i}] {titre}", 0, 1, 'L')
            pdf.set_x(MARGIN_LEFT)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(0, 152, 219)
            short_url = (url[:80] + '...') if len(url) > 80 else url
            pdf.cell(CONTENT_WIDTH, 5, short_url, link=url)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(4)

    # ── 5. Documentary Trivia & Facts ──────────────────
    pdf.add_page()
    _section_title(pdf, "5", "Documentary Trivia & Facts")
    pdf.ln(2)
    pdf.set_x(MARGIN_LEFT)
    pdf.set_font("Helvetica", "", 11)

    qcm = analyse.get("partie_educative", [])
    if qcm:
        for bloc in qcm:
            pdf.multi_cell(CONTENT_WIDTH, 7, _clean_unicode_for_latin1(bloc))
            pdf.ln(3)
            pdf.set_x(MARGIN_LEFT)
    else:
        pdf.multi_cell(CONTENT_WIDTH, 7, "No educational content generated for this analysis.")
    pdf.ln(4)

    # ── 6. Conclusion ───────────────────────────
    pdf.add_page()
    _section_title(pdf, "6", "Conclusion")
    pdf.set_x(MARGIN_LEFT)
    pdf.set_font("Helvetica", "", 11)
    conclusion = analyse.get("conclusion", "This analysis provides a comprehensive overview of the subject presented in the image.")
    pdf.multi_cell(CONTENT_WIDTH, 7, _clean_unicode_for_latin1(conclusion))
    pdf.ln(6)

    # ── 7. Bibliography ─────────────────────────
    _section_title(pdf, "7", "Bibliography & References")
    pdf.ln(2)

    if not resultats_web and not resultats_images and not resultats_videos:
        pdf.set_x(MARGIN_LEFT)
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(CONTENT_WIDTH, 6, "No references available for this analysis.", 0, 1, 'L')
    else:
        if resultats_web:
            _render_link_block(pdf, "Web Articles", resultats_web, lambda r: r.get('href', ''), lambda r: r.get('title', 'Untitled'))
        if resultats_images:
            _render_link_block(pdf, "Image Sources", resultats_images, lambda r: r.get('url', ''), lambda r: r.get('titre', 'Image'))
        if resultats_videos:
            _render_link_block(pdf, "Video Sources", resultats_videos, lambda r: r.get('url', ''), lambda r: r.get('titre', 'Video'))

    pdf.set_x(MARGIN_LEFT)
    pdf.output(file_path)
    print(f"\n[PDF] Booklet generated successfully: {file_path}")
    return file_path
