"""Build the CrawlMesh report DOCX from Markdown + LaTeX.

Pipeline:
  report.md --pandoc--> DOCX (native OMML equations)
  python-docx post-processing: cover, TOC field, page numbers, captions,
  table styling, equation centering, and heading/page-break rules.

Run:
  .\\.venv\\Scripts\\python.exe docs\\report\\build_report.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pypandoc
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
SOURCE = BASE / "report.md"
REFERENCE = BASE / "template.docx"
RAW = BASE / "report_raw.docx"
OUT = BASE / "Laporan_Proyek_CrawlMesh_Draft.docx"
ROOT_OUT = ROOT / "Laporan_Proyek_CrawlMesh_Draft.docx"
FONT = "Times New Roman"


def set_font(run, size: float, bold: bool | None = None, italic: bool | None = None) -> None:
    run.font.name = FONT
    run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    run.font.color.rgb = RGBColor(0, 0, 0)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), FONT)
    for tag in ("w:sz", "w:szCs"):
        for old in rpr.findall(qn(tag)):
            rpr.remove(old)
        node = OxmlElement(tag)
        node.set(qn("w:val"), str(int(round(size * 2))))
        rpr.append(node)


def style_paragraph(paragraph, size: float, *, align=None, before=0, after=6, spacing=1.5,
                    bold=None, italic=None, keep_next=False) -> None:
    if align is not None:
        paragraph.alignment = align
    pf = paragraph.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = spacing
    pf.keep_with_next = keep_next
    for run in paragraph.runs:
        set_font(run, size, bold=bold, italic=italic)


def set_style_font(style, size: float, bold: bool | None = None) -> None:
    style.font.name = FONT
    style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), FONT)
    for tag in ("w:sz", "w:szCs"):
        for old in rpr.findall(qn(tag)):
            rpr.remove(old)
        node = OxmlElement(tag)
        node.set(qn("w:val"), str(int(round(size * 2))))
        rpr.append(node)


def ensure_base_styles(doc: Document) -> None:
    for name in ("Normal", "Body Text", "First Paragraph", "Compact"):
        if name not in doc.styles:
            continue
        style = doc.styles[name]
        set_style_font(style, 11)
        style.paragraph_format.line_spacing = 1.5
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for name, size in (("Heading 1", 14), ("Heading 2", 12), ("Heading 3", 11)):
        if name in doc.styles:
            set_style_font(doc.styles[name], size, bold=True)


def add_field(paragraph, instruction: str, placeholder: str = "") -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = placeholder
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(separate)
    run._r.append(text)
    run._r.append(end)


def set_update_fields(doc: Document) -> None:
    settings = doc.settings.element
    for old in settings.findall(qn("w:updateFields")):
        settings.remove(old)
    update = OxmlElement("w:updateFields")
    update.set(qn("w:val"), "true")
    settings.append(update)


def shade_cell(cell, hex_color: str = "D9E2F3") -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    for old in tc_pr.findall(qn("w:shd")):
        tc_pr.remove(old)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def set_cell_margins(table, top=35, start=45, bottom=35, end=45) -> None:
    tbl_pr = table._tbl.tblPr
    for old in tbl_pr.findall(qn("w:tblCellMar")):
        tbl_pr.remove(old)
    mar = OxmlElement("w:tblCellMar")
    for tag, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = OxmlElement(f"w:{tag}")
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")
        mar.append(node)
    tbl_pr.append(mar)


def set_table_width(table) -> None:
    tbl_pr = table._tbl.tblPr
    for tag in ("w:tblW", "w:tblLayout"):
        for old in tbl_pr.findall(qn(tag)):
            tbl_pr.remove(old)
    width = OxmlElement("w:tblW")
    width.set(qn("w:type"), "pct")
    width.set(qn("w:w"), "5000")
    tbl_pr.append(width)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tbl_pr.append(layout)


def table_widths(table) -> list[float] | None:
    headers = [cell.text.strip() for cell in table.rows[0].cells]
    n = len(headers)
    if n == 2:
        return [6.0, 8.0]
    if n == 3:
        if headers[0] == "Simbol":
            return [3.0, 5.0, 6.0]
        if headers[0] == "Fitur":
            return [3.8, 2.2, 8.0]
        if headers[0] == "Jenis variabel":
            return [2.5, 3.5, 8.0]
        return [4.0, 4.0, 6.0]
    if n == 4:
        if headers[0] == "ID":
            return [1.4, 4.2, 4.4, 4.0]
        if headers[0] == "Requirement":
            return [2.5, 3.8, 2.9, 4.8]
        if headers[0] == "No.":
            return [1.2, 4.5, 4.5, 3.8]
        return [3.5, 3.5, 3.5, 3.5]
    if n == 5:
        return [3.0, 2.8, 3.0, 2.8, 2.4]
    if n == 6:
        return [1.6, 2.0, 2.3, 2.8, 2.3, 2.8]
    if n == 7:
        if headers[0] == "Node":
            return [1.9, 1.3, 2.0, 2.8, 1.7, 1.7, 2.5]
        if headers[0] == "Worker":
            return [1.3, 2.1, 2.1, 2.1, 2.1, 2.1, 2.1]
        if headers[0] == "Jumlah proses":
            return [1.4, 2.1, 2.1, 2.1, 2.1, 2.1, 2.1]
        return [2.0] * 7
    return None


def apply_column_widths(table) -> None:
    widths = table_widths(table)
    if not widths:
        return
    for index, width in enumerate(widths):
        table.columns[index].width = Cm(width)
    for row in table.rows:
        for index, cell in enumerate(row.cells):
            if index < len(widths):
                cell.width = Cm(widths[index])


def prevent_row_split(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    for old in tr_pr.findall(qn("w:cantSplit")):
        tr_pr.remove(old)
    cant = OxmlElement("w:cantSplit")
    tr_pr.append(cant)


def repeat_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    for old in tr_pr.findall(qn("w:tblHeader")):
        tr_pr.remove(old)
    header = OxmlElement("w:tblHeader")
    tr_pr.append(header)


def format_tables(doc: Document) -> None:
    for table in doc.tables:
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        set_table_width(table)
        set_cell_margins(table)
        apply_column_widths(table)
        columns = len(table.columns)
        font_size = 7.5 if columns >= 7 else (8.5 if columns in (4, 6) else 9)
        for row_index, row in enumerate(table.rows):
            prevent_row_split(row)
            if row_index == 0:
                repeat_header(row)
            for cell in row.cells:
                if row_index == 0:
                    shade_cell(cell)
                for paragraph in cell.paragraphs:
                    style_paragraph(
                        paragraph,
                        font_size,
                        align=WD_ALIGN_PARAGRAPH.LEFT,
                        before=1,
                        after=1,
                        spacing=1.0,
                        bold=True if row_index == 0 else None,
                    )
                    for run in paragraph.runs:
                        run.font.size = Pt(font_size)
        # Keep short tables on one page; long tables may split with a repeated header.
        if len(table.rows) <= 12:
            for row in table.rows[:-1]:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        paragraph.paragraph_format.keep_with_next = True


def move_table_captions(doc: Document) -> None:
    body = doc.element.body
    for table in doc.tables:
        node = table._tbl
        candidate = node.getnext()
        # Skip whitespace paragraphs before the caption.
        while candidate is not None and candidate.tag == qn("w:p"):
            text = "".join(candidate.itertext()).strip()
            if text:
                break
            candidate = candidate.getnext()
        if candidate is None or candidate.tag != qn("w:p"):
            continue
        text = "".join(candidate.itertext()).strip()
        if not text.startswith("Tabel "):
            continue
        node.addprevious(candidate)


def format_captions(doc: Document) -> None:
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        if text.startswith("Tabel ") or text.startswith("Gambar "):
            paragraph.style = doc.styles["Caption"]
            style_paragraph(
                paragraph,
                10,
                align=WD_ALIGN_PARAGRAPH.CENTER,
                before=4,
                after=4,
                spacing=1.0,
                bold=False,
                italic=False,
            )
            paragraph.paragraph_format.keep_with_next = True
            # Add a short source line once, immediately after figure captions.
            if text.startswith("Gambar "):
                next_text = ""
                next_node = paragraph._p.getnext()
                if next_node is not None:
                    next_text = "".join(next_node.itertext()).strip()
                if next_text.startswith("Sumber:"):
                    continue
                source = (
                    "Sumber: Diolah dari implementasi CrawlMesh."
                    if text.startswith("Gambar 3.")
                    else "Sumber: Dokumentasi proyek CrawlMesh."
                )
                source_paragraph = paragraph.insert_paragraph_before()
                # insert after, not before
                source_paragraph._p.getparent().remove(source_paragraph._p)
                new_p = OxmlElement("w:p")
                paragraph._p.addnext(new_p)
                from docx.text.paragraph import Paragraph

                source_paragraph = Paragraph(new_p, paragraph._parent)
                source_paragraph.style = doc.styles["Caption"]
                run = source_paragraph.add_run(source)
                set_font(run, 9, italic=True)
                source_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                source_paragraph.paragraph_format.space_before = Pt(0)
                source_paragraph.paragraph_format.space_after = Pt(6)
                source_paragraph.paragraph_format.line_spacing = 1.0


def keep_figures_with_captions(doc: Document) -> None:
    for paragraph in doc.paragraphs:
        if paragraph._p.xpath(".//w:drawing"):
            paragraph.paragraph_format.keep_with_next = True
            paragraph.paragraph_format.keep_together = True


def center_equations(doc: Document) -> None:
    for paragraph in doc.paragraphs:
        xml = paragraph._p.xml
        if "<m:oMathPara" in xml:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.space_before = Pt(6)
            paragraph.paragraph_format.space_after = Pt(6)
            paragraph.paragraph_format.line_spacing = 1.15
            paragraph.paragraph_format.keep_together = True


def format_headings(doc: Document) -> None:
    for paragraph in doc.paragraphs:
        style_name = paragraph.style.name if paragraph.style is not None else ""
        if style_name == "Heading 1":
            style_paragraph(
                paragraph,
                14,
                align=WD_ALIGN_PARAGRAPH.LEFT,
                before=16,
                after=8,
                spacing=1.15,
                bold=True,
                keep_next=True,
            )
        elif style_name == "Heading 2":
            style_paragraph(
                paragraph,
                12,
                align=WD_ALIGN_PARAGRAPH.LEFT,
                before=12,
                after=6,
                spacing=1.15,
                bold=True,
                keep_next=True,
            )
        elif style_name == "Heading 3":
            style_paragraph(
                paragraph,
                11,
                align=WD_ALIGN_PARAGRAPH.LEFT,
                before=10,
                after=4,
                spacing=1.15,
                bold=True,
                keep_next=True,
            )


def format_body(doc: Document) -> None:
    for paragraph in doc.paragraphs:
        if "TOC \\o" in paragraph._p.xml or paragraph.text.strip() == "DAFTAR ISI":
            continue
        if paragraph.style is not None and paragraph.style.name in (
            "Normal",
            "Body Text",
            "First Paragraph",
            "Compact",
        ):
            paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            paragraph.paragraph_format.line_spacing = 1.5
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(6)
            for run in paragraph.runs:
                set_font(run, 11)


def format_code_blocks(doc: Document) -> None:
    for paragraph in doc.paragraphs:
        if paragraph.style is None or paragraph.style.name != "Source Code":
            continue
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        paragraph.paragraph_format.line_spacing = 1.0
        paragraph.paragraph_format.space_before = Pt(3)
        paragraph.paragraph_format.space_after = Pt(6)
        ppr = paragraph._p.get_or_add_pPr()
        for old in ppr.findall(qn("w:wordWrap")):
            ppr.remove(old)
        word_wrap = OxmlElement("w:wordWrap")
        word_wrap.set(qn("w:val"), "1")
        ppr.append(word_wrap)
        for run in paragraph.runs:
            run.font.name = "Consolas"
            run.font.size = Pt(8.5)
            run.font.color.rgb = RGBColor(0, 0, 0)


def add_page_numbers(doc: Document) -> None:
    section = doc.sections[0]
    section.different_first_page_header_footer = True
    footer = section.footer
    footer.is_linked_to_previous = False
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_field(paragraph, " PAGE ", "1")
    for run in paragraph.runs:
        set_font(run, 10)
    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = hp.add_run("Laporan Proyek CrawlMesh")
    set_font(run, 9, italic=True)


def add_toc(doc: Document) -> None:
    marker = None
    for paragraph in doc.paragraphs:
        if paragraph.text.strip() == "[[TOC]]":
            marker = paragraph
            break
    if marker is None:
        return
    marker.text = ""
    marker.style = doc.styles["Normal"]
    marker.alignment = WD_ALIGN_PARAGRAPH.LEFT
    marker.paragraph_format.page_break_before = True
    marker.paragraph_format.space_before = Pt(0)
    marker.paragraph_format.space_after = Pt(8)
    run = marker.add_run("DAFTAR ISI")
    set_font(run, 14, bold=True)
    toc_paragraph = OxmlElement("w:p")
    marker._p.addnext(toc_paragraph)
    from docx.text.paragraph import Paragraph

    toc = Paragraph(toc_paragraph, marker._parent)
    toc.alignment = WD_ALIGN_PARAGRAPH.LEFT
    add_field(toc, 'TOC \\o "1-3" \\h \\z \\u', "Klik kanan lalu pilih Update Field untuk memuat daftar isi.")
    for run in toc.runs:
        set_font(run, 11)


def add_page_breaks(doc: Document) -> None:
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if paragraph.style is not None and paragraph.style.name == "Heading 1":
            if text.startswith("BAB ") or text.startswith("DAFTAR REFERENSI") or text.startswith("LAMPIRAN "):
                paragraph.paragraph_format.page_break_before = True


def center_cover(doc: Document) -> None:
    in_cover = True
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text == "DAFTAR ISI":
            in_cover = False
            break
        if not text:
            continue
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if paragraph.style is not None and paragraph.style.name == "Title":
            for run in paragraph.runs:
                set_font(run, 20, bold=True)
        elif paragraph.style is not None and paragraph.style.name == "Subtitle":
            for run in paragraph.runs:
                set_font(run, 13, italic=True)
        else:
            for run in paragraph.runs:
                set_font(run, 11)
            paragraph.paragraph_format.line_spacing = 1.3
            paragraph.paragraph_format.space_after = Pt(4)


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"source tidak ada: {SOURCE}")
    pypandoc.convert_file(
        str(SOURCE),
        "docx",
        outputfile=str(RAW),
        extra_args=[
            f"--reference-doc={REFERENCE}",
            f"--resource-path={BASE}",
            "--from=markdown+raw_tex+pipe_tables+fenced_divs+tex_math_dollars",
        ],
    )
    doc = Document(str(RAW))
    ensure_base_styles(doc)
    add_toc(doc)
    add_page_breaks(doc)
    format_tables(doc)
    move_table_captions(doc)
    format_captions(doc)
    format_headings(doc)
    format_body(doc)
    format_code_blocks(doc)
    keep_figures_with_captions(doc)
    center_equations(doc)
    center_cover(doc)
    add_page_numbers(doc)
    set_update_fields(doc)
    doc.core_properties.title = "Laporan Proyek CrawlMesh"
    doc.core_properties.subject = "Distributed Web Crawler dengan Orkestrasi Master–Worker"
    doc.core_properties.author = "CrawlMesh"
    doc.save(str(OUT))
    shutil.copyfile(OUT, ROOT_OUT)
    print(f"built {OUT}")
    print(f"copied {ROOT_OUT}")


if __name__ == "__main__":
    main()
