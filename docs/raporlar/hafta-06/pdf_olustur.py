"""Hafta 6 raporunu PDF'e çevirir: kapak.html + rapor.html -> Edge ile yazdırılır, pypdf ile birleştirilir.
Kullanım: python pdf_olustur.py   (çıktı: ../hafta-06_raporu.pdf)"""
import subprocess
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
K = Path(__file__).resolve().parent
CIKTI = K.parent / "hafta-06_raporu.pdf"


def yazdir(html: Path, pdf: Path) -> None:
    with tempfile.TemporaryDirectory() as prof:
        subprocess.run([EDGE, "--headless", "--disable-gpu", f"--user-data-dir={prof}",
                        "--no-pdf-header-footer", "--print-to-pdf-no-header",
                        "--virtual-time-budget=8000", f"--print-to-pdf={pdf}", html.as_uri()],
                       check=True, capture_output=True, timeout=180)


with tempfile.TemporaryDirectory() as t:
    t = Path(t)
    yazdir(K / "kapak.html", t / "kapak.pdf")
    yazdir(K / "rapor.html", t / "rapor.pdf")
    w = PdfWriter()
    for f in ("kapak.pdf", "rapor.pdf"):
        for p in PdfReader(t / f).pages:
            w.add_page(p)
    w.add_metadata({"/Title": "Hafta 6 Raporu", "/Author": "Sabri Duruk, Yunis Teymurlu"})
    with open(CIKTI, "wb") as f:
        w.write(f)
print(CIKTI, len(PdfReader(CIKTI).pages), "sayfa")
