"""Hafta 4 raporunun sekillerini uretir (docs/figures/hafta-04/).

Kullanim:
    python scripts/hafta04/make_figures.py

Girdi: experiments/hafta-04_sinif-01/*.csv, runs/sinif-01/hafta-04/*/renders,
data/sinif-01/hafta-04/sfm/*, data/sinif-01/hafta-04/dense/*/fused.ply
"""
import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from common import EXP, REPO, RUNS, WORK  # noqa: E402

OUT = REPO / "docs" / "figures" / "hafta-04"
# Kategorik renkler sabit sirada (dogrulanmis referans palet, ilk uc yuva);
# her cikarici ayrica kendi isaretcisini tasir (renk tek basina kimlik degil).
EXT = {"sift": ("SIFT", "#2a78d6", "o"),
       "aliked": ("ALIKED + LightGlue", "#eb6834", "s"),
       "loma": ("LoMa", "#1baf7a", "^")}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
MATCH_TR = {"exhaustive": "exhaustive", "sequential": "sequential",
            "sequential_loop": "sequential+loop", "vocab_tree": "vocab_tree",
            "vocab_tree_k7": "vocab_tree k=7"}
MAP_TR = {"incremental": "incremental", "global": "global",
          "hierarchical_leaf100": "hierarchical\n(leaf=100)"}
BLUES = matplotlib.colors.LinearSegmentedColormap.from_list(
    "blue", ["#cde2fb", "#2a78d6", "#0d366b"])

plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.facecolor": "#fcfcfb",
                     "axes.facecolor": "#fcfcfb", "savefig.dpi": 200})


def rows(name: str) -> list[dict]:
    return list(csv.DictReader(open(EXP / name, encoding="utf-8")))


def f(x):
    return float(x) if x not in ("", None) else None


def run_key(run: str) -> tuple[str, str, str]:
    ext, rest = run.split("_", 1)
    mapper = "incremental" if rest.endswith("incremental") else "global"
    return ext, rest[: -len(mapper) - 1], mapper


SHORT = {("exhaustive", "incremental"): "exh + inc", ("exhaustive", "global"): "exh + glob",
         ("sequential", "incremental"): "seq + inc", ("sequential", "global"): "seq + glob",
         ("sequential_loop", "incremental"): "seq+loop + inc",
         ("sequential_loop", "global"): "seq+loop + glob"}
# Cakisan etiketler icin elle kaydirma (punto); verilmeyenler sagda
OFFSET = {("sift", "exhaustive", "global"): (-8, -10, "right"),
          ("sift", "exhaustive", "incremental"): (-8, 6, "right"),
          ("loma", "exhaustive", "incremental"): (-8, 7, "right"),
          ("loma", "sequential", "incremental"): (-8, -9, "right"),
          ("aliked", "sequential_loop", "incremental"): (-8, 0, "right"),
          ("loma", "exhaustive", "global"): (-8, 0, "right")}


def fig_correct_vs_psnr(sfm: list[dict], gs: list[dict]) -> None:
    """Her cikarici ayri panelde; her nokta hangi SfM kombinasyonu oldugunu yazar."""
    key = {(r["extractor"], r["matching"], r["mapper"]): r for r in sfm}
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.9), sharex=True, sharey=True)
    for ax, ext in zip(axes, EXT):
        name, color, marker = EXT[ext]
        for g in gs:
            k = run_key(g["run"])
            if k[0] != ext:
                continue
            x, y = f(key[k]["correct_posed_pct"]), f(g["psnr"])
            ax.scatter(x, y, s=60, color=color, marker=marker, edgecolor="#fcfcfb",
                       linewidth=1.5, zorder=3)
            dx, dy, ha = OFFSET.get(k, (8, 0, "left"))
            label = SHORT[(k[1], k[2])]
            if k == ("sift", "sequential", "incremental"):
                label += " (14 test karesi)"
            ax.annotate(label, (x, y), xytext=(dx, dy), textcoords="offset points",
                        fontsize=7.5, color=MUTED, ha=ha, va="center")
        ax.set_title(name, fontsize=10)
        ax.set_xlim(10, 105)
        ax.set_ylim(14, 30)
        ax.grid(color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.set_xlabel("Doğru pozlanan kare (%)")
    axes[0].set_ylabel("3DGS test PSNR (dB)")
    fig.tight_layout()
    fig.savefig(OUT / "sekil_h4_1_dogruluk_psnr.png")
    plt.close(fig)


def fig_correct_matrix(sfm: list[dict]) -> None:
    """Dogru pozlanan kare orani: hucre basina tek sayi (349 karenin %'si)."""
    matches, mappers = list(MATCH_TR), list(MAP_TR)
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.4), sharey=True)
    for ax, ext in zip(axes, EXT):
        m = np.full((len(matches), len(mappers)), np.nan)
        for r in sfm:
            if r["extractor"] == ext and r["mapper"] in mappers and r["status"] == "ok":
                m[matches.index(r["matching"]), mappers.index(r["mapper"])] = \
                    f(r["correct_posed_pct"])
        im = ax.imshow(np.nan_to_num(m, nan=-1), cmap=BLUES, vmin=0, vmax=100, aspect="auto")
        for i in range(len(matches)):
            for j in range(len(mappers)):
                if np.isnan(m[i, j]):
                    ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, color=GRID))
                    ax.text(j, i, "N/A", ha="center", va="center", color=MUTED, fontsize=9)
                else:
                    ax.text(j, i, f"%{m[i, j]:.0f}", ha="center", va="center", fontsize=11,
                            color="#fcfcfb" if m[i, j] > 55 else INK)
        ax.set_xticks(range(len(mappers)), [MAP_TR[x] for x in mappers], fontsize=8)
        ax.set_yticks(range(len(matches)), [MATCH_TR[x] for x in matches], fontsize=8)
        ax.set_title(EXT[ext][0], fontsize=10, color=INK)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=axes, fraction=0.02, pad=0.02)
    cb.set_label("Doğru pozlanan kare (%)", fontsize=8)
    cb.outline.set_visible(False)
    fig.savefig(OUT / "sekil_h4_2_sfm_matrisi.png", bbox_inches="tight")
    plt.close(fig)


def fig_scale(scale: list[dict]) -> None:
    ns = [349, 1000, 5000, 10000]
    order = ["exhaustive", "vocab_tree", "sequential_loop", "sequential", "vocab_tree_k7"]
    colors = dict(zip(order, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.6), sharey=True)
    for ax, ext in zip(axes, EXT):
        for r in scale:
            if r["extractor"] == ext:
                ax.plot(ns, [f(r[f"hours_{n}"]) for n in ns], color=colors[r["matching"]],
                        linewidth=2, marker="o", markersize=4)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.axhline(24, color=MUTED, linewidth=0.8, linestyle="--")
        ax.text(360, 27, "1 gün", fontsize=7, color=MUTED)
        ax.set_title(EXT[ext][0], fontsize=10)
        ax.set_xlabel("Kare sayısı")
        ax.grid(color=GRID, linewidth=0.6, which="major")
        ax.set_xticks(ns, ["349", "1.000", "5.000", "10.000"], fontsize=8)
    axes[0].set_ylabel("Çıkarma + eşleştirme (saat)")
    handles = [plt.Line2D([], [], color=colors[k], linewidth=2, label=MATCH_TR[k]) for k in order]
    fig.legend(handles=handles, frameon=False, loc="upper center", ncol=5, fontsize=8)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(OUT / "sekil_h4_3_olcek_kestirimi.png")
    plt.close(fig)


def _split(run: str, frame: str):
    img = Image.open(RUNS / run / "renders" / f"{frame}_gt_render.png")
    w = img.width // 2
    return img.crop((0, 0, w, img.height)), img.crop((w, 0, img.width, img.height))


def fig_renders(gs: list[dict]) -> None:
    psnr = {g["run"]: f(g["psnr"]) for g in gs}
    runs = ["sift_exhaustive_incremental", "loma_sequential_incremental",
            "aliked_sequential_loop_incremental", "sift_sequential_global",
            "aliked_exhaustive_incremental"]
    frame = "frame_0200"
    gt = _split(runs[0], frame)[0]
    tiles = [gt] + [_split(r, frame)[1] for r in runs]
    titles = ["Gerçek fotoğraf\n(test karesi)"] + [
        f"{EXT[run_key(r)[0]][0].split(' ')[0]} {MATCH_TR[run_key(r)[1]]}\n+ {run_key(r)[2]}"
        f" · {psnr[r]:.2f} dB".replace(".", ",") for r in runs]
    fig, axes = plt.subplots(1, len(tiles), figsize=(13, 4.4))
    for ax, im, t in zip(axes, tiles, titles):
        ax.imshow(im)
        ax.set_title(t, fontsize=8)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT / "sekil_h4_4_render_karsilastirma.jpg", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_outlier_effect() -> None:
    frame = "frame_0100"
    gt, bad = _split("_aykiri_dahil_sift_exhaustive_global", frame)
    good = _split("sift_exhaustive_global", frame)[1]
    titles = ["Gerçek fotoğraf (test karesi)",
              "6 kopuk kamera eğitimde\nPSNR 14,15 dB",
              "Kopuk kameralar ayıklandı\nPSNR 28,15 dB"]
    fig, axs = plt.subplots(1, 3, figsize=(7.5, 4.4))
    for ax, im, t in zip(axs, (gt, bad, good), titles):
        ax.imshow(im)
        ax.set_title(t, fontsize=9)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT / "sekil_h4_7_kopuk_kamera_etkisi.jpg", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _model(ext: str, match: str, mapper: str):
    """Ana seyrek modelin kamera merkezleri (ad -> konum) ve 3B noktalari."""
    from nerfstudio.data.utils.colmap_parsing_utils import (
        qvec2rotmat, read_images_binary, read_points3D_binary)
    d = WORK / "sfm" / ext / "r1" / match / mapper
    mp = json.loads((d / "map.json").read_text(encoding="utf-8"))
    sp = d / "sparse" / mp["main_model"]
    ims = read_images_binary(str(sp / "images.bin"))
    cams = {im.name: -qvec2rotmat(im.qvec).T @ im.tvec for im in ims.values()}
    pts = np.array([p.xyz for p in read_points3D_binary(str(sp / "points3D.bin")).values()])
    return cams, pts


def fig_camera_layout() -> None:
    """Ust gorunus. Her model referansa (LoMa exhaustive + incremental) RANSAC
    benzerlik donusumuyla hizalanir; dogru modelde kamera yolu ve sira dizilimi
    referansla cakisir, yanlis modelde kayar, katlanir ya da kopar."""
    from collect import umeyama
    ref_c, ref_p = _model("loma", "exhaustive", "incremental")
    names = sorted(ref_c)
    B = np.array([ref_c[n] for n in names])
    mu = B.mean(0)
    # Yukari yon: kamera merkezlerinin en kucuk varyans ekseni (el yuksekligi ~sabit)
    _, _, vt = np.linalg.svd(B - mu, full_matrices=False)
    plane, up = vt[:2], vt[2]
    ref_scale = float(np.median(np.linalg.norm(B - mu, axis=1)))
    lo, hi = np.percentile((ref_p - mu) @ up, [15, 85])  # zemin ve tavan disarida
    lim = np.abs((B - mu) @ plane.T).max(0) * 1.35
    panels = [("loma", "exhaustive", "incremental", "Referans geometri\nLoMa exhaustive + incremental"),
              ("loma", "sequential", "incremental", "LoMa sequential + incremental\n(doğru)"),
              ("aliked", "exhaustive", "incremental", "ALIKED exhaustive + incremental\n(oda katlanmış)"),
              ("sift", "sequential", "global", "SIFT sequential + global\n(yanlış birleşme)")]
    fig, axs = plt.subplots(1, 4, figsize=(13, 4.3))
    rng = np.random.default_rng(0)
    for ax, (ext, match, mapper, title) in zip(axs, panels):
        cams, pts = _model(ext, match, mapper)
        common = [n for n in names if n in cams]
        a = np.array([cams[n] for n in common])
        b = np.array([ref_c[n] for n in common])
        best, keep = -1, None
        for _ in range(2000):
            idx = rng.choice(len(common), 3, replace=False)
            sc, r, t = umeyama(a[idx], b[idx])
            k = np.linalg.norm((sc * (r @ a.T)).T + t - b, axis=1) < 0.05 * ref_scale
            if k.sum() > best:
                best, keep = k.sum(), k
        sc, r, t = umeyama(a[keep], b[keep])

        def tf(x):
            return (sc * (r @ x.T)).T + t

        P = tf(pts)
        h = (P - mu) @ up
        P2 = (P[(h > lo) & (h < hi)] - mu) @ plane.T
        if len(P2) > 40000:
            P2 = P2[rng.choice(len(P2), 40000, replace=False)]
        ax.scatter(P2[:, 0], P2[:, 1], s=0.4, color="#9c9b97", linewidths=0)
        cam_names = sorted(cams)
        A = (tf(np.array([cams[n] for n in cam_names])) - mu) @ plane.T
        ax.scatter(A[:, 0], A[:, 1], c=[int(n[6:10]) for n in cam_names], cmap="viridis",
                   s=7, zorder=3, vmin=1, vmax=349)
        ax.set_xlim(-lim[0], lim[0])
        ax.set_ylim(-lim[1], lim[1])
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=8.5)
        ax.set_xticks([])
        ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(True)
            sp.set_color(GRID)
    sm = plt.cm.ScalarMappable(cmap="viridis", norm=plt.Normalize(1, 349))
    cb = fig.colorbar(sm, ax=axs, fraction=0.012, pad=0.01)
    cb.set_label("Kamera: kare sırası", fontsize=8)
    cb.outline.set_visible(False)
    fig.savefig(OUT / "sekil_h4_6_kamera_yerlesimi.png", bbox_inches="tight")
    plt.close(fig)


def fig_dense_top() -> None:
    from plyfile import PlyData
    v = PlyData.read(str(WORK / "dense" / "sift_exhaustive_incremental" / "fused.ply"))["vertex"]
    xyz = np.stack([v["x"], v["y"], v["z"]], 1)
    rgb = np.stack([v["red"], v["green"], v["blue"]], 1) / 255.0
    rng = np.random.default_rng(0)
    idx = rng.choice(len(xyz), min(400_000, len(xyz)), replace=False)
    xyz, rgb = xyz[idx], rgb[idx]
    c = xyz - np.median(xyz, 0)
    _, _, vt = np.linalg.svd(c[rng.choice(len(c), 50_000)], full_matrices=False)
    h = c @ vt[2]
    lo, hi = np.percentile(h, [5, 95])
    sel = (h > lo + 0.15 * (hi - lo)) & (h < hi - 0.15 * (hi - lo))  # zemin ve tavan disarida
    p = c[sel] @ vt[:2].T
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(p[:, 0], p[:, 1], s=0.15, c=rgb[sel], linewidths=0)
    ax.set_aspect("equal")
    lim = np.percentile(np.abs(p), 99, axis=0) * 1.05
    ax.set_xlim(-lim[0], lim[0])
    ax.set_ylim(-lim[1], lim[1])
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT / "sekil_h4_5_dense_ust_gorunus.jpg", dpi=150)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.iterdir():
        old.unlink()
    sfm, gs = rows("sfm_runs.csv"), rows("gs_summary.csv")
    fig_correct_vs_psnr(sfm, gs)
    fig_correct_matrix(sfm)
    fig_scale(rows("scale_estimate.csv"))
    fig_renders(gs)
    fig_dense_top()
    fig_camera_layout()
    fig_outlier_effect()
    print("\n".join(str(p.relative_to(REPO)) for p in sorted(OUT.iterdir())))


if __name__ == "__main__":
    main()
