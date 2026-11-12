"""CVAT dışa aktarımını (CVAT for images 1.1) YOLO etiketlerine çevirir.

Çokgenler segmentasyon etiketi olur; kutu etiketi çokgenin sınırlayıcı kutusudur.
CVAT'ta kutu (rectangle) çizilmişse yalnız algılama etiketine girer.
Öznitelikler (durum, cam, kesik) nesneler.json'a yazılır ve değerlendirmede
recall'ı kırılımlara ayırmak için kullanılır. Görevdeki her kare etiketlenmiş
sayılır: nesnesi olmayan kare, nesne içermeyen (negatif) kare demektir.

Kullanım: python cvat_donustur.py <cvat_export.zip veya annotations.xml>
Çıktı (ALG/veri): labels_seg/, labels_det/, nesneler.json, sayim.json
"""
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

from ortak import ALG, SINIFLAR, yaz_json


def xml_oku(p: Path) -> ET.Element:
    if p.suffix == ".zip":
        with zipfile.ZipFile(p) as z:
            ad = next(n for n in z.namelist() if n.endswith(".xml"))
            return ET.fromstring(z.read(ad))
    return ET.parse(p).getroot()


def noktalar(s: str):
    return [tuple(map(float, xy.split(","))) for xy in s.split(";")]


def main(kaynak: Path, cikis: Path = ALG / "veri") -> None:
    kok = xml_oku(kaynak)
    seg_d, det_d = cikis / "labels_seg", cikis / "labels_det"
    for d in (seg_d, det_d):
        d.mkdir(parents=True, exist_ok=True)
    nesneler, sayim, bilinmeyen = [], Counter(), Counter()
    goruntu = 0
    for im in kok.iter("image"):
        ad = Path(im.get("name")).name
        W, H = float(im.get("width")), float(im.get("height"))
        seg, det = [], []
        for el in im:
            et = el.get("label")
            if et not in SINIFLAR:
                bilinmeyen[et] += 1
                continue
            c = SINIFLAR.index(et)
            oz = {a.get("name"): (a.text or "").strip() for a in el.findall("attribute")}
            if el.tag == "polygon":
                p = noktalar(el.get("points"))
                xs, ys = [x for x, _ in p], [y for _, y in p]
                seg.append(f"{c} " + " ".join(f"{x / W:.6f} {y / H:.6f}" for x, y in p))
                x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
            elif el.tag == "box":
                x0, y0, x1, y1 = (float(el.get(k)) for k in ("xtl", "ytl", "xbr", "ybr"))
            else:
                continue
            x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
            det.append(f"{c} {(x0 + x1) / 2 / W:.6f} {(y0 + y1) / 2 / H:.6f} {(x1 - x0) / W:.6f} {(y1 - y0) / H:.6f}")
            nesneler.append({"ad": ad, "sinif": et, "kutu": [round(v, 1) for v in (x0, y0, x1, y1)],
                             "cokgen": el.tag == "polygon", "oznitelik": oz})
            sayim[et] += 1
        (seg_d / f"{Path(ad).stem}.txt").write_text("\n".join(seg))
        (det_d / f"{Path(ad).stem}.txt").write_text("\n".join(det))
        goruntu += 1
    yaz_json(cikis / "nesneler.json", nesneler)
    ozet = {"goruntu": goruntu, "nesne": dict(sayim),
            "nesneli_goruntu": len({n["ad"] for n in nesneler}),
            "kutu_olarak_cizilen": sum(not n["cokgen"] for n in nesneler),
            "bilinmeyen_etiket": dict(bilinmeyen)}
    yaz_json(cikis / "sayim.json", ozet)
    print(ozet)
    if bilinmeyen:
        print("UYARI: sınıf listesinde olmayan etiketler atlandı:", dict(bilinmeyen))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
