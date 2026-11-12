"""D1, D2, D3, D4: bütün modelleri aynı kurallarla değerlendirir.

1. Her model doğrulama ve test karelerinde düşük eşikle (0,01) çalıştırılır; tahminler önbelleğe yazılır.
2. Güven eşiği yalnız DOĞRULAMA kümesinde seçilir: sınıf ortalaması F1'i en yüksek yapan eşik.
3. Bu eşikle TEST kümesinde sınıf başına TP, FP, FN, precision, recall, F1 hesaplanır.
   Bir tespit, aynı sınıftan bir gerçek kutuyla IoU ≥ 0,5 ise doğrudur (güvene göre açgözlü eşleme).
4. Recall ayrıca özniteliklere göre (kapı durumu, cam, kesik) kırılır.
5. İnce ayarlı modeller için Ultralytics'in mAP@0,5 değeri (kutu, maske) test kümesinde eklenir.

D1 eğitimsiz modeller: YOLO-World (yolov8s-worldv2) ve YOLOE-26 (yoloe-26s-seg), ISTEMLER'deki
İngilizce istemlerle. Aynı sınıfa giden istemlerin tespitleri sınıf içi NMS ile birleştirilir.

Kullanım: python degerlendir.py            # mevcut bütün modeller
Çıktı (ALG/sonuclar): tahmin_<model>.json, sonuclar.json, sonuclar.csv, sonuclar.md
"""
import csv
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from ortak import YEREL, GORUNTU_BOYU, ALG, IOU_ESIK, ISTEMLER, SINIFLAR, oku_json, yaz_json

SON = ALG / "sonuclar"
SIFIR_ATIS = {"yolo-world-s": ("yolov8s-worldv2.pt", "world"), "yoloe-26s": ("yoloe-26s-seg.pt", "yoloe")}
ESIKLER = np.round(np.arange(0.05, 0.91, 0.05), 2)


def iou(a, b):
    x0, y0 = np.maximum(a[:, None, 0], b[None, :, 0]), np.maximum(a[:, None, 1], b[None, :, 1])
    x1, y1 = np.minimum(a[:, None, 2], b[None, :, 2]), np.minimum(a[:, None, 3], b[None, :, 3])
    kes = np.clip(x1 - x0, 0, None) * np.clip(y1 - y0, 0, None)
    alan = lambda k: (k[:, 2] - k[:, 0]) * (k[:, 3] - k[:, 1])
    return kes / (alan(a)[:, None] + alan(b)[None, :] - kes + 1e-9)


def model_yukle(ad):
    """(predict fonksiyonu, tahmin sınıf no → bizim sınıf no eşlemesi)"""
    from ultralytics import YOLO
    if ad in SIFIR_ATIS:
        agirlik, tur = SIFIR_ATIS[ad]
        istem = [i for s in SINIFLAR for i in ISTEMLER[s]]
        esle = [SINIFLAR.index(s) for s in SINIFLAR for _ in ISTEMLER[s]]
        if tur == "world":
            m = YOLO(agirlik)
            m.set_classes(istem)
        else:
            from ultralytics import YOLOE
            m = YOLOE(agirlik)
            m.set_classes(istem, m.get_text_pe(istem))
        return m, esle
    m = YOLO(str(ALG / "kosular" / ad / "weights" / "best.pt"))
    return m, list(range(len(SINIFLAR)))


def tahmin_et(ad, kumeler):
    p = SON / f"tahmin_{ad}.json"
    onbellek = oku_json(p, {})
    if all(k in onbellek for k in kumeler):
        return onbellek
    import torch
    from torchvision.ops import batched_nms
    m, esle = model_yukle(ad)
    tur = "seg" if ad.endswith("-seg") else "det"
    for k in kumeler:
        if k in onbellek:
            continue
        resimler = sorted((YEREL / tur / k / "images").glob("*.jpg"))
        out, sure = {}, []
        for r in m.predict([str(x) for x in resimler], conf=0.01, iou=0.6, imgsz=GORUNTU_BOYU,
                           stream=True, verbose=False):
            b = r.boxes
            kutu = b.xyxy.cpu()
            sinif = torch.tensor([esle[int(c)] for c in b.cls.cpu()], dtype=torch.long)
            guven = b.conf.cpu()
            if len(kutu) and ad in SIFIR_ATIS:          # istemler birleşince sınıf içi NMS
                tut = batched_nms(kutu.float(), guven.float(), sinif, 0.5)
                kutu, sinif, guven = kutu[tut], sinif[tut], guven[tut]
            out[Path(r.path).name] = [[*map(float, kutu[i]), int(sinif[i]), float(guven[i])]
                                      for i in range(len(kutu))]
            sure.append(sum(r.speed.values()))
        onbellek[k] = {"tahmin": out, "ms_kare": float(np.median(sure)) if sure else None}
        yaz_json(p, onbellek)
    return onbellek


def gercekler(kume):
    nes = oku_json(ALG / "veri" / "nesneler.json")
    ads = set(oku_json(ALG / "veri" / "bolme.json")["kumeler"][kume])
    g = defaultdict(list)
    for n in nes:
        if n["ad"] in ads:
            g[n["ad"]].append(n)
    return ads, g


def esle(tahmin, ads, g, esik):
    """Sınıf başına TP/FP/FN ve her gerçek nesnenin bulunup bulunmadığı."""
    tp, fp, fn = Counter(), Counter(), Counter()
    bulundu = []
    for ad in ads:
        t = [x for x in tahmin.get(ad, []) if x[5] >= esik]
        for ci, s in enumerate(SINIFLAR):
            gt = [n for n in g.get(ad, []) if n["sinif"] == s]
            pr = sorted([x for x in t if x[4] == ci], key=lambda x: -x[5])
            kullan = [False] * len(gt)
            if gt and pr:
                M = iou(np.array([x[:4] for x in pr]), np.array([n["kutu"] for n in gt]))
                for i in range(len(pr)):
                    j = int(np.argmax(np.where(kullan, -1, M[i])))
                    if not kullan[j] and M[i, j] >= IOU_ESIK:
                        kullan[j] = True
                        tp[s] += 1
                    else:
                        fp[s] += 1
            else:
                fp[s] += len(pr)
            fn[s] += kullan.count(False)
            bulundu += [(n, k) for n, k in zip(gt, kullan)]
    return tp, fp, fn, bulundu


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def map_ultralytics(ad):
    from ultralytics import YOLO
    tur = "seg" if ad.endswith("-seg") else "det"
    m = YOLO(str(ALG / "kosular" / ad / "weights" / "best.pt"))
    v = m.val(data=str(YEREL / f"{tur}.yaml"), split="test", imgsz=GORUNTU_BOYU, verbose=False, plots=False)
    out = {"kutu_map50": float(v.box.map50)}
    if tur == "seg":
        out["maske_map50"] = float(v.seg.map50)
    return out


def main():
    SON.mkdir(parents=True, exist_ok=True)
    modeller = [a for a in SIFIR_ATIS] + sorted(
        p.name for p in (ALG / "kosular").glob("*") if (p / "bitti.json").exists())
    val_ads, val_g = gercekler("val")
    test_ads, test_g = gercekler("test")
    sonuc = {}
    for ad in modeller:
        print("değerlendiriliyor:", ad)
        t = tahmin_et(ad, ["val", "test"])
        sinif_val = [s for s in SINIFLAR if any(n["sinif"] == s for v in val_g.values() for n in v)]
        en_iyi = (0, -1.0)
        for e in ESIKLER:
            tp, fp, fn, _ = esle(t["val"]["tahmin"], val_ads, val_g, e)
            f1 = np.mean([prf(tp[s], fp[s], fn[s])[2] for s in sinif_val]) if sinif_val else 0
            if f1 > en_iyi[1]:
                en_iyi = (float(e), float(f1))
        esik = en_iyi[0]
        tp, fp, fn, bulundu = esle(t["test"]["tahmin"], test_ads, test_g, esik)
        sinif = {}
        for s in SINIFLAR:
            p, r, f = prf(tp[s], fp[s], fn[s])
            sinif[s] = {"nesne": tp[s] + fn[s], "tp": tp[s], "fp": fp[s], "fn": fn[s],
                        "precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3)}
        kirilim = defaultdict(lambda: [0, 0])
        for n, k in bulundu:
            for oz, deger in n["oznitelik"].items():
                kirilim[f"{n['sinif']}.{oz}={deger}"][0] += int(k)
                kirilim[f"{n['sinif']}.{oz}={deger}"][1] += 1
        sonuc[ad] = {"esik_val": esik, "val_ort_f1": round(en_iyi[1], 3), "test": sinif,
                     "test_ort_f1": round(float(np.mean([sinif[s]["f1"] for s in SINIFLAR if sinif[s]["nesne"]] or [0])), 3),
                     "recall_kirilim": {k: f"{a}/{b}" for k, (a, b) in sorted(kirilim.items())},
                     "ms_kare": t["test"]["ms_kare"], "sifir_atis": ad in SIFIR_ATIS}
        if ad not in SIFIR_ATIS:
            sonuc[ad].update(map_ultralytics(ad))
            sonuc[ad]["egitim_dk"] = oku_json(ALG / "kosular" / ad / "bitti.json")["egitim_dk"]
        yaz_json(SON / "sonuclar.json", sonuc)
    rapor(sonuc)


def rapor(sonuc):
    with open(SON / "sonuclar.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "sinif", "nesne", "tp", "fp", "fn", "precision", "recall", "f1", "esik"])
        for ad, r in sonuc.items():
            for s, v in r["test"].items():
                w.writerow([ad, s, v["nesne"], v["tp"], v["fp"], v["fn"], v["precision"], v["recall"], v["f1"], r["esik_val"]])
    ozet = oku_json(ALG / "veri" / "bolme.json")["ozet"]
    L = ["# Algılama deneyi sonuçları (test kümesi)", "",
         "Küme | Kare | " + " | ".join(f"{s} nesne" for s in SINIFLAR), "---|---|" + "---|" * len(SINIFLAR)]
    L += [f"{k} | {v['kare']} | " + " | ".join(str(v["nesne"][s]) for s in SINIFLAR) for k, v in ozet.items()]
    L += ["", "Model | Eşik (val) | " + " | ".join(f"{s} P / R / F1" for s in SINIFLAR) + " | Ort. F1 | mAP50 kutu | mAP50 maske | ms/kare",
          "---|---|" + "---|" * len(SINIFLAR) + "---|---|---|---|"]
    for ad, r in sonuc.items():
        hucre = [f"{v['precision']:.2f} / {v['recall']:.2f} / {v['f1']:.2f} (n={v['nesne']})" for v in r["test"].values()]
        sayi = lambda k, n: f"{r[k]:.{n}f}" if r.get(k) is not None else "–"
        L.append(f"{ad} | {r['esik_val']} | " + " | ".join(hucre) + f" | {r['test_ort_f1']:.2f} | "
                 f"{sayi('kutu_map50', 3)} | {sayi('maske_map50', 3)} | {sayi('ms_kare', 1)}")
    (SON / "sonuclar.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
