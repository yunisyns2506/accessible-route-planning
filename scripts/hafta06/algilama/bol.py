"""Eğitim / doğrulama / test bölmesi (blok bölme) ve yerel veri seti kurulumu.

Ardışık kareler neredeyse aynı olduğu için kareler tek tek değil, zaman sırasındaki
bloklar hâlinde bölünür (varsayılan blok = 15 etiketli kare). Farklı kümelere giden
komşu blokların sınırındaki birer kare tampon olarak atılır. Blokların kümelere
dağılımı, kare oranı %70/%15/%15'e yakın olacak ve her sınıf doğrulama ile testte
en az bir kez bulunacak şekilde tohumlu rastgele aramayla seçilir.
'ayri_test' kaynağı (başka kat/bina çekimi) varsa tamamı teste gider; diğer
kaynaklar yalnız eğitim/doğrulamaya bölünür.

Kullanım:
  python bol.py              # bolme.json üretir (ALG/veri)
  python bol.py --kur        # /content/veri_yerel altında det ve seg veri setlerini kurar
"""
import argparse
import csv
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from ortak import YEREL, ALG, SINIFLAR, TOHUM, oku_json, yaz_json

VERI = ALG / "veri"


def bloklar(manifest, nesneler, B):
    say = defaultdict(Counter)
    for n in nesneler:
        say[n["ad"]][n["sinif"]] += 1
    kaynak = defaultdict(list)
    for r in manifest:
        kaynak[r["kaynak"]].append(r)
    out = []
    for ad, rs in kaynak.items():
        rs.sort(key=lambda r: int(r["sira"]))
        for i in range(0, len(rs), B):
            parca = rs[i:i + B]
            c = Counter()
            for r in parca:
                c.update(say[r["ad"]])
            out.append({"kaynak": ad, "kareler": [r["ad"] for r in parca], "nesne": c})
    return out


def puan(atama, bl, hedef, toplam):
    kare, nes = defaultdict(int), defaultdict(Counter)
    for b, k in zip(bl, atama):
        kare[k] += len(b["kareler"])
        nes[k].update(b["nesne"])
    n = sum(kare.values())
    p = sum(abs(kare[k] / n - f) for k, f in hedef.items())
    for s in SINIFLAR:
        if toplam[s] == 0:
            continue
        for k, ceza in (("train", 3.0), ("test", 1.0), ("val", 0.3)):
            if k in hedef and nes[k][s] == 0:
                p += ceza
        p += 0.3 * sum(abs(nes[k][s] / toplam[s] - f) for k, f in hedef.items())
    return p


def bol(B=15, deneme=20000):
    manifest = list(csv.DictReader(open(ALG / "etiket" / "manifest.csv")))
    nesneler = oku_json(VERI / "nesneler.json")
    if nesneler is None:
        raise SystemExit("HATA: önce cvat_donustur.py çalıştırılmalı")
    bl = bloklar(manifest, nesneler, B)
    ayri = [b for b in bl if b["kaynak"] == "ayri_test"]
    serbest = [b for b in bl if b["kaynak"] != "ayri_test"]
    hedef = {"train": 0.82, "val": 0.18} if ayri else {"train": 0.70, "val": 0.15, "test": 0.15}
    toplam = Counter()
    for b in serbest:
        toplam.update(b["nesne"])
    rng = random.Random(TOHUM)
    kumeler = list(hedef)
    en_iyi, en_iyi_p = None, 1e9
    for _ in range(deneme):
        a = [rng.choices(kumeler, weights=list(hedef.values()))[0] for _ in serbest]
        p = puan(a, serbest, hedef, toplam)
        if p < en_iyi_p:
            en_iyi, en_iyi_p = a, p
    for b, k in zip(serbest, en_iyi):
        b["kume"] = k
    for b in ayri:
        b["kume"] = "test"

    # Tampon: aynı kaynakta farklı kümeye geçilen sınırda iki taraftan birer kare atılır
    atilan = set()
    onceki = {}
    for b in bl:
        o = onceki.get(b["kaynak"])
        if o is not None and o["kume"] != b["kume"]:
            atilan.add(o["kareler"][-1])
            atilan.add(b["kareler"][0])
        onceki[b["kaynak"]] = b
    bolme = {"train": [], "val": [], "test": []}
    for b in bl:
        bolme[b["kume"]] += [k for k in b["kareler"] if k not in atilan]

    say = defaultdict(Counter)
    for n in nesneler:
        say[n["ad"]][n["sinif"]] += 1
    ozet = {}
    for k, ads in bolme.items():
        c = Counter()
        for ad in ads:
            c.update(say[ad])
        ozet[k] = {"kare": len(ads), "nesne": {s: c[s] for s in SINIFLAR},
                   "nesne_iceren_kare": {s: sum(1 for ad in ads if say[ad][s]) for s in SINIFLAR}}
    sonuc = {"blok_boyu": B, "tampon_atilan": sorted(atilan), "puan": round(en_iyi_p, 4),
             "bloklar": [{"kaynak": b["kaynak"], "ilk": b["kareler"][0], "son": b["kareler"][-1],
                          "kume": b["kume"], "nesne": dict(b["nesne"])} for b in bl],
             "kumeler": bolme, "ozet": ozet}
    yaz_json(VERI / "bolme.json", sonuc)
    for k, v in ozet.items():
        print(k, v)
    print(f"tampon olarak atılan kare: {len(atilan)}")
    for s in SINIFLAR:
        eksik = [k for k in ("train", "val", "test") if ozet[k]["nesne"][s] == 0]
        if eksik:
            print(f"UYARI: '{s}' sınıfı {eksik} kümesinde yok; bu sınıf için o kümede sonuç verilemez")


def kur(yerel=YEREL):
    b = oku_json(VERI / "bolme.json")
    img = ALG / "etiket" / "images"
    for tur in ("det", "seg"):
        if (yerel / tur).exists():
            shutil.rmtree(yerel / tur)         # önceki bölmeden kalan kareler karışmasın
        for k, ads in b["kumeler"].items():
            (yerel / tur / k / "images").mkdir(parents=True, exist_ok=True)
            (yerel / tur / k / "labels").mkdir(parents=True, exist_ok=True)
            for ad in ads:
                st = Path(ad).stem
                hedef = yerel / tur / k / "images" / ad
                if not hedef.exists():
                    shutil.copy2(img / ad, hedef)
                shutil.copy2(VERI / f"labels_{tur}" / f"{st}.txt", yerel / tur / k / "labels" / f"{st}.txt")
        isimler = "\n".join(f"  {i}: {s}" for i, s in enumerate(SINIFLAR))
        (yerel / f"{tur}.yaml").write_text(
            f"path: {yerel / tur}\ntrain: train/images\nval: val/images\ntest: test/images\nnames:\n{isimler}\n")
    print("kuruldu:", yerel, {k: len(v) for k, v in b["kumeler"].items()})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--kur", action="store_true")
    ap.add_argument("--blok", type=int, default=15)
    a = ap.parse_args()
    kur() if a.kur else bol(a.blok)
