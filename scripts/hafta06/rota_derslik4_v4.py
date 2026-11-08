"""Derslik 4 tekrar çekimi, son rota: hafta 5'in düz geçişleri + 45° çapraz geçiş + kürsü, zemin, tavan.

Kullanım: python rota_derslik4_v4.py <kroki_taban.npz> <cikti_klasoru>
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from rota_derslik4 import ARA_Y, SIRA_X, goris, taban as taban_k3, yol  # noqa: E402

XS, XE = SIRA_X[0] - 0.1, SIRA_X[1] + 0.45


def taban(ax, *a):
    """Ortak taban; K3 yıldızı bu rotada başlangıç değil, kaldırılır."""
    r = taban_k3(ax, *a)
    ax.lines[-1].remove()
    return r


def zikzak(aralar, ilk_geri):
    """Sıra aralarından tek geçiş. ilk_geri: ilk ara kürsüden arkaya (-x)."""
    g = []
    for i, k in enumerate(aralar):
        y = ARA_Y[k]
        geri = (i % 2 == 0) == ilk_geri
        g += [[XE, y], [XS, y]] if geri else [[XS, y], [XE, y]]
    return g


def main(npz, out):
    z = np.load(npz); out = Path(out)
    bas = z["kamera"][0]
    fig, axs = plt.subplots(2, 4, figsize=(34, 14.5)); axs = axs.ravel()

    # 1 · salon turu
    _, (xi, xa, yi, ya) = taban(axs[0], z, "1 · Salon turu  ~2 dk",
                                "Duvarlardan ~1 m içeride tam tur\nYükseklik 1,3 m · Dikey 10° aşağı\nYatay: DÜZ (yürüme yönü)")
    d = 1.0
    yol(axs[0], [bas, [bas[0], ya - d], [xa - d, ya - d], [xa - d, yi + d], [xi + d, yi + d], [xi + d, ya - d], [XE + 0.6, ya - d]])
    axs[0].plot(*bas, "o", ms=15, c="#c0392b", zorder=9)
    goris(axs[0], (-3, yi + d), 180, r=1.8)
    axs[0].text(bas[0] + 0.35, bas[1], "BAŞLA", fontsize=11, va="center", weight="bold", color="#c0392b", zorder=10)

    # 2 · düz 1,3 m
    taban(axs[1], z, "2 · Sıra araları, düz  ~3 dk",
          "6. aradan 1. araya zikzak (hafta 5 ile aynı)\nYükseklik 1,3 m · Dikey 10° aşağı\nYatay: DÜZ · Bir ara ~25 sn")
    yol(axs[1], zikzak(range(5, -1, -1), True), lw=2.6, ok_ara=3)
    goris(axs[1], (-3, ARA_Y[2]), 0 if False else 0, r=1.5)
    axs[1].text(XE + 0.3, ARA_Y[5], "6. ara\nbaşla", va="center", fontsize=10); axs[1].text(XE + 0.3, ARA_Y[0], "1. ara\nbitir", va="center", fontsize=10)

    # 3 · düz 0,75 m, yön ters
    taban(axs[2], z, "3 · Sıra araları, alçak, YÖN TERS  ~3 dk",
          "1. aradan 6. araya: her ara 2. bölümün TERS yönünde\nYükseklik 0,75 m · Dikey 5° yukarı\nYatay: DÜZ · Bir ara ~25 sn")
    yol(axs[2], zikzak(range(6), True), lw=2.6, ok_ara=3)
    goris(axs[2], (-3, ARA_Y[2]), 180, r=1.5)
    axs[2].text(XE + 0.3, ARA_Y[0], "1. ara\nbaşla", va="center", fontsize=10); axs[2].text(XE + 0.3, ARA_Y[5], "6. ara\nbitir", va="center", fontsize=10)

    # 4 · çapraz
    taban(axs[3], z, "4 · Sıra araları, ÇAPRAZ  ~5 dk",
          "Her aradan arkaya git, aynı aradan öne dön; 6. aradan 1. araya\nYükseklik 1,5 m · Dikey 20° aşağı\nYatay: HEP 45° SOLA · Bir geçiş ~25 sn")
    g = []
    for k in range(5, -1, -1):
        y = ARA_Y[k]
        g += [[XE, y + 0.2], [XS, y + 0.2], [XS, y - 0.2], [XE, y - 0.2]]
    yol(axs[3], g, lw=2.0, ok_ara=6)
    goris(axs[3], (-3, ARA_Y[3] + 0.2), 225, r=1.5); goris(axs[3], (-3, ARA_Y[2] - 0.2), 45, r=1.5)

    # 5 · kürsü
    taban(axs[4], z, "5 · Kürsü ve masa  ~1,5 dk",
          "Çevresinde 2 tur, ~1,5 m uzaktan: önce 1,3 m, sonra 0,9 m\nDikey 15° aşağı\nYatay: 45° NESNEYE doğru · Arkası dar ise yan yürü")
    kx0, kx1, ky0, ky1 = 8.6, 9.7, -4.6, -2.4
    axs[4].add_patch(Rectangle((kx0, ky0), kx1 - kx0, ky1 - ky0, fc="#7f8c8d", ec="k", zorder=4))
    axs[4].text(kx0 - 0.15, ky1 + 0.9, "kürsü/masa\n(tahmini yer)", ha="right", fontsize=10)
    e = 0.75
    yol(axs[4], [[kx0 - e, ky1 + e], [kx0 - e, ky0 - e], [kx1 + 0.6, ky0 - e], [kx1 + 0.6, ky1 + e], [kx0 - e, ky1 + e]], ok_ara=1)

    # 6 · zemin
    taban(axs[5], z, "6 · Açık zemin  ~1,5 dk",
          "Kürsü önünde 2 şerit, sonra kapı duvarı boyunca\nYükseklik 1,4 m · Dikey 35° AŞAĞI\nYatay: DÜZ")
    yol(axs[5], [[6.6, ya - 1.2], [6.6, yi + 1.0], [7.8, yi + 1.0], [7.8, ya - 1.2]], ok_ara=3)
    yol(axs[5], [[5.5, yi + 0.7], [XS, yi + 0.7]], ok_ara=5)
    goris(axs[5], (6.6, 1), 270, r=1.4)

    # 7 · tavan
    taban(axs[6], z, "7 · Tavan, dönüş  ~1,5 dk",
          "2. ve 5. ara hizasında uzun kenar; kesik çizgide telefon düz, başlangıca dön\nYükseklik: kollar yukarı (~2 m) · Dikey 35° YUKARI\nYatay: DÜZ · Bitiş: başlangıç kadrajı, 3 sn dur")
    yol(axs[6], [[XS, ARA_Y[1]], [XE, ARA_Y[1]], [XE + 0.6, ARA_Y[4]], [XS, ARA_Y[4]]], ok_ara=5)
    yol(axs[6], [[XS, ARA_Y[4]], [XS, ya - 0.9], [6.6, ya - 0.9], bas], ok_ara=5, ls="--", lw=2)
    axs[6].plot(*bas, "o", ms=15, c="#c0392b", zorder=9)
    goris(axs[6], (-3, ARA_Y[1]), 0, r=1.4)

    ax = axs[7]; ax.axis("off")
    ax.text(0.0, 0.97,
            "Tek video, kesmeden · ~17 dk\n"
            "Lens 0,5× (13mm) · 4K 30 fps\n"
            "Her şey kilitli (ISO, enstantane, beyaz dengesi)\n\n"
            "Her bölüm başında 2 sn kıpırdama:\n"
            "bölümleri videoda bulmamızı sağlar\n\n"
            "Sarı üçgen: telefonun yatayda baktığı yön\n"
            "Kırmızı nokta: başlangıç ve bitiş\n\n"
            "Düz: sıraların önü ve arkası, kameraların yeri\n"
            "Çapraz: sıraların yan yüzü",
            va="top", fontsize=17, transform=ax.transAxes, linespacing=1.5)
    fig.suptitle("Derslik 4 · çekim rotası: hafta 5'in düz geçişleri + çapraz geçiş + kürsü, zemin, tavan", fontsize=24, y=0.995)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.91, bottom=0.1, wspace=0.05, hspace=0.42)
    fig.savefig(out / "rota_derslik4.png", dpi=70)
    fig.savefig(out / "rota_derslik4.svg")
    print("yazıldı")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
