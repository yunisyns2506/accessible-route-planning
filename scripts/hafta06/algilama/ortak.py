"""Hafta 6 algılama deneyi: ortak ayarlar.

Sınıflar, Drive yolları ve küçük yardımcılar. Bütün betikler bunu içe aktarır.
"""
import json
import os
from pathlib import Path

# --- Sınıflar (sıra = YOLO sınıf numarası; değiştirme)
SINIFLAR = ["kapi", "merdiven", "asansor"]

# Eğitimsiz modeller için metin istemleri; aynı sınıfa giden istemlerin tespitleri birleştirilir
ISTEMLER = {
    "kapi": ["door", "glass door"],
    "merdiven": ["stairs", "staircase"],
    "asansor": ["elevator door", "elevator"],
}

# CVAT öznitelikleri (etiketleme kılavuzu ile aynı)
OZNITELIKLER = {
    "kapi": {"durum": ["kapali", "acik", "yari_acik", "tek_kanat_acik", "iki_kanat_acik"],
             "cam": ["hayir", "evet"], "kesik": ["hayir", "evet"]},
    "merdiven": {"kesik": ["hayir", "evet"]},
    "asansor": {"durum": ["kapali", "acik"], "kesik": ["hayir", "evet"]},
}

# --- Drive yolları (Colab)
H6 = Path(os.environ.get("H6", "/content/drive/MyDrive/Hafta 6 Çalışmaları"))
ALG = Path(os.environ.get("ALG", "/content/drive/MyDrive/Hafta 6 Algılama"))
KAYNAKLAR = {  # ad: kare klasörü (Hafta 6 hatlarının seçtiği keskin kareler, 1920x1080)
    "sinif": H6 / "derslik4_cekim2" / "frames_1080",
    "koridor": H6 / "derslik4_koridor" / "frames_1080",
}

YEREL = Path(os.environ.get("YEREL", "/content/veri_yerel"))  # eğitim için yerel kopya

# --- Deney ayarları
TOHUM = 0
IOU_ESIK = 0.5          # tespit doğru sayılırken kutu IoU eşiği
GORUNTU_BOYU = int(os.environ.get("GORUNTU_BOYU", 960))     # eğitim/çıkarım görüntü boyu (uzun kenar)
EPOK = int(os.environ.get("EPOK", 100))
SABIR = 30              # erken durdurma


def yaz_json(p: Path, veri) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(veri, ensure_ascii=False, indent=2))
    tmp.replace(p)


def oku_json(p: Path, varsayilan=None):
    return json.loads(p.read_text()) if p.exists() else varsayilan
