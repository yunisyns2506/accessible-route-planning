"""Etiketlenecek kareleri seçer ve CVAT'a yüklenecek zip'i hazırlar.

Hafta 6 hatlarının seçtiği kareler (sınıf 1.500, koridor 422) zaman sırasındadır ve
ardışık kareler neredeyse aynıdır. Her kaynaktan her k'ıncı kare alınır:
varsayılan sınıf k=6 (250 kare), koridor k=3 (~141 kare). Koridor daha sık
örneklenir çünkü asansör yalnız orada görünür.

Ayrı bir test çekimi varsa (başka kat/bina) --ayri-test ile kare klasörü verilir;
bu kareler bölmede yalnız teste gider.

Kullanım:
  python etiket_seti.py                      # sınıf k=6, koridor k=3
  python etiket_seti.py --k sinif=6 koridor=3 --ayri-test /yol/frames
Çıktı (ALG/etiket): images/*.jpg, manifest.csv, cvat_yukle.zip, cvat_etiketler.json
(cvat_etiketler.json, CVAT projesinde Labels → Raw alanına yapıştırılır.)
"""
import argparse
import csv
import shutil
import zipfile
from pathlib import Path

from ortak import ALG, KAYNAKLAR, OZNITELIKLER, yaz_json


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", nargs="*", default=["sinif=6", "koridor=3"])
    ap.add_argument("--ayri-test", type=Path, default=None)
    ap.add_argument("--ayri-test-k", type=int, default=3)
    ap.add_argument("--cikis", type=Path, default=ALG / "etiket")
    a = ap.parse_args()

    adimlar = {s.split("=")[0]: int(s.split("=")[1]) for s in a.k}
    kaynaklar = {ad: (KAYNAKLAR[ad], k) for ad, k in adimlar.items()}
    if a.ayri_test:
        kaynaklar["ayri_test"] = (a.ayri_test, a.ayri_test_k)

    img = a.cikis / "images"
    img.mkdir(parents=True, exist_ok=True)
    satirlar = []
    for ad, (klasor, k) in kaynaklar.items():
        kareler = sorted(klasor.glob("*.jpg"))
        if not kareler:
            raise SystemExit(f"HATA: {klasor} içinde kare yok")
        secilen = kareler[k // 2::k]          # pencerenin ortası; ilk kareden başlamaz
        for sira, p in enumerate(secilen):
            yeni = f"{ad}_{p.stem}.jpg"
            if not (img / yeni).exists():
                shutil.copy2(p, img / yeni)
            satirlar.append({"ad": yeni, "kaynak": ad, "kare": p.stem, "sira": sira})
        print(f"{ad}: {len(kareler)} kareden {len(secilen)} seçildi (k={k})")

    with open(a.cikis / "manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ad", "kaynak", "kare", "sira"])
        w.writeheader()
        w.writerows(satirlar)

    z = a.cikis / "cvat_yukle.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_STORED) as zf:
        for s in satirlar:
            zf.write(img / s["ad"], s["ad"])
    renk = {"kapi": "#e6550d", "merdiven": "#3182bd", "asansor": "#31a354"}
    yaz_json(a.cikis / "cvat_etiketler.json", [
        {"name": s, "color": renk[s], "type": "polygon", "attributes": [
            {"name": o, "mutable": False, "input_type": "select", "default_value": v[0], "values": v}
            for o, v in oz.items()]} for s, oz in OZNITELIKLER.items()])
    print(f"toplam {len(satirlar)} kare → {z} ({z.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
