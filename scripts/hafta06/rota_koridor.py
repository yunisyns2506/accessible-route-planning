"""Koridor çekimi için ölçeksiz, sade şema: asansör → K3 → asansör.

Kullanım: python rota_koridor.py <cikti_klasoru>
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle, Wedge  # noqa: E402

L = 20.0            # şema uzunluğu
K3 = 16.0           # kapının şemadaki yeri
GRI, KIRMIZI, MAVI, SARI = "0.25", "#c0392b", "#2471a3", "#f1c40f"


def taban(ax):
    ax.add_patch(Rectangle((0, 0), L, 3, fc="#fbfbfb", ec="none", zorder=0))
    ax.plot([0, L], [3, 3], c="#5dade2", lw=5, zorder=2)
    ax.text(L / 2, 3.28, "korkuluk / cam", ha="center", fontsize=13, color="#2e86c1")
    ax.plot([0, K3 - 0.8], [0, 0], c=GRI, lw=5, zorder=2); ax.plot([K3 + 0.8, L], [0, 0], c=GRI, lw=5, zorder=2)
    ax.plot([K3 - 0.8, K3 + 0.8], [0, 0], c="#27ae60", lw=5, zorder=2)
    ax.text(K3, -0.48, "K3", ha="center", fontsize=15, weight="bold", color="#27ae60")
    ax.text(7, -0.48, "beyaz duvar", ha="center", fontsize=13, color="0.35")
    ax.add_patch(Rectangle((-1.2, 0.6), 1.2, 1.8, fc="#bdc3c7", ec="k", zorder=3))
    ax.text(-0.6, 1.5, "asan-\nsör", ha="center", va="center", fontsize=12, zorder=4)
    ax.set_xlim(-1.5, L + 0.5); ax.set_ylim(-1.1, 3.9); ax.axis("off")


def ok(ax, a, b, c, lw=4):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=30, color=c, lw=lw, zorder=5))


def bak(ax, p, yon, r=1.6):
    ax.add_patch(Wedge(p, r, yon - 47, yon + 47, fc=SARI, ec="#b7950b", alpha=.6, zorder=6))
    ax.plot(*p, "s", ms=9, c="k", zorder=7)


def main(out):
    fig, axs = plt.subplots(3, 1, figsize=(15, 13.5))

    ax = axs[0]; taban(ax)
    ax.set_title("1 · GİDİŞ  ~75 sn: orta hattan, telefon göğüs üstünde (1,3–1,4 m), düz, 10° aşağı", loc="left", fontsize=17, weight="bold")
    ok(ax, (0.2, 1.5), (K3 - 2.3, 1.5), KIRMIZI); bak(ax, (6.5, 1.5), 0)
    ax.text(0.15, 1.95, "3 sn dur", fontsize=12, color=KIRMIZI, weight="bold")

    ax = axs[1]; taban(ax)
    ax.set_title("2 · K3 KAPISI  ~30 sn: A'dan kapıya bak → B'den kapıya bak → içeri gir (C) → dönüp kapıya bak → çık", loc="left", fontsize=17, weight="bold")
    A, B, C = (K3 - 2.3, 1.5), (K3 + 2.3, 1.5), (K3, -0.65)
    ok(ax, A, B, KIRMIZI, lw=3)
    bak(ax, A, -33); bak(ax, B, 213)
    ax.text(A[0] - 0.75, A[1] + 0.25, "A", fontsize=18, weight="bold"); ax.text(B[0] + 0.45, B[1] + 0.25, "B", fontsize=18, weight="bold")
    ax.text(K3 + 1.1, -0.75, "C: 2 m içeride\nkapıya bak", fontsize=12, va="center")
    ok(ax, (K3, 0.9), (K3, -0.15), KIRMIZI, lw=3)

    ax = axs[2]; taban(ax)
    ax.set_title("3 · DÖNÜŞ  ~75 sn: aynı yoldan asansöre, telefon bel hizasında (~1 m), düz, 5° yukarı", loc="left", fontsize=17, weight="bold")
    ok(ax, (K3, 1.5), (0.2, 1.5), MAVI); bak(ax, (9, 1.5), 180)
    ax.text(0.15, 1.95, "3 sn dur, kaydı durdur", fontsize=12, color=MAVI, weight="bold")

    fig.suptitle("Koridor çekimi · tek video, kesmeden, ~3 dk · 0,5× (13mm), 4K 30 fps · şema ölçeksiz\n"
                 "Sarı üçgen: telefonun baktığı yön", fontsize=18)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.88, bottom=0.03, hspace=0.3)
    fig.savefig(Path(out) / "rota_koridor.png", dpi=75)


if __name__ == "__main__":
    main(sys.argv[1])
