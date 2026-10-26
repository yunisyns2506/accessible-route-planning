"""Ölçek kalibrasyonu: elle işaretlenen uç noktaları SfM pozlarıyla üçgenler.

Girdi (JSON): {"nokta_adi": {"kare": [u, v], ...}, ...}; pikseller 1920x1080 karelerde (modelin
görüntü boyutu). En az iki karede işaretli nokta gerekir. Akış:
  1. her işaret köşe olarak alt piksele inceltilir (cv2.cornerSubPix; köşe değilse yerinde kalır),
  2. bozulma giderilip (OPENCV modeli) DLT ile üçgenlenir,
  3. nokta yakındaki "aday" karelere izdüşürülür; ilk karedeki yama ile normalize çapraz korelasyon
     (NCC >= 0,85, izdüşüme 15 px içinde) tutan kareler gözleme eklenir ve yeniden üçgenlenir,
  4. her gözlemin yeniden izdüşüm hatası yazılır (işaretleme tutarlılığı göstergesi).
Çıktı: noktalar.json (3B konum, gözlemler, hatalar) ve isaretler.jpg (her gözlemin yakın kırpımı).

Kullanım: python olcek_ucgenle.py <model> <kareler_klasoru> <isaretler.json> <aday_kareler> <cikti>
  aday_kareler: virgülle ayrılmış kare adları (uzantısız), NCC ile aranacak ek kareler
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\sabod\tools\pycolmap-4.2.1")
import cv2  # noqa: E402
import numpy as np  # noqa: E402
import pycolmap  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

YAMA, ARAMA, NCC_ESIK = 12, 15, 0.85


def ucgenle(gozlem, kam, poz):
    A = []
    for ad, uv in gozlem.items():
        x = kam.cam_from_img(np.array(uv, float))
        P = poz[ad]
        A += [x[0] * P[2] - P[0], x[1] * P[2] - P[1]]
    X = np.linalg.svd(np.array(A))[2][-1]
    return X[:3] / X[3]


def izdus(X, ad, kam, poz):
    pc = poz[ad][:, :3] @ X + poz[ad][:, 3]
    return None if pc[2] <= 0 else kam.img_from_cam(pc)


def main(model, kdir, isaret_json, adaylar, out):
    out.mkdir(parents=True, exist_ok=True)
    r = pycolmap.Reconstruction(str(model))
    kam = next(iter(r.cameras.values()))
    poz = {im.name[:-4]: im.cam_from_world().matrix() for im in r.images.values() if im.has_pose}
    gri = {}

    def g(ad):
        if ad not in gri:
            gri[ad] = cv2.cvtColor(cv2.imread(str(kdir / f"{ad}.jpg")), cv2.COLOR_BGR2GRAY)
        return gri[ad]

    isaret = json.loads(Path(isaret_json).read_text(encoding="utf-8"))
    sonuc = {}
    for ad, gz in isaret.items():
        gz = {k: np.array(v, float) for k, v in gz.items()}
        for k in gz:
            c = gz[k].reshape(1, 1, 2).astype(np.float32)
            ince = cv2.cornerSubPix(g(k), c.copy(), (5, 5), (-1, -1), (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.01))[0, 0]
            if np.linalg.norm(ince - gz[k]) < 4:
                gz[k] = ince.astype(float)
        X = ucgenle(gz, kam, poz)
        ref = next(iter(gz)); u, v = np.round(gz[ref]).astype(int)
        sab = g(ref)[v - YAMA:v + YAMA + 1, u - YAMA:u + YAMA + 1]
        eklenen = {}
        for a in adaylar:
            if a in gz or a not in poz or sab.shape != (2 * YAMA + 1,) * 2:
                continue
            p = izdus(X, a, kam, poz)
            if p is None:
                continue
            pu, pv = np.round(p).astype(int); s = YAMA + ARAMA
            if not (s <= pu < 1920 - s and s <= pv < 1080 - s):
                continue
            res = cv2.matchTemplate(g(a)[pv - s:pv + s + 1, pu - s:pu + s + 1], sab, cv2.TM_CCOEFF_NORMED)
            _, mx, _, loc = cv2.minMaxLoc(res)
            if mx >= NCC_ESIK:
                eklenen[a] = np.array([pu - ARAMA + loc[0], pv - ARAMA + loc[1]], float)
        gz_tum = {**gz, **eklenen}
        if eklenen:
            X = ucgenle(gz_tum, kam, poz)
            # NCC ile eklenip 3 px'ten fazla sapan gözlemler (yanlış eşleşme) atılır, yeniden üçgenlenir
            for _ in range(3):
                kotu = [k for k in eklenen if np.linalg.norm(izdus(X, k, kam, poz) - eklenen[k]) > 3.0]
                if not kotu:
                    break
                for k in kotu:
                    eklenen.pop(k); gz_tum.pop(k)
                X = ucgenle(gz_tum, kam, poz)
        hata = {k: float(np.linalg.norm(izdus(X, k, kam, poz) - uv)) for k, uv in gz_tum.items()}
        sonuc[ad] = {"xyz": X.tolist(), "elle": {k: v.tolist() for k, v in gz.items()},
                     "ncc_ile": {k: v.tolist() for k, v in eklenen.items()}, "izdusum_hatasi_px": hata}
        print(f"{ad}: {len(gz)} elle + {len(eklenen)} NCC, hata px " + ", ".join(f"{k} {e:.1f}" for k, e in hata.items()))
    (out / "noktalar.json").write_text(json.dumps(sonuc, indent=1), encoding="utf-8")

    # yakın kırpımlar: yeşil = elle (inceltilmiş), mavi = NCC, kırmızı artı = 3B noktanın izdüşümü
    tiles = []
    for ad, s in sonuc.items():
        X = np.array(s["xyz"])
        for k, uv in list(s["elle"].items()) + list(s["ncc_ile"].items()):
            im = Image.open(kdir / f"{k}.jpg"); h = 40
            cu, cv_ = np.round(uv).astype(int)
            t = im.crop((cu - h, cv_ - h, cu + h, cv_ + h)).resize((240, 240), Image.LANCZOS); d = ImageDraw.Draw(t)
            q = (np.array(uv) - [cu - h, cv_ - h]) * 3
            renk = "lime" if k in s["elle"] else "cyan"
            d.ellipse([q[0] - 6, q[1] - 6, q[0] + 6, q[1] + 6], outline=renk, width=2)
            p = izdus(X, k, kam, poz)
            if p is not None:
                q = (p - [cu - h, cv_ - h]) * 3; d.line([q[0] - 8, q[1], q[0] + 8, q[1]], fill="red"); d.line([q[0], q[1] - 8, q[0], q[1] + 8], fill="red")
            d.rectangle([0, 0, 240, 14], fill="black"); d.text((3, 1), f"{ad} {k} {s['izdusum_hatasi_px'][k]:.1f}px", fill="white")
            tiles.append(t)
    n = 8; W = Image.new("RGB", (n * 240, -(-len(tiles) // n) * 240), "white")
    for i, t in enumerate(tiles):
        W.paste(t, ((i % n) * 240, (i // n) * 240))
    W.save(out / "isaretler.jpg", quality=90)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4].split(","), Path(sys.argv[5]))
