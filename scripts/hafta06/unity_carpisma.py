"""Birleşik sınıf + koridor Unity PLY'sinden çarpışma kutuları üretir ve DerslikCarpisma.cs yazar.

Hafta 5 sürümünden farkları (birleşik Hafta 6 modeli için):
  * Platform ve sınıf sınırları elle değil, gerçek-zemin katmanından otomatik bulunur: katman
    "platform ön kenarından karşı duvara, iki yan duvar arasına" uzanır. Katmanın en küçük x'i
    platform ön kenarı, z aralığı sınıfın iki yan duvarıdır. Platform yalnız bu z aralığında geçerli,
    böylece platformla aynı x'teki koridor zemini platform sayılmaz.
  * Dış sınır duvarları yok (K3 kapısını kapatıyordu). Onun yerine "yürünebilir alan" kurulur:
    yerel zemin kotunda Gaussian bulunan hücrelerin en büyük bağlı bölgesi. Bu bölgede olmayan ve
    engel de olmayan hücreler boşluk kutusuyla kapatılır; kapı açıklığı zemin taşıdığı için açık kalır.
  * İsteğe bağlı --kapi x0 x1 z0 z1 ile verilen dikdörtgendeki engel hücreleri silinir (kapı kanadı
    açıklığı kapatıyorsa).
  * Kutular 20 cm hücrelidir: yürümeyi sınırlamak içindir, geçiş genişliği denetimi için kullanılmaz.

Kullanım: python unity_carpisma.py <birlesik_..._unity.ply> <cikti_klasoru> [--kapi -7.0 -5.4 6.0 7.8]
Çıktı: DerslikCarpisma.cs, carpisma_plan.png, carpisma_ozet.json
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from plyfile import PlyData  # noqa: E402
from scipy import ndimage  # noqa: E402

HUCRE = 0.2
ZEMIN_Y = -0.015          # düz zemin katmanının kotu (m, Unity)
PLATFORM_YUK = 0.46       # sahne yüksekliği, mezura D2 (m)
BANT = (0.5, 1.9)         # yerel zeminin üstünde engel bandı (m)
ESIK = 15                 # engel için hücre başına opak Gaussian
ZEMIN_BANT = (-1.5, 0.12) # yerel zemine göre zemin kanıtı bandı (parlak zeminde Gaussian'lar zeminin 1 m+ altına iner)
ZEMIN_ESIK = 3            # zemin kanıtı için hücre başına Gaussian
ENGEL_Y = 2.6             # engel kutularının üst kotu (zemine göre)
MIN_ALAN = 15.0           # bu alandan küçük kopuk zemin parçaları yürünemez sayılır (m²)


def dikdortgenler(G):
    """Dolu hücreleri açgözlü yöntemle eksen hizalı dikdörtgenlere böler: (i0, j0, i1, j1)."""
    G = G.copy(); out = []
    nx, nz = G.shape
    for i in range(nx):
        for j in range(nz):
            if not G[i, j]:
                continue
            j1 = j
            while j1 < nz and G[i, j1]:
                j1 += 1
            i1 = i + 1
            while i1 < nx and G[i1, j:j1].all():
                i1 += 1
            G[i:i1, j:j1] = False
            out.append((i, j, i1, j1))
    return out


def main(ply: Path, out: Path, kapi=None):
    v = PlyData.read(str(ply))["vertex"]
    X = np.c_[v["x"], v["y"], v["z"]].astype(float)
    opk = 1 / (1 + np.exp(-np.asarray(v["opacity"], dtype=float)))
    # zemin_gercek.py'nin eklediği katman: opaklık logit = log(199), yatay σ = 0,033, düşey σ = 0,002 (tam değerler)
    names = v.data.dtype.names
    s0 = np.asarray(v["scale_0"]) if "scale_0" in names else None
    s2 = np.asarray(v["scale_2"]) if "scale_2" in names else None
    katman = (np.abs(np.asarray(v["opacity"], dtype=float) - np.log(199)) < 1e-3) & \
             (np.abs(np.asarray(v["scale_1"], dtype=float) - np.log(0.002)) < 1e-3)
    if s0 is not None and s2 is not None:
        katman &= (np.abs(s0 - np.log(0.033)) < 1e-3) & (np.abs(s2 - np.log(0.033)) < 1e-3)
    print(f"zemin katmanı: {int(katman.sum())} Gaussian")
    if katman.sum() < 1000:
        raise SystemExit("HATA: gerçek-zemin katmanı bulunamadı; *_gercek_zemin_unity.ply dosyası verilmeli")
    K = X[katman]
    PX = K[:, 0].min()                                  # platform ön kenarı
    SZ = (K[:, 2].min(), K[:, 2].max())                 # sınıf yan duvarları
    PY = ZEMIN_Y + PLATFORM_YUK
    # Platformun arka ucu = sınıfın arka duvarı: platform kenarının gerisinde, sınıf genişliği boyunca uzanan,
    # 0,8-2,5 m yüksekliğinde nokta yoğunluğu en fazla olan x (kenara en yakın güçlü tepe)
    duvar = (X[:, 0] < PX - 0.3) & (X[:, 0] > PX - 8) & (X[:, 2] > SZ[0] + 0.5) & (X[:, 2] < SZ[1] - 0.5) & \
            (X[:, 1] > PY + 0.8) & (X[:, 1] < PY + 2.5) & (opk > 0.5)
    PX0 = None
    if duvar.sum() > 500:
        h, e = np.histogram(X[duvar, 0], bins=np.arange(PX - 8, PX - 0.3 + 1e-6, 0.1))
        guclu = np.where(h >= 0.5 * h.max())[0]
        PX0 = float(e[guclu.max()] + 0.05)                                  # kenara en yakın güçlü tepe
    print(f"platform: ön kenar x = {PX:.2f}, arka duvar x = {PX0}")

    XZ = X[opk > 0.1]                      # zemin kanıtı: parlak zeminde Gaussian'lar yarı saydam olabiliyor
    X, opk = X[opk > 0.5], opk[opk > 0.5]
    x0, z0 = np.percentile(X[:, 0], 0.5) - 0.5, np.percentile(X[:, 2], 0.5) - 0.5
    x1, z1 = np.percentile(X[:, 0], 99.5) + 0.5, np.percentile(X[:, 2], 99.5) + 0.5
    nx, nz = int(np.ceil((x1 - x0) / HUCRE)), int(np.ceil((z1 - z0) / HUCRE))
    xc = lambda i: x0 + i * HUCRE                       # noqa: E731
    zc = lambda j: z0 + j * HUCRE                       # noqa: E731

    # hücre başına yerel zemin kotu
    gx, gz = np.meshgrid(xc(np.arange(nx) + 0.5), zc(np.arange(nz) + 0.5), indexing="ij")
    platform = (gx < PX) & (gz > SZ[0]) & (gz < SZ[1]) & (gx > (PX0 if PX0 is not None else -np.inf))
    zemin_kot = np.where(platform, PY, ZEMIN_Y)

    ix = ((X[:, 0] - x0) / HUCRE).astype(int); iz = ((X[:, 2] - z0) / HUCRE).astype(int)
    ic = (ix >= 0) & (ix < nx) & (iz >= 0) & (iz < nz)
    ix, iz, Xi = ix[ic], iz[ic], X[ic]
    yuk = Xi[:, 1] - zemin_kot[ix, iz]

    say = np.zeros((nx, nz)); b = (yuk > BANT[0]) & (yuk < BANT[1]); np.add.at(say, (ix[b], iz[b]), 1)
    engel = say >= ESIK
    kom = sum(np.roll(np.roll(engel, a, 0), c, 1) for a in (-1, 0, 1) for c in (-1, 0, 1)) - engel
    engel &= kom >= 2
    if kapi:
        kx0, kx1, kz0, kz1 = kapi
        engel &= ~((gx > kx0) & (gx < kx1) & (gz > kz0) & (gz < kz1))

    jx = ((XZ[:, 0] - x0) / HUCRE).astype(int); jz = ((XZ[:, 2] - z0) / HUCRE).astype(int)
    jc = (jx >= 0) & (jx < nx) & (jz >= 0) & (jz < nz)
    jx, jz = jx[jc], jz[jc]
    zyuk = XZ[jc, 1] - zemin_kot[jx, jz]
    zs = np.zeros((nx, nz)); b = (zyuk > ZEMIN_BANT[0]) & (zyuk < ZEMIN_BANT[1]); np.add.at(zs, (jx[b], jz[b]), 1)
    zemin = ndimage.binary_closing(zs >= ZEMIN_ESIK, iterations=2) & ~engel
    etiket, n = ndimage.label(zemin)
    if n == 0:
        raise SystemExit("HATA: yürünebilir zemin bulunamadı")
    alan = np.bincount(etiket.ravel()) * HUCRE ** 2
    alan[0] = 0
    yurunur = np.isin(etiket, np.where(alan >= MIN_ALAN)[0])     # 15 m²'den büyük bütün zemin bölgeleri
    print("zemin bölgeleri (m²):", sorted([round(float(x), 1) for x in alan[alan > 1]], reverse=True)[:6])
    bosluk = ~yurunur & ~engel

    kutular, bos = [], []
    for G, hedef in ((engel, kutular), (bosluk, bos)):
        for i, j, i1, j1 in dikdortgenler(G):
            taban = float(zemin_kot[min((i + i1) // 2, nx - 1), min((j + j1) // 2, nz - 1)])
            hedef.append(((xc(i) + xc(i1)) / 2, taban + ENGEL_Y / 2, (zc(j) + zc(j1)) / 2,
                          xc(i1) - xc(i), ENGEL_Y, zc(j1) - zc(j)))
    px0 = PX0 if PX0 is not None else x0
    W, D = x1 - x0, z1 - z0; cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    ozel = [(cx, ZEMIN_Y - 0.25, cz, W + 2, 0.5, D + 2),                                    # zemin
            ((px0 + PX) / 2, (ZEMIN_Y + PY) / 2, (SZ[0] + SZ[1]) / 2,                       # platform
             PX - px0, PY - ZEMIN_Y, SZ[1] - SZ[0])]
    hepsi = ozel + kutular + bos
    out.mkdir(parents=True, exist_ok=True)
    satir = ",\n".join("        " + ", ".join(f"{a:.3f}f" for a in k) for k in hepsi)
    cs = (Path(__file__).with_name("DerslikCarpisma.cs.sablon").read_text(encoding="utf-8")
          .replace("/*KUTULAR*/", satir).replace("/*ADET*/", str(len(hepsi)))
          .replace("/*OZEL*/", str(len(ozel))))
    (out / "DerslikCarpisma.cs").write_text(cs, encoding="utf-8")

    fig, ax = plt.subplots(figsize=(14, 9))
    s = np.random.default_rng(0).permutation(len(X))[:300000]
    ax.scatter(X[s, 0], X[s, 2], s=0.2, c="0.75")
    for k, renk in [(kk, (1, 0, 0, .35)) for kk in kutular] + [(kk, (.2, .2, .2, .25)) for kk in bos]:
        ax.add_patch(plt.Rectangle((k[0] - k[3] / 2, k[2] - k[5] / 2), k[3], k[5], fc=renk, ec="none"))
    ax.add_patch(plt.Rectangle((px0, SZ[0]), PX - px0, SZ[1] - SZ[0], fc="none", ec="b", ls="--", lw=1))
    ax.text(PX - 0.2, SZ[1] - 0.4, f"platform ({PLATFORM_YUK:.2f} m)", color="b", ha="right")
    if kapi:
        ax.add_patch(plt.Rectangle((kapi[0], kapi[2]), kapi[1] - kapi[0], kapi[3] - kapi[2], fc="none", ec="g", lw=1.5))
    ax.set_aspect("equal"); ax.set_xlim(x0 - 0.5, x1 + 0.5); ax.set_ylim(z0 - 0.5, z1 + 0.5)
    ax.set_title(f"Çarpışma: kırmızı engel ({len(kutular)}), gri boşluk ({len(bos)}); mavi kesikli platform. Üstten X–Z, m")
    fig.tight_layout(); fig.savefig(out / "carpisma_plan.png", dpi=80)
    ozet = {"platform_on_kenari_x": round(float(PX), 3), "platform_arka_x": round(float(px0), 3), "sinif_z": [round(float(SZ[0]), 3), round(float(SZ[1]), 3)],
            "platform_ust_y": round(PY, 3), "engel_kutusu": len(kutular), "bosluk_kutusu": len(bos),
            "toplam_kutu": len(hepsi), "yurunur_m2": round(float(yurunur.sum()) * HUCRE ** 2, 1),
            "izgara": [nx, nz], "x": [round(float(x0), 2), round(float(x1), 2)], "z": [round(float(z0), 2), round(float(z1), 2)], "kapi": kapi}
    (out / "carpisma_ozet.json").write_text(json.dumps(ozet, ensure_ascii=False, indent=2))
    print(ozet)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ply", type=Path)
    ap.add_argument("cikti", type=Path)
    ap.add_argument("--kapi", type=float, nargs=4, default=None, metavar=("X0", "X1", "Z0", "Z1"))
    a = ap.parse_args()
    main(a.ply, a.cikti, a.kapi)
