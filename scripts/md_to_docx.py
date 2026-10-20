"""Markdown raporu .docx dosyasina cevirir (python-docx ile).

Desteklenenler: basliklar (#..####), boru-isaretli tablolar, madde ve numarali
listeler, kod bloklari, alinti bloklari, yatay cizgi, gomulu gorseller
(![acikama](yol)) ve satir ici **kalin** / `kod` bicimlendirmesi.

Kullanim:
    python scripts/md_to_docx.py docs/sinif_deney_raporu.md [cikti.docx]
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\*[^*]+\*)")
IMAGE = re.compile(r"^!\[(?P<alt>.*?)\]\((?P<src>[^)]+)\)\s*$")
MAX_IMG_WIDTH = Inches(6.0)
MAX_IMG_HEIGHT = Inches(3.4)


def add_runs(paragraph, text: str) -> None:
    """Satir ici **kalin**, `kod` ve *italik* bicimlerini isler."""
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            paragraph.add_run(part[2:-2]).bold = True
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(0xB0, 0x30, 0x60)
        elif (part.startswith("*") and part.endswith("*")
              and len(part) > 2 and not part.startswith("**")):
            paragraph.add_run(part[1:-1]).italic = True
        else:
            paragraph.add_run(part)


def is_table_sep(line: str) -> bool:
    body = line.strip().strip("|")
    return bool(body) and all(
        re.fullmatch(r"\s*:?-{2,}:?\s*", c) for c in body.split("|"))


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def add_table(doc: Document, rows: list[list[str]]) -> None:
    ncols = max(len(r) for r in rows)
    table = doc.add_table(rows=0, cols=ncols)
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for ri, row in enumerate(rows):
        cells = table.add_row().cells
        for ci in range(ncols):
            text = row[ci] if ci < len(row) else ""
            para = cells[ci].paragraphs[0]
            add_runs(para, text)
            for run in para.runs:
                run.font.size = Pt(9)
                if ri == 0:
                    run.bold = True
    doc.add_paragraph()


def add_image(doc: Document, src: Path, caption: str, base: Path) -> None:
    path = (base / src).resolve()
    if not path.exists():
        doc.add_paragraph(f"[Gorsel bulunamadi: {src}]")
        return
    # Genislik 6 inc; dik/kare gorseller sayfayi kaplamasin diye yukseklik sinirli
    from PIL import Image
    with Image.open(path) as im:
        aspect = im.height / im.width
    if MAX_IMG_WIDTH * aspect > MAX_IMG_HEIGHT:
        doc.add_picture(str(path), height=MAX_IMG_HEIGHT)
    else:
        doc.add_picture(str(path), width=MAX_IMG_WIDTH)
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    if caption:
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = cap.add_run(caption)
        run.italic = True
        run.font.size = Pt(9)


def convert(md_path: Path, out_path: Path) -> None:
    base = md_path.parent
    lines = md_path.read_text(encoding="utf-8").split("\n")

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Kod blogu
        if stripped.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            para = doc.add_paragraph()
            run = para.add_run("\n".join(buf))
            run.font.name = "Consolas"
            run.font.size = Pt(8.5)
            continue

        # Tablo
        if (stripped.startswith("|") and i + 1 < len(lines)
                and is_table_sep(lines[i + 1])):
            rows = [split_row(line)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            add_table(doc, rows)
            continue

        # Gorsel
        m = IMAGE.match(stripped)
        if m:
            add_image(doc, Path(m.group("src")), m.group("alt"), base)
            i += 1
            continue

        # Baslik
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            doc.add_heading(m.group(2).replace("**", ""), level=level)
            i += 1
            continue

        # Yatay cizgi
        if stripped in ("---", "***", "___"):
            i += 1
            continue

        # Alinti
        if stripped.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Inches(0.35)
            add_runs(para, " ".join(b for b in buf if b))
            for run in para.runs:
                run.font.size = Pt(9.5)
            continue

        # Madde listesi
        m = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m:
            para = doc.add_paragraph(style="List Bullet")
            add_runs(para, m.group(1))
            i += 1
            continue

        # Numarali liste
        m = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if m:
            para = doc.add_paragraph(style="List Number")
            add_runs(para, m.group(1))
            i += 1
            continue

        # Bos satir
        if not stripped:
            i += 1
            continue

        # Normal paragraf (ardisik satirlari birlestir)
        buf = []
        while i < len(lines):
            cur = lines[i].strip()
            if (not cur or cur.startswith(("#", "|", ">", "```", "---"))
                    or re.match(r"^\s*([-*]|\d+\.)\s+", lines[i])
                    or IMAGE.match(cur)):
                break
            buf.append(cur)
            i += 1
        text = " ".join(buf).replace("&nbsp;", " ")
        para = doc.add_paragraph()
        add_runs(para, text)

    doc.save(str(out_path))
    print(f"Yazildi: {out_path}")


def main() -> None:
    md = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else md.with_suffix(".docx")
    convert(md, out)


if __name__ == "__main__":
    main()
