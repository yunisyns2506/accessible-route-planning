"""Adım 2: duvarlar arasında geometrik kayma var mı? (seyrek nokta bulutuyla)

Hafta 4'te LoMa'nın dokusuz yüzeyde de 3B nokta ürettiği görülmüştü; bu modelde de kamera
yolunun dışında, duvar tarafında ~13 bin nokta var. Her duvar için, kamera yolunun ötesindeki
ve zemin/tavan katmanları dışındaki tüm noktalara (her yükseklikte) RANSAC ile düşey bir düzlem
uydurulur. Ölçülenler:
  * karşılıklı duvarların paralelliği ve komşu duvarların dikliği (derece)
  * duvarların düşeyliği: duvar normalinin zemine paralellikten sapması (derece)
  * düzlemsellik (iç noktaların düzleme RMS uzaklığı) ve duvar boyunca kayma: duvar boyunca
    10 dilimde noktaların düzleme medyan uzaklığının değişimi. SfM'de biriken kayma, düz bir
    duvarın yay gibi bükülmesi ya da ucunun kaçması olarak görünür.
  * zemin eğilmesi: zemin noktalarının uzun ve kısa eksen boyunca düzlemden sapması
Ölçek henüz yok: uzunluklar salon uzunluğunun yüzdesi olarak verilir; ölçek kalibrasyonundan
sonra cm'ye çevrilecek.

Kullanım: python analiz_duvar.py <model> <cikti_klasoru> <baslik>
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

RNG = np.random.default_rng(1)


def ransac_cizgi(Q, esik, n_iter=4000):
    """2B noktalara en çok iç noktalı çizgi; iç noktalarla PCA ile iyileştirilir."""
    en_iyi = None
    for _ in range(n_iter):
        a, b = Q[RNG.choice(len(Q), 2, replace=False)]
        d = b - a
        if np.linalg.norm(d) < 1e-9:
            continue
        nrm = np.array([-d[1], d[0]]) / np.linalg.norm(d)
        ic = np.abs((Q - a) @ nrm) < esik
        if en_iyi is None or ic.sum() > en_iyi.sum():
            en_iyi = ic
    S = Q[en_iyi]; m = S.mean(0)
    yon = np.linalg.svd(S - m)[2][0]
    return yon, m, en_iyi


def ransac_duzlem(P, esik, n_iter=2000):
    en_iyi = None
    for _ in range(n_iter):
        a, b, c = P[RNG.choice(len(P), 3, replace=False)]
        n = np.cross(b - a, c - a)
        if np.linalg.norm(n) < 1e-12:
            continue
        n /= np.linalg.norm(n)
        ic = np.abs((P - a) @ n) < esik
        if en_iyi is None or ic.sum() > en_iyi.sum():
            en_iyi = ic
    Q = P[en_iyi]; m = Q.mean(0)
    return np.linalg.svd(Q - m)[2][-1], m, en_iyi


def aci2(u, v):
    return np.degrees(np.arccos(np.clip(abs(u @ v), 0, 1)))


def main(model, out, baslik):
    out.mkdir(parents=True, exist_ok=True)
    r = pycolmap.Reconstruction(str(model))
    pts = list(r.points3D.values())
    P = np.array([p.xyz for p in pts])
    ok = (np.array([p.error for p in pts]) < 2.0) & (np.array([p.track.length() for p in pts]) >= 3)
    P = P[ok]
    ims = sorted([im for im in r.images.values() if im.has_pose], key=lambda i: i.name)
    C = np.array([im.projection_center() for im in ims])
    up = -np.mean([im.cam_from_world().rotation.matrix()[1] for im in ims], axis=0); up /= np.linalg.norm(up)
    Ch = C - np.outer(C @ up, up)
    V = np.linalg.svd(Ch - Ch.mean(0))[2]
    ex = V[0] - (V[0] @ up) * up; ex /= np.linalg.norm(ex); ey = np.cross(up, ex)
    o = C.mean(0)
    X = np.c_[(P - o) @ ex, (P - o) @ ey, (P - o) @ up]
    Cx = np.c_[(C - o) @ ex, (C - o) @ ey, (C - o) @ up]
    z_kam = np.median(Cx[:, 2])

    # zemin: kameraların altındaki en yoğun yatay katman, RANSAC düzlemi
    zh = X[:, 2]
    h, k = np.histogram(zh[zh < z_kam], 120); z0 = k[np.argmax(h)]
    sec = np.abs(zh - z0) < 0.08
    n_z, m_z, ic = ransac_duzlem(X[sec], 0.02)
    if n_z[2] < 0:
        n_z = -n_z
    zemin = X[sec][ic]
    yuk = (X - m_z) @ n_z
    kamera_yuk = np.median((Cx - m_z) @ n_z)
    tavan = np.percentile(yuk, 99.5)
    govde = (yuk > 0.04 * tavan) & (yuk < 0.92 * tavan)       # zemin ve tavan katmanları dışı
    xmin, xmax = np.percentile(Cx[:, 0], [0.5, 99.5]); ymin, ymax = np.percentile(Cx[:, 1], [0.5, 99.5])
    uzunluk = xmax - xmin                                       # salon uzunluğu vekili: kamera yolunun boyu
    pay = 0.03 * uzunluk
    # her duvar: kamera yolunun ötesi, köşelere taşmamak için öbür eksende kamera aralığı içinde
    bolge = {"sol kısa duvar": (govde & (X[:, 0] < xmin - pay) & (X[:, 1] > ymin) & (X[:, 1] < ymax), 0),
             "sağ kısa duvar": (govde & (X[:, 0] > xmax + pay) & (X[:, 1] > ymin) & (X[:, 1] < ymax), 0),
             "alt uzun duvar": (govde & (X[:, 1] < ymin - pay) & (X[:, 0] > xmin) & (X[:, 0] < xmax), 1),
             "üst uzun duvar": (govde & (X[:, 1] > ymax + pay) & (X[:, 0] > xmin) & (X[:, 0] < xmax), 1)}
    esik = 0.006 * uzunluk
    duvar = {}
    for ad, (s_, eks) in bolge.items():
        Q = X[s_]
        eksen = np.eye(3)[eks]
        # düşey ve duvar yönüne bakan düzlem şartıyla RANSAC
        en_iyi = None
        for _ in range(4000):
            a3, b3, c3 = Q[RNG.choice(len(Q), 3, replace=False)]
            n = np.cross(b3 - a3, c3 - a3)
            if np.linalg.norm(n) < 1e-12:
                continue
            n /= np.linalg.norm(n)
            if abs(n @ n_z) > np.sin(np.radians(10)) or abs(n @ eksen) < np.cos(np.radians(30)):
                continue
            ic = np.abs((Q - a3) @ n) < esik
            if en_iyi is None or ic.sum() > en_iyi.sum():
                en_iyi = ic
        S = Q[en_iyi]; m = S.mean(0)
        n = np.linalg.svd(S - m)[2][-1]
        dd = (S - m) @ n
        t = S[:, 1 - eks]
        dil = np.linspace(np.percentile(t, 1), np.percentile(t, 99), 11)
        prof = np.array([(0.5 * (dil[i] + dil[i + 1]), np.median(dd[(t >= dil[i]) & (t < dil[i + 1])]))
                         for i in range(10) if ((t >= dil[i]) & (t < dil[i + 1])).sum() >= 15])
        duvar[ad] = {"n": n, "m": m, "S": S, "profil": prof, "nokta": int(en_iyi.sum()), "aday": int(len(Q)),
                     "kapsam_yuzde": float(np.ptp(t) / uzunluk * 100),
                     "rms_yuzde": float(np.sqrt(np.mean(dd ** 2)) / uzunluk * 100),
                     "kayma_yuzde": float(np.ptp(prof[:, 1]) / uzunluk * 100) if len(prof) > 2 else float("nan"),
                     "duseylik_sapma_derece": float(np.degrees(np.arcsin(min(1, abs(n @ n_z)))))}

    d = duvar
    dik = {f"{a} – {b}": float(abs(90 - aci2(d[a]["n"], d[b]["n"])))
           for a in ("sol kısa duvar", "sağ kısa duvar") for b in ("alt uzun duvar", "üst uzun duvar")}
    dz = (zemin - m_z) @ n_z
    zem = {}
    for eks, ad in ((0, "uzun"), (1, "kısa")):
        t = zemin[:, eks]; dil = np.linspace(np.percentile(t, 2), np.percentile(t, 98), 11)
        pr = [np.median(dz[(t >= dil[i]) & (t < dil[i + 1])]) for i in range(10) if ((t >= dil[i]) & (t < dil[i + 1])).sum() > 20]
        zem[ad] = float(np.ptp(pr) / uzunluk * 100)
    sonuc = {
        "paralellik_uzun_duvarlar_derece": aci2(d["alt uzun duvar"]["n"], d["üst uzun duvar"]["n"]),
        "paralellik_kisa_duvarlar_derece": aci2(d["sol kısa duvar"]["n"], d["sağ kısa duvar"]["n"]),
        "diklik_sapmasi_derece": dik,
        "duvarlar": {k: {"nokta": v["nokta"], "aday": v["aday"], "kapsam_yuzde": round(v["kapsam_yuzde"], 1),
                         "rms_yuzde": round(v["rms_yuzde"], 3), "kayma_yuzde": round(v["kayma_yuzde"], 3),
                         "duseylik_sapma_derece": round(v["duseylik_sapma_derece"], 2)} for k, v in d.items()},
        "zemin_egilme_yuzde": {k: round(v, 3) for k, v in zem.items()},
        "zemin_rms_yuzde": round(float(np.sqrt(np.mean(dz ** 2)) / uzunluk * 100), 3),
        "en_boy_orani": float(abs((d["üst uzun duvar"]["m"] - d["alt uzun duvar"]["m"]) @ d["alt uzun duvar"]["n"]) /
                              abs((d["sağ kısa duvar"]["m"] - d["sol kısa duvar"]["m"]) @ d["sol kısa duvar"]["n"])),
    }
    (out / "duvar_sonuc.json").write_text(json.dumps(sonuc, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(sonuc, indent=1, ensure_ascii=False))

    fig = plt.figure(figsize=(16, 7.5))
    ax = fig.add_subplot(1, 2, 1)
    ax.scatter(X[govde][::4, 0], X[govde][::4, 1], s=0.05, c="0.7")
    ax.plot(Cx[:, 0], Cx[:, 1], c="k", lw=0.4, alpha=0.5)
    renk = dict(zip(d, ("C0", "C1", "C2", "C3")))
    for a, w in d.items():
        ax.scatter(w["S"][:, 0], w["S"][:, 1], s=0.6, c=renk[a], label=f"{a} ({w['nokta']} nokta)")
        yon = np.cross(n_z, w["n"]); yon /= np.linalg.norm(yon)
        t = (w["S"] - w["m"]) @ yon
        u = w["m"] + np.outer([t.min(), t.max()], yon)
        ax.plot(u[:, 0], u[:, 1], c=renk[a], lw=1.2)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([]); ax.legend(markerscale=6, fontsize=8, loc="upper left")
    ax.set_title("Kat planı: duvar düzlemlerine giren noktalar (renkli)")
    ax2 = fig.add_subplot(1, 2, 2)
    for a, w in d.items():
        p = w["profil"]
        if len(p):
            ax2.plot((p[:, 0] - p[0, 0]) / uzunluk * 100, p[:, 1] / uzunluk * 100, "-o", c=renk[a], ms=3,
                     label=f"{a}: kayma %{w['kayma_yuzde']:.2f}, düşeylik {w['duseylik_sapma_derece']:.1f}°")
    ax2.axhline(0, c="k", lw=0.5); ax2.grid(alpha=0.3); ax2.legend(fontsize=8)
    ax2.set_xlabel("duvar boyunca konum (salon uzunluğunun %'si)"); ax2.set_ylabel("düzlemden sapma (salon uzunluğunun %'si)")
    ax2.set_title("Duvar boyunca düzlemden sapma (10 dilim, medyan)")
    fig.suptitle(f"{baslik}: paralellik uzun {sonuc['paralellik_uzun_duvarlar_derece']:.2f}°, kısa "
                 f"{sonuc['paralellik_kisa_duvarlar_derece']:.2f}°; diklik sapması en çok {max(dik.values()):.2f}°")
    fig.tight_layout(); fig.savefig(out / "duvar_analizi.png", dpi=110)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
