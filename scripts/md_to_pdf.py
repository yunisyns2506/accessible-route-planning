"""Markdown raporu PDF'e cevirir (HTML + Edge'in basiksiz yazdirmasi).

Kullanim:
    python scripts/md_to_pdf.py docs/raporlar/hafta-04_raporu.md [cikti.pdf]

Gorsellerin alt metni sekil aciklamasi olarak altina yazilir. Word/LibreOffice
gerektirmez; Microsoft Edge (Chromium) `--headless --print-to-pdf` kullanilir.
"""
import html
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import markdown

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

CSS = """
@page { size: A4; margin: 18mm 17mm 18mm 17mm; }
body { font-family: Calibri, "Segoe UI", Arial, sans-serif; font-size: 10.5pt;
       line-height: 1.38; color: #111; }
h1 { font-size: 17pt; margin: 0 0 6px; color: #0d366b; }
h2 { font-size: 13pt; margin: 16px 0 6px; color: #0d366b;
     border-bottom: 1px solid #cde2fb; padding-bottom: 2px; page-break-after: avoid; }
h3 { font-size: 11.5pt; margin: 12px 0 4px; color: #184f95; page-break-after: avoid; }
p { margin: 4px 0 6px; }
ul, ol { margin: 4px 0 6px; padding-left: 20px; }
li { margin: 2px 0; }
hr { border: 0; border-top: 1px solid #ddd; margin: 10px 0; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 8px; font-size: 9pt; }
tr { page-break-inside: avoid; }
thead { display: table-header-group; }
th { background: #2a78d6; color: #fff; font-weight: 600; }
th, td { border: 1px solid #b9c9de; padding: 3px 6px; vertical-align: top; }
tr:nth-child(even) td { background: #f1f6fd; }
code { font-family: Consolas, monospace; font-size: 8.8pt; background: #f2f2f0;
       padding: 0 2px; }
pre { background: #f6f6f4; border: 1px solid #e2e2df; padding: 6px 8px; font-size: 8.3pt;
      white-space: pre; overflow: hidden; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
blockquote { margin: 6px 0; padding: 4px 10px; border-left: 3px solid #86b6ef;
             background: #f5f9fe; color: #333; }
figure { margin: 8px 0 10px; text-align: center; page-break-inside: avoid; }
figure img { max-width: 100%; max-height: 92mm; }
figcaption { font-size: 8.8pt; color: #444; margin-top: 3px; text-align: left; }
"""


def main() -> int:
    src = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else src.with_suffix(".pdf")
    text = src.read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=["tables", "fenced_code"])

    def figure(m: re.Match) -> str:
        alt, path = html.unescape(m.group("alt")), m.group("src")
        uri = (src.parent / path).resolve().as_uri()
        return (f'<figure><img src="{uri}" alt=""><figcaption>{html.escape(alt)}'
                f"</figcaption></figure>")

    body = re.sub(r'<p>\s*<img alt="(?P<alt>[^"]*)" src="(?P<src>[^"]+)"\s*/?>\s*</p>', figure, body)
    doc = (f'<!doctype html><html lang="tr"><head><meta charset="utf-8">'
           f"<style>{CSS}</style></head><body>{body}</body></html>")
    # Edge, PDF'i once gecici klasore yazar (OneDrive klasorune dogrudan
    # yazamayabiliyor); sonra hedefe kopyalanir.
    tmp = Path(tempfile.mkdtemp(prefix="md2pdf_"))
    page, pdf = tmp / "rapor.html", tmp / "rapor.pdf"
    page.write_text(doc, encoding="utf-8")
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--user-data-dir={tmp / 'profil'}", f"--print-to-pdf={pdf}",
                    page.as_uri()], check=True, capture_output=True, timeout=180)
    # Edge baslaticisi PDF yazilmadan once donebiliyor; dosya oturana kadar bekle
    last = -1
    for _ in range(240):
        size = pdf.stat().st_size if pdf.exists() else -1
        if size > 0 and size == last:
            break
        last = size
        time.sleep(1)
    shutil.copy2(pdf, out)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"Yazildi: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
