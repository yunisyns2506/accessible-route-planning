"""Rapor icin birlesik (etiketli) sekiller uretir.

Tek tek sayfa kaplayan gorseller yerine, ilgili kareleri yan yana / alt alta
birlestirip ustlerine etiket yazar. Cikti: docs/figures/sekil_*.jpg

Kullanim:
    python scripts/make_figures.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FIG = Path("docs/figures")        # rapor sekilleri (sekil*.jpg)
SRC = FIG / "kaynak"                  # ham ekran goruntuleri
REN = FIG / "render"                  # render / gercek karsilastirmalari
BAND = 34          # etiket seridi yuksekligi
GAP = 8            # paneller arasi bosluk
BG = (255, 255, 255)


def font(size: int = 20) -> ImageFont.ImageFont:
    for name in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def label(img: Image.Image, text: str, size: int = 20) -> Image.Image:
    """Goruntunun ustune etiket seridi ekler."""
    out = Image.new("RGB", (img.width, img.height + BAND), (28, 28, 30))
    out.paste(img, (0, BAND))
    d = ImageDraw.Draw(out)
    d.text((10, BAND // 2), text, fill=(255, 255, 255), anchor="lm", font=font(size))
    return out


def row(panels: list[Image.Image], height: int) -> Image.Image:
    """Panelleri ayni yukseklige olcekleyip yan yana dizer."""
    scaled = []
    for p in panels:
        w = round(p.width * height / p.height)
        scaled.append(p.resize((w, height), Image.LANCZOS))
    total_w = sum(p.width for p in scaled) + GAP * (len(scaled) - 1)
    out = Image.new("RGB", (total_w, height), BG)
    x = 0
    for p in scaled:
        out.paste(p, (x, 0))
        x += p.width + GAP
    return out


def column(panels: list[Image.Image], width: int) -> Image.Image:
    scaled = []
    for p in panels:
        h = round(p.height * width / p.width)
        scaled.append(p.resize((width, h), Image.LANCZOS))
    total_h = sum(p.height for p in scaled) + GAP * (len(scaled) - 1)
    out = Image.new("RGB", (width, total_h), BG)
    y = 0
    for p in scaled:
        out.paste(p, (0, y))
        y += p.height + GAP
    return out


def crop_viewport(path: Path) -> Image.Image:
    """Nerfstudio ekran goruntusunden sag paneli kirpar."""
    im = Image.open(path).convert("RGB")
    return im.crop((0, 28, 600, im.height))


def main() -> None:
    # Sekil 1 - kare kalitesi (iki dikey kare yan yana)
    s1 = row([
        label(Image.open(SRC / "kare_0110_en_net.jpg").convert("RGB"),
              "En net kare (Laplacian 465)"),
        label(Image.open(SRC / "kare_0311_en_bulanik.jpg").convert("RGB"),
              "En bulanik kare (Laplacian 25)"),
    ], height=760)
    s1.save(FIG / "sekil1_kare_kalitesi.jpg", quality=88)

    # Sekil 2 - egitim ilerleyisi (uc adim yan yana, panel kirpilmis)
    s2 = row([
        label(crop_viewport(SRC / "egitim_G3_adim3566.jpg"), "adim 3.566", 18),
        label(crop_viewport(SRC / "egitim_G3_adim8191.jpg"), "adim 8.191", 18),
        label(crop_viewport(SRC / "egitim_G3_adim14927.jpg"), "adim 14.927", 18),
    ], height=330)
    s2.save(FIG / "sekil2_egitim_ilerleyisi.jpg", quality=88)

    # Sekil 3 - kamera yolu
    s3 = crop_viewport(SRC / "egitim_G4_adim1473_kamera_yolu.jpg")
    s3 = s3.resize((900, round(s3.height * 900 / s3.width)), Image.LANCZOS)
    s3.save(FIG / "sekil3_kamera_yolu.jpg", quality=88)

    # Sekil 4 - uc yontemin ayni test kamerasindaki renderi (alt alta)
    s4 = column([
        label(Image.open(REN / "G2_antialiased_test00.jpg").convert("RGB"),
              "G2  antialiased  -  28,55 dB"),
        label(Image.open(REN / "G4_camopt_test00.jpg").convert("RGB"),
              "G4  kamera pozu optimizasyonu  -  21,14 dB  (sahne kaymis)"),
        label(Image.open(REN / "G7_nerfacto_test00.jpg").convert("RGB"),
              "G7  nerfacto (NeRF)  -  22,53 dB"),
    ], width=1000)
    s4.save(FIG / "sekil4_render_karsilastirma.jpg", quality=86)

    # Sekil 5 - modelin genel gorunumu (onerilen yapilandirma, 30k)
    hero = Image.open(SRC / "G2_antialiased_30k_genisaci_3.jpg").convert("RGB")
    hero = hero.resize((1200, round(hero.height * 1200 / hero.width)), Image.LANCZOS)
    hero.save(FIG / "sekil5_model_genel.jpg", quality=90)

    # Sekil 6 - iki ek aci
    s6 = row([
        label(Image.open(SRC / "G2_antialiased_30k_genisaci_1.jpg").convert("RGB"),
              "tahta tarafi", 18),
        label(Image.open(SRC / "G2_antialiased_30k_genisaci_2.jpg").convert("RGB"),
              "pencere tarafi", 18),
    ], height=420)
    s6.save(FIG / "sekil6_model_acilar.jpg", quality=88)

    for f in ["sekil1_kare_kalitesi", "sekil2_egitim_ilerleyisi",
              "sekil3_kamera_yolu", "sekil4_render_karsilastirma",
              "sekil5_model_genel", "sekil6_model_acilar"]:
        p = FIG / f"{f}.jpg"
        print(f"{f}.jpg  {Image.open(p).size}  {p.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
