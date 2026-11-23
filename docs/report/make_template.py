"""Build the Pandoc reference document used for the CrawlMesh report.

Output: docs/report/template.docx
Format contract: A4, margins 4/3/3/3 cm, Times New Roman 11 pt, 1.5 line
spacing, justified body text.
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

OUT = Path(__file__).with_name("template.docx")
FONT = "Times New Roman"


def set_run_font(style, size: float, bold: bool | None = None, italic: bool | None = None) -> None:
    style.font.name = FONT
    style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    if italic is not None:
        style.font.italic = italic
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), FONT)


def set_para(style, *, align=None, before=0, after=6, spacing=1.5, keep_next=False) -> None:
    pf = style.paragraph_format
    if align is not None:
        pf.alignment = align
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = spacing
    pf.keep_with_next = keep_next


def main() -> None:
    doc = Document()

    # A4 with the academic margin contract.
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(3.0)
    section.bottom_margin = Cm(3.0)
    section.left_margin = Cm(4.0)
    section.right_margin = Cm(3.0)
    section.header_distance = Cm(1.5)
    section.footer_distance = Cm(1.5)

    styles = doc.styles

    normal = styles["Normal"]
    set_run_font(normal, 11)
    set_para(normal, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=6, spacing=1.5)

    title = styles["Title"]
    set_run_font(title, 18, bold=True)
    set_para(title, align=WD_ALIGN_PARAGRAPH.CENTER, after=12, spacing=1.15)

    subtitle = styles["Subtitle"]
    set_run_font(subtitle, 13, bold=False, italic=True)
    set_para(subtitle, align=WD_ALIGN_PARAGRAPH.CENTER, after=18, spacing=1.15)

    for name, size, before, after in (
        ("Heading 1", 14, 14, 8),
        ("Heading 2", 12, 12, 6),
        ("Heading 3", 11, 10, 4),
        ("Heading 4", 11, 8, 3),
    ):
        style = styles[name]
        set_run_font(style, size, bold=True)
        set_para(
            style,
            align=WD_ALIGN_PARAGRAPH.LEFT,
            before=before,
            after=after,
            spacing=1.15,
            keep_next=True,
        )
        # Word built-in headings are blue by default; force black.
        style.font.color.rgb = None

    caption = styles["Caption"]
    set_run_font(caption, 10, bold=False, italic=False)
    set_para(caption, align=WD_ALIGN_PARAGRAPH.CENTER, after=8, spacing=1.0)

    for name in ("Body Text", "First Paragraph", "Compact"):
        if name in styles:
            style = styles[name]
            set_run_font(style, 11)
            set_para(style, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=6, spacing=1.5)

    for name in ("Table", "Table Grid"):
        if name in styles:
            style = styles[name]
            set_run_font(style, 9.5)
            set_para(style, align=WD_ALIGN_PARAGRAPH.LEFT, after=0, spacing=1.0)

    # Pandoc uses "Source Code" for fenced code; keep it readable and small.
    if "Source Code" in styles:
        code = styles["Source Code"]
        code.font.name = "Consolas"
        code.font.size = Pt(9)
        set_para(code, after=0, spacing=1.0)

    doc.save(OUT)
    print(f"template saved: {OUT}")


if __name__ == "__main__":
    main()
