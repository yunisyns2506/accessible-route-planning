"""D2 ve D3: ince ayar eğitimleri (Ultralytics). Kaldığı yerden sürer.

D2 (kutu):  yolov8n, yolo11n, yolo26n   → /content/veri_yerel/det.yaml
D3 (maske): yolov8n-seg, yolo26n-seg    → /content/veri_yerel/seg.yaml
Hepsi aynı ayarlarla: COCO ön eğitimli ağırlık, 960 px, 100 epok, erken durdurma 30,
tohum 0. Koşular Drive'a (ALG/kosular/<ad>) yazılır; Colab kopsa da last.pt'den sürer.

Kullanım: python egit.py            # hepsi sırayla
          python egit.py yolo26n     # tek model
"""
import shutil
import sys
import time
from pathlib import Path

from ortak import YEREL, EPOK, GORUNTU_BOYU, ALG, SABIR, TOHUM, oku_json, yaz_json

MODELLER = {
    "yolov8n": ("yolov8n.pt", "det"),
    "yolo11n": ("yolo11n.pt", "det"),
    "yolo26n": ("yolo26n.pt", "det"),
    "yolov8n-seg": ("yolov8n-seg.pt", "seg"),
    "yolo26n-seg": ("yolo26n-seg.pt", "seg"),
}
KOS = ALG / "kosular"


def egit(ad: str) -> None:
    from ultralytics import YOLO
    agirlik, tur = MODELLER[ad]
    d = KOS / ad
    if (d / "bitti.json").exists():
        print(f"{ad}: zaten bitti, atlandı")
        return
    son = d / "weights" / "last.pt"
    t = time.time()
    if son.exists():
        print(f"{ad}: {son} üzerinden sürdürülüyor")
        try:
            YOLO(str(son)).train(resume=True)
        except AssertionError as e:                 # eğitim bitmiş ama bitti.json yazılmadan kopmuş
            if "finished" not in str(e):
                raise
            print(f"{ad}: eğitim zaten tamamlanmış, işaretleniyor")
    else:
        if d.exists():
            shutil.rmtree(d)
        YOLO(agirlik).train(data=str(YEREL / f"{tur}.yaml"), imgsz=GORUNTU_BOYU, epochs=EPOK,
                            patience=SABIR, seed=TOHUM, deterministic=True, batch=16, workers=4,
                            project=str(KOS), name=ad, exist_ok=True, plots=True, verbose=False)
    sure = oku_json(d / "sure.json", {"dk": 0})["dk"] + (time.time() - t) / 60
    yaz_json(d / "sure.json", {"dk": round(sure, 1)})
    yaz_json(d / "bitti.json", {"agirlik": agirlik, "tur": tur, "egitim_dk": round(sure, 1)})
    print(f"{ad}: bitti ({sure:.1f} dk)")


if __name__ == "__main__":
    for ad in (sys.argv[1:] or list(MODELLER)):
        egit(ad)
