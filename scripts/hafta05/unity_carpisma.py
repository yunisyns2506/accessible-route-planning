"""Unity'ye hazırlanmış splat .ply'sinden çarpışma kutuları üretir ve DerslikCarpisma.cs yazar.

Gaussian'larda yüzey yok; bu yüzden opak Gaussian'lar (opaklık > 0,5) kat planında 0,2 m hücrelere
düşürülür:
  * zemin: sınıf zemini y = 0, öğretmen platformu (x < PLATFORM_X) y = PLATFORM_Y,
  * engel: yerel zeminin 0,5–1,9 m üstünde en az ESIK Gaussian bulunan hücre (duvar, sandalye sırtı,
    masa, kürsü); platform yüksekliği (0,41 m) bu bandın altında kaldığı için basamak gibi çıkılabilir,
  * tek başına kalan hücreler (komşusu < 2) uçuşan parça sayılıp atılır,
  * engel hücreleri açgözlü dikdörtgen birleştirmeyle az sayıda kutuya indirilir,
  * salonun çevresine güvenlik duvarları eklenir.
Kutular splat GameObject'inin yerel koordinatlarındadır (C# tarafında onun çocuğu olarak kurulur).

Kullanım: python unity_carpisma.py <unity.ply> <cikti_klasoru>
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from plyfile import PlyData  # noqa: E402

HUCRE = 0.2
PLATFORM_X, PLATFORM_Y = -9.4, 0.41      # platform ön kenarı (x) ve üst yüzeyi (m); kontrol_unity_ply ve kesitlerden
BANT = (0.5, 1.9)                        # yerel zeminin üstünde engel bandı (m)
ESIK = 15                                # hücre başına opak Gaussian
ENGEL_Y = 2.6                            # engel kutularının üst kotu (zıplamayla aşılmasın)


def dikdortgenler(G):
    """Dolu hücreleri açgözlü yöntemle eksen hizalı dikdörtgenlere böler: (i0, j0, i1, j1) dahil-hariç."""
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


def main(ply, out):
    v = PlyData.read(str(ply))["vertex"]
    X = np.c_[v["x"], v["y"], v["z"]]
    X = X[1 / (1 + np.exp(-np.asarray(v["opacity"]))) > 0.5]
    x0, z0 = np.percentile(X[:, 0], 0.5) - 0.5, np.percentile(X[:, 2], 0.5) - 0.5
    x1, z1 = np.percentile(X[:, 0], 99.5) + 0.5, np.percentile(X[:, 2], 99.5) + 0.5
    nx, nz = int(np.ceil((x1 - x0) / HUCRE)), int(np.ceil((z1 - z0) / HUCRE))
    ix = ((X[:, 0] - x0) / HUCRE).astype(int); iz = ((X[:, 2] - z0) / HUCRE).astype(int)
    ic = (ix >= 0) & (ix < nx) & (iz >= 0) & (iz < nz)
    yerel = np.where(X[:, 0] < PLATFORM_X, PLATFORM_Y, 0.0)
    b = ic & (X[:, 1] - yerel > BANT[0]) & (X[:, 1] - yerel < BANT[1])
    say = np.zeros((nx, nz)); np.add.at(say, (ix[b], iz[b]), 1)
    G = say >= ESIK
    kom = sum(np.roll(np.roll(G, a, 0), c, 1) for a in (-1, 0, 1) for c in (-1, 0, 1)) - G
    G &= kom >= 2
    kutular = []                                   # (merkez x, y, z, boyut x, y, z)
    xc = lambda i: x0 + i * HUCRE                  # noqa: E731
    zc = lambda j: z0 + j * HUCRE                  # noqa: E731
    for i, j, i1, j1 in dikdortgenler(G):
        taban = PLATFORM_Y if xc((i + i1) / 2) < PLATFORM_X else 0.0
        kutular.append(((xc(i) + xc(i1)) / 2, (taban + ENGEL_Y) / 2, (zc(j) + zc(j1)) / 2,
                        xc(i1) - xc(i), ENGEL_Y - taban, zc(j1) - zc(j)))
    # zemin, platform ve çevre duvarları
    W, D = x1 - x0, z1 - z0; cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    ozel = [(cx, -0.25, cz, W + 2, 0.5, D + 2),                                         # sınıf zemini
            ((x0 - 1 + PLATFORM_X) / 2, PLATFORM_Y / 2, cz, PLATFORM_X - x0 + 1, PLATFORM_Y, D + 2),  # platform
            (x0 - 0.25, 2.0, cz, 0.5, 4.0, D + 2), (x1 + 0.25, 2.0, cz, 0.5, 4.0, D + 2),
            (cx, 2.0, z0 - 0.25, W + 2, 4.0, 0.5), (cx, 2.0, z1 + 0.25, W + 2, 4.0, 0.5)]
    out.mkdir(parents=True, exist_ok=True)
    satir = ",\n".join("        " + ", ".join(f"{a:.3f}f" for a in k) for k in ozel + kutular)
    cs = (Path(__file__).with_name("DerslikCarpisma.cs.sablon").read_text(encoding="utf-8")
          .replace("/*KUTULAR*/", satir).replace("/*ADET*/", str(len(ozel) + len(kutular))))
    (out / "DerslikCarpisma.cs").write_text(cs, encoding="utf-8")

    fig, ax = plt.subplots(figsize=(13, 9))
    s = np.random.default_rng(0).permutation(len(X))[:300000]
    ax.scatter(X[s, 0], X[s, 2], s=0.2, c="0.7")
    for k in kutular:
        ax.add_patch(plt.Rectangle((k[0] - k[3] / 2, k[2] - k[5] / 2), k[3], k[5], fc=(1, 0, 0, 0.35), ec="r", lw=0.4))
    ax.axvline(PLATFORM_X, c="b", ls="--", lw=1); ax.text(PLATFORM_X - 0.2, z1 - 0.3, "platform (0,41 m)", color="b", ha="right")
    ax.set_aspect("equal"); ax.set_xlim(x0 - 0.5, x1 + 0.5); ax.set_ylim(z0 - 0.5, z1 + 0.5)
    ax.set_title(f"Çarpışma kutuları (kırmızı, {len(kutular)} engel + zemin/platform/çevre), üstten X–Z, m")
    fig.tight_layout(); fig.savefig(out / "carpisma_plan.png", dpi=80)
    print(f"engel kutusu {len(kutular)}, toplam {len(ozel) + len(kutular)}; ızgara {nx}x{nz}; x {x0:.2f}..{x1:.2f}, z {z0:.2f}..{z1:.2f}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
