"""Adım 3: eksik ya da zayıf geometri bulunan bölgeler (seyrek nokta bulutuyla).

Kat planı 0,25 m'lik (ölçekten önce: salon uzunluğunun ~%2,5'i) hücrelere bölünür ve her hücre
için üç gösterge hesaplanır:
  * nokta yoğunluğu: hücredeki güvenilir 3B nokta sayısı (zemin ve tavan katmanları ayrı)
  * görüş sayısı: hücredeki noktaları gören farklı kamera sayısı (az kamera = zayıf üçgenleme)
  * iz uzunluğu: hücredeki noktaların medyan gözlem sayısı
Ayrıca duvar boyunca (salonun çevresi) yükseklik katmanlarında boşluk oranı çıkarılır: duvar
yüzeyini temsil eden şeritte hiç nokta düşmeyen hücrelerin oranı. 3DGS'in "uydurduğu"
(geometri yerine görünümle doldurduğu) bölgeler bunlardır.

Kullanım: python analiz_eksik.py <model> <cikti_klasoru> <baslik>
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\sabod\tools\pycolmap-4.2.1")
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pycolmap  # noqa: E402

HUCRE = 0.025      # salon uzunluğunun oranı


def main(model, out, baslik):
    out.mkdir(parents=True, exist_ok=True)
    r = pycolmap.Reconstruction(str(model))
    pts = list(r.points3D.values())
    P = np.array([p.xyz for p in pts])
    hata = np.array([p.error for p in pts]); iz = np.array([p.track.length() for p in pts])
    kam = [set(el.image_id for el in p.track.elements) for p in pts]
    ims = sorted([im for im in r.images.values() if im.has_pose], key=lambda i: i.name)
    C = np.array([im.projection_center() for im in ims])
    up = -np.mean([im.cam_from_world().rotation.matrix()[1] for im in ims], axis=0); up /= np.linalg.norm(up)
    Ch = C - np.outer(C @ up, up)
    V = np.linalg.svd(Ch - Ch.mean(0))[2]
    ex = V[0] - (V[0] @ up) * up; ex /= np.linalg.norm(ex); ey = np.cross(up, ex)
    o = C.mean(0)
    X = np.c_[(P - o) @ ex, (P - o) @ ey, (P - o) @ up]
    Cx = np.c_[(C - o) @ ex, (C - o) @ ey, (C - o) @ up]
    L = np.ptp(np.percentile(Cx[:, 0], [0.5, 99.5]))
    ok = (hata < 2.0) & (iz >= 2)
    zh = X[:, 2]; kz = np.median(Cx[:, 2])
    h, k = np.histogram(zh[zh < kz], 150); alt = k[np.argmax(h)]
    h, k = np.histogram(zh[zh > kz], 150); ust = k[np.argmax(h)]
    H = ust - alt
    katman = {"zemin ve oturaklar": (zh < alt + 0.14 * H), "orta (duvarlar, kapı, pencere)": (zh >= alt + 0.14 * H) & (zh < ust - 0.08 * H),
              "tavan": (zh >= ust - 0.08 * H)}
    # ızgara: kamera yolunun %10 dışına kadar
    x0, x1 = np.percentile(Cx[:, 0], [0.5, 99.5]); y0, y1 = np.percentile(Cx[:, 1], [0.5, 99.5])
    pay = 0.08 * L; s = HUCRE * L
    xe = np.arange(x0 - pay, x1 + pay + s, s); ye = np.arange(y0 - pay, y1 + pay + s, s)
    sonuc = {"hucre_salon_uzunlugu_orani": HUCRE, "katmanlar": {}}
    fig, axs = plt.subplots(2, 3, figsize=(21, 11))
    for j, (ad, sec) in enumerate(katman.items()):
        m = ok & sec
        yog, _, _ = np.histogram2d(X[m, 0], X[m, 1], [xe, ye])
        ix = np.clip(np.digitize(X[m, 0], xe) - 1, 0, len(xe) - 2); iy = np.clip(np.digitize(X[m, 1], ye) - 1, 0, len(ye) - 2)
        gorus = np.zeros_like(yog); izm = np.full_like(yog, np.nan)
        idx = np.where(m)[0]
        hucre = {}
        for n, (a, b) in zip(idx, zip(ix, iy)):
            hucre.setdefault((a, b), [set(), []])
            hucre[(a, b)][0] |= kam[n]; hucre[(a, b)][1].append(iz[n])
        for (a, b), (ks, il) in hucre.items():
            gorus[a, b] = len(ks); izm[a, b] = np.median(il)
        # salon içi hücreler: kamera yolunun sınırları içinde
        xc = 0.5 * (xe[:-1] + xe[1:]); yc = 0.5 * (ye[:-1] + ye[1:])
        ic = (xc[:, None] > x0) & (xc[:, None] < x1) & (yc[None, :] > y0) & (yc[None, :] < y1)
        cevre = ~ic
        sonuc["katmanlar"][ad] = {
            "nokta": int(m.sum()),
            "salon_ici_bos_hucre_yuzde": round(float((yog[ic] == 0).mean() * 100), 1),
            "cevre_bos_hucre_yuzde": round(float((yog[cevre] == 0).mean() * 100), 1),
            "salon_ici_az_gorus_hucre_yuzde (<5 kamera, dolu hücreler)": round(float((gorus[ic & (yog > 0)] < 5).mean() * 100), 1),
            "medyan_gorus": float(np.median(gorus[yog > 0])), "medyan_iz": float(np.nanmedian(izm))}
        ext = [xe[0], xe[-1], ye[0], ye[-1]]
        a1 = axs[0, j].imshow(np.log10(yog.T + 1), origin="lower", extent=ext, cmap="magma")
        axs[0, j].plot(Cx[:, 0], Cx[:, 1], c="c", lw=0.3); axs[0, j].set_title(f"{ad}: nokta yoğunluğu (log10)")
        fig.colorbar(a1, ax=axs[0, j], shrink=0.7)
        g = np.where(yog > 0, gorus, np.nan)
        a2 = axs[1, j].imshow(g.T, origin="lower", extent=ext, cmap="viridis", vmax=np.nanpercentile(g, 95))
        axs[1, j].plot(Cx[:, 0], Cx[:, 1], c="w", lw=0.3); axs[1, j].set_title(f"{ad}: noktaları gören kamera sayısı")
        fig.colorbar(a2, ax=axs[1, j], shrink=0.7)
        for ax in (axs[0, j], axs[1, j]):
            ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect("equal")
    fig.suptitle(f"{baslik}: kat planında geometri kapsamı (hücre = salon uzunluğunun %{HUCRE * 100:.1f}'i; siyah/boş = nokta yok)")
    fig.tight_layout(); fig.savefig(out / "eksik_geometri.png", dpi=100)
    (out / "eksik_sonuc.json").write_text(json.dumps(sonuc, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(sonuc, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
