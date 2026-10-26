"""Adım 2 (vekil ölçü): salonda biriken kayma var mı? Sandalye sıraları ve tavan ızgarası ile.

Gerçekte düz ve birbirine paralel olan doğrusal yapılar seyrek bulutta yoğun nokta üretir:
  * 5 uzun sandalye sırası (oturak yüksekliği bandı)
  * tavan ızgarası ve aydınlatma hatları (tavan bandı), iki yönde
Her yapı kat planında bir çizgiye uydurulur (RANSAC + PCA) ve şunlar ölçülür:
  * düzlük: yapı boyunca 10 dilimde çizgiden medyan sapmanın değişimi (salon uzunluğunun %'si)
  * paralellik: aynı ailedeki çizgilerin birbirine göre açısı (derece)
  * aralık tutarlılığı: komşu sıralar arasındaki mesafenin salonun bir ucunda ve öbür ucunda
    farkı (yelpazelenme; salon boyunca biriken ölçek/yön kaymasının işareti)
  * diklik: tavan ızgarasının iki yönü arasındaki açının 90°'den sapması
Ölçek yok: uzunluklar salon uzunluğunun yüzdesi olarak verilir.

Kullanım: python analiz_siralar.py <model> <cikti_klasoru> <baslik>
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
from scipy.signal import find_peaks  # noqa: E402

RNG = np.random.default_rng(1)


def cizgi(Q, esik, n_iter=3000):
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
    return yon, m, S


def aile(XY, eks, uzunluk, en_az_aralik, genislik, en_az_nokta=150, kalin=False):
    """eks yönünde uzanan çizgiler: dik koordinattaki yoğunluk tepelerinden bulunur."""
    v = XY[:, 1 - eks]
    h, k = np.histogram(v, 400); mk = (k[:-1] + k[1:]) / 2
    adim = mk[1] - mk[0]
    hs = np.convolve(h, np.ones(3) / 3, "same")
    tepe, _ = find_peaks(hs, distance=max(1, int(en_az_aralik / adim)), prominence=0.25 * hs.max())
    sonuc = []
    for t in mk[tepe]:
        Q = XY[np.abs(v - t) < genislik]
        if len(Q) < en_az_nokta:
            continue
        if kalin:
            # kalın yapı (sandalye sırası): boyuna 12 dilimde dik koordinatın medyanı = sıranın orta çizgisi
            tt0 = Q[:, eks]; dil = np.linspace(np.percentile(tt0, 1), np.percentile(tt0, 99), 13)
            orta = np.array([(0.5 * (dil[i] + dil[i + 1]), np.median(Q[(tt0 >= dil[i]) & (tt0 < dil[i + 1]), 1 - eks]))
                             for i in range(12) if ((tt0 >= dil[i]) & (tt0 < dil[i + 1])).sum() >= 15])
            if len(orta) < 6:
                continue
            eg, kes = np.polyfit(orta[:, 0], orta[:, 1], 1)
            yon = np.array([1.0, eg]) if eks == 0 else np.array([eg, 1.0]); yon /= np.linalg.norm(yon)
            m = np.array([orta[:, 0].mean(), eg * orta[:, 0].mean() + kes]) if eks == 0 else np.array([eg * orta[:, 0].mean() + kes, orta[:, 0].mean()])
            S = Q
            prof = np.c_[orta[:, 0], (orta[:, 1] - (eg * orta[:, 0] + kes)) * np.cos(np.arctan(eg))]
            sonuc.append({"yon": yon, "m": m, "S": S, "profil": prof, "nokta": len(Q),
                          "kapsam_yuzde": float(np.ptp(orta[:, 0]) / uzunluk * 100),
                          "duzluk_yuzde": float(np.ptp(prof[:, 1]) / uzunluk * 100)})
            continue
        yon, m, S = cizgi(Q, 0.004 * uzunluk)
        if abs(yon[eks]) < np.cos(np.radians(20)):
            continue
        if yon[eks] < 0:
            yon = -yon
        nrm = np.array([-yon[1], yon[0]])
        tt = (S - m) @ yon; dd = (S - m) @ nrm
        dil = np.linspace(np.percentile(tt, 1), np.percentile(tt, 99), 11)
        prof = np.array([(0.5 * (dil[i] + dil[i + 1]), np.median(dd[(tt >= dil[i]) & (tt < dil[i + 1])]))
                         for i in range(10) if ((tt >= dil[i]) & (tt < dil[i + 1])).sum() >= 10])
        if len(prof) < 5:
            continue
        sonuc.append({"yon": yon, "m": m, "S": S, "profil": prof, "nokta": len(S),
                      "kapsam_yuzde": float(np.ptp(tt) / uzunluk * 100),
                      "duzluk_yuzde": float(np.ptp(prof[:, 1]) / uzunluk * 100)})
    return sonuc


def aci(u, v):
    return float(np.degrees(np.arccos(np.clip(abs(u @ v), 0, 1))))


def main(model, out, baslik):
    out.mkdir(parents=True, exist_ok=True)
    r = pycolmap.Reconstruction(str(model))
    pts = list(r.points3D.values())
    P = np.array([p.xyz for p in pts])
    P = P[(np.array([p.error for p in pts]) < 2.0) & (np.array([p.track.length() for p in pts]) >= 3)]
    ims = sorted([im for im in r.images.values() if im.has_pose], key=lambda i: i.name)
    C = np.array([im.projection_center() for im in ims])
    up = -np.mean([im.cam_from_world().rotation.matrix()[1] for im in ims], axis=0); up /= np.linalg.norm(up)
    Ch = C - np.outer(C @ up, up)
    V = np.linalg.svd(Ch - Ch.mean(0))[2]
    ex = V[0] - (V[0] @ up) * up; ex /= np.linalg.norm(ex); ey = np.cross(up, ex)
    o = C.mean(0)
    X = np.c_[(P - o) @ ex, (P - o) @ ey, (P - o) @ up]
    Cx = np.c_[(C - o) @ ex, (C - o) @ ey, (C - o) @ up]
    uzunluk = np.ptp(np.percentile(Cx[:, 0], [0.5, 99.5]))
    # yükseklik dağılımında iki yoğun katman: alt (zemin + oturaklar) ve üst (tavan ızgarası)
    zh = X[:, 2]; kam = np.median(Cx[:, 2])
    h, k = np.histogram(zh[zh < kam], 150); alt = k[np.argmax(h)]
    h, k = np.histogram(zh[zh > kam], 150); ust = k[np.argmax(h)]
    H = ust - alt
    oturak = (zh > alt - 0.06 * H) & (zh < alt + 0.14 * H)
    tavanb = (zh > ust - 0.08 * H) & (zh < ust + 0.12 * H)

    siralar = aile(X[oturak][:, :2], 0, uzunluk, 0.08 * uzunluk, 0.035 * uzunluk, kalin=True)
    tx = aile(X[tavanb][:, :2], 0, uzunluk, 0.03 * uzunluk, 0.006 * uzunluk)
    ty = aile(X[tavanb][:, :2], 1, uzunluk, 0.03 * uzunluk, 0.006 * uzunluk)

    sonuc = {"zemin_tavan_ayrimi": "katmanlar kamera yüksekliğine göre bulundu"}
    for ad, a in (("sandalye_siralari", siralar), ("tavan_uzun_yon", tx), ("tavan_kisa_yon", ty)):
        if not a:
            sonuc[ad] = None; continue
        ref = np.median([s["yon"] for s in a], axis=0); ref /= np.linalg.norm(ref)
        sonuc[ad] = {"cizgi_sayisi": len(a),
                     "duzluk_yuzde_medyan": round(float(np.median([s["duzluk_yuzde"] for s in a])), 3),
                     "duzluk_yuzde_en_kotu": round(float(max(s["duzluk_yuzde"] for s in a)), 3),
                     "paralellik_derece_en_buyuk": round(max(aci(s["yon"], ref) for s in a), 2),
                     "kapsam_yuzde_medyan": round(float(np.median([s["kapsam_yuzde"] for s in a])), 1)}
    if len(siralar) >= 2:
        siralar.sort(key=lambda s: s["m"][1])
        uclar = []
        for s1, s2 in zip(siralar[:-1], siralar[1:]):
            nrm = np.array([-s1["yon"][1], s1["yon"][0]])
            x_sol, x_sag = np.percentile(X[oturak][:, 0], [10, 90])
            aralik = []
            for x in (x_sol, x_sag):
                y1 = s1["m"][1] + (x - s1["m"][0]) * s1["yon"][1] / s1["yon"][0]
                y2 = s2["m"][1] + (x - s2["m"][0]) * s2["yon"][1] / s2["yon"][0]
                aralik.append(abs(y2 - y1))
            uclar.append({"sol_uc": aralik[0] / uzunluk * 100, "sag_uc": aralik[1] / uzunluk * 100,
                          "fark_yuzde_araligin": (aralik[1] - aralik[0]) / np.mean(aralik) * 100})
        sonuc["sira_araliklari"] = [{k: round(v, 2) for k, v in u.items()} for u in uclar]
    if tx and ty:
        r1 = np.median([s["yon"] for s in tx], axis=0); r2 = np.median([s["yon"] for s in ty], axis=0)
        sonuc["tavan_diklik_sapmasi_derece"] = round(abs(90 - aci(r1 / np.linalg.norm(r1), r2 / np.linalg.norm(r2))), 2)
    (out / "siralar_sonuc.json").write_text(json.dumps(sonuc, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(sonuc, indent=1, ensure_ascii=False))

    fig, axs = plt.subplots(1, 3, figsize=(20, 6.5))
    for ax, (ad, sec, a_list, renk) in zip(axs[:2], (("Sandalye sıraları (oturak bandı)", oturak, [siralar], ["C3"]),
                                                    ("Tavan ızgarası (tavan bandı)", tavanb, [tx, ty], ["C0", "C2"]))):
        ax.scatter(X[sec][::2, 0], X[sec][::2, 1], s=0.05, c="0.7")
        for a, c in zip(a_list, renk):
            for s in a:
                tt = (s["S"] - s["m"]) @ s["yon"]
                u = s["m"] + np.outer([tt.min(), tt.max()], s["yon"])
                ax.plot(u[:, 0], u[:, 1], c=c, lw=1)
        ax.set_aspect("equal"); ax.set_title(ad); ax.set_xticks([]); ax.set_yticks([])
    ax = axs[2]
    for i, s in enumerate(siralar):
        p = s["profil"]
        ax.plot((p[:, 0] - p[0, 0]) / uzunluk * 100, p[:, 1] / uzunluk * 100, "-o", ms=3,
                label=f"sıra {i + 1}: düzlük %{s['duzluk_yuzde']:.2f}")
    ax.axhline(0, c="k", lw=0.5); ax.grid(alpha=0.3); ax.legend(fontsize=8)
    ax.set_xlabel("sıra boyunca konum (salon uzunluğunun %'si)"); ax.set_ylabel("çizgiden sapma (salon uzunluğunun %'si)")
    ax.set_title("Sandalye sıraları boyunca düzlemden sapma")
    s = sonuc.get("sandalye_siralari") or {}
    fig.suptitle(f"{baslik}: {s.get('cizgi_sayisi', 0)} sıra, paralellik en çok {s.get('paralellik_derece_en_buyuk', float('nan'))}°, "
                 f"tavan diklik sapması {sonuc.get('tavan_diklik_sapmasi_derece', float('nan'))}°")
    fig.tight_layout(); fig.savefig(out / "siralar_analizi.png", dpi=110)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
