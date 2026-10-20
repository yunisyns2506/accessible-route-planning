"""Zayif dokulu yuzeylerde SIFT / ALIKED / LoMa karsilastirmasi (mevcut veriden).

Kullanim:
    python scripts/hafta04/weak_texture.py

Yeni cekim yapilmadan, ayni 349 kare dokusuz alan oranina gore iki gruba
ayrilir ve her cikaricinin zaten uretilmis ciktilari bu iki grupta olculur:

* Dokusuz alan: tam cozunurlukte 32x32 piksellik bloklarin parlaklik standart
  sapmasi < 4 (gri duzey) olan bloklar (bos duvar, tahta, tavan, zemin).
* Zayif dokulu kare: alanin >= %60'i dokusuz. Normal kare: geri kalanlar.

Olcutler (her cikarici icin ayni eslestirme stratejisi kullanilir):
* Kare basina anahtar nokta ve bunlarin dokusuz bloklara dusen orani
  (features.db).
* Komsu karelerle dogrulanmis eslesme: sequential eslestirmede karenin en guclu
  iki komsusuyla dogrulanmis (inlier) eslesme sayisinin ortalamasi.
* Modele giris ve kare basina 3B noktaya donusen gozlem (exhaustive +
  incremental modeli; dokusuz bloklardakiler ayrica).
* 3DGS test PSNR (exhaustive + incremental egitimi; sabit test karelerinden
  zayif dokulu ve normal olanlar).

Cikti: experiments/hafta-04_sinif-01/zayif_doku.csv, zayif_doku_kareler.csv,
docs/figures/hafta-04/sekil_h4_8_zayif_doku.jpg
"""
import csv
import json
import sqlite3
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from common import EXP, FRAMES, REPO, RUNS, WORK  # noqa: E402
from nerfstudio.data.utils.colmap_parsing_utils import read_images_binary  # noqa: E402

BLOCK, STD_T, WEAK_T = 32, 4.0, 0.60
EXTS = {"sift": "SIFT", "aliked": "ALIKED + LightGlue", "loma": "LoMa"}
PAIR_ID = 2147483647


def texture_maps() -> dict[str, np.ndarray]:
    """Kare adi -> dokusuz blok maskesi (blok cozunurlugunde, True = dokusuz)."""
    out = {}
    for f in sorted(FRAMES.glob("*.jpg")):
        g = cv2.imread(str(f), cv2.IMREAD_GRAYSCALE).astype(np.float32)
        h, w = (g.shape[0] // BLOCK) * BLOCK, (g.shape[1] // BLOCK) * BLOCK
        std = g[:h, :w].reshape(h // BLOCK, BLOCK, w // BLOCK, BLOCK).std(axis=(1, 3))
        out[f.name] = std < STD_T
    return out


def in_textureless(mask: np.ndarray, xy: np.ndarray) -> np.ndarray:
    bx = np.clip((xy[:, 0] // BLOCK).astype(int), 0, mask.shape[1] - 1)
    by = np.clip((xy[:, 1] // BLOCK).astype(int), 0, mask.shape[0] - 1)
    return mask[by, bx]


def keypoints(db: Path) -> dict[str, np.ndarray]:
    con = sqlite3.connect(db)
    names = dict(con.execute("select image_id, name from images"))
    out = {}
    for iid, rows, cols, data in con.execute("select image_id, rows, cols, data from keypoints"):
        out[names[iid]] = np.frombuffer(data, np.float32).reshape(rows, cols)[:, :2]
    con.close()
    return out


def neighbour_inliers(db: Path) -> dict[str, float]:
    """Karenin en guclu iki komsusuyla dogrulanmis eslesme sayisi ortalamasi."""
    con = sqlite3.connect(db)
    names = dict(con.execute("select image_id, name from images"))
    per = {n: [] for n in names.values()}
    for pid, rows in con.execute("select pair_id, rows from two_view_geometries"):
        i2 = pid % PAIR_ID
        i1 = (pid - i2) // PAIR_ID
        per[names[i1]].append(rows)
        per[names[i2]].append(rows)
    con.close()
    return {n: float(np.mean(sorted(v, reverse=True)[:2])) if v else 0.0 for n, v in per.items()}


def model_obs(ext: str) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    d = WORK / "sfm" / ext / "r1" / "exhaustive" / "incremental"
    mp = json.loads((d / "map.json").read_text(encoding="utf-8"))
    ims = read_images_binary(str(d / "sparse" / mp["main_model"] / "images.bin"))
    return {im.name: (im.xys, im.point3D_ids >= 0) for im in ims.values()}


def psnr_by_frame(ext: str) -> dict[str, float]:
    p = RUNS / f"{ext}_exhaustive_incremental" / "eval_per_image.json"
    return {r["frame"]: r["psnr"] for r in json.loads(p.read_text(encoding="utf-8"))["per_image"]}


def main() -> None:
    masks = texture_maps()
    frac = {n: float(m.mean()) for n, m in masks.items()}
    weak = {n for n, v in frac.items() if v >= WEAK_T}
    normal = set(frac) - weak
    print(f"zayif dokulu kare: {len(weak)}, normal: {len(normal)}")

    rows, per_frame = [], {n: {"frame": n, "dokusuz_alan": round(frac[n], 3),
                               "grup": "zayif" if n in weak else "normal"} for n in frac}
    for ext in EXTS:
        base = WORK / "sfm" / ext / "r1"
        kps = keypoints(base / "features.db")
        nb = neighbour_inliers(base / "sequential" / "database.db")
        obs = model_obs(ext)
        ps = psnr_by_frame(ext)
        stats = {}
        for name in frac:
            kp = kps.get(name, np.zeros((0, 2), np.float32))
            kp_tl = in_textureless(masks[name], kp) if len(kp) else np.zeros(0, bool)
            reg = name in obs
            tri = tri_tl = 0
            if reg:
                xy, has3d = obs[name]
                tri = int(has3d.sum())
                tri_tl = int((in_textureless(masks[name], xy[has3d])).sum()) if tri else 0
            stats[name] = dict(kp=len(kp), kp_tl=int(kp_tl.sum()), nb=nb.get(name, 0.0),
                               reg=reg, tri=tri, tri_tl=tri_tl, psnr=ps.get(name))
            per_frame[name].update({f"{ext}_kp": len(kp), f"{ext}_kp_dokusuz": int(kp_tl.sum()),
                                    f"{ext}_komsu_eslesme": round(nb.get(name, 0.0), 1),
                                    f"{ext}_modelde": int(reg), f"{ext}_3b_gozlem": tri})

        def mean(group, key):
            v = [stats[n][key] for n in group if stats[n][key] is not None]
            return float(np.mean(v)) if v else None

        def reg_rate(group):
            return 100 * np.mean([stats[n]["reg"] for n in group])

        tl_share = 100 * sum(stats[n]["kp_tl"] for n in weak) / max(1, sum(stats[n]["kp"] for n in weak))
        rows.append({
            "cikarici": ext,
            "kp_zayif": round(mean(weak, "kp")), "kp_normal": round(mean(normal, "kp")),
            "kp_dokusuz_bolgede_pct_zayif": round(tl_share, 1),
            "komsu_eslesme_zayif": round(mean(weak, "nb")),
            "komsu_eslesme_normal": round(mean(normal, "nb")),
            "komsu_eslesme_oran_pct": round(100 * mean(weak, "nb") / mean(normal, "nb")),
            "modele_giris_zayif_pct": round(reg_rate(weak), 1),
            "modele_giris_normal_pct": round(reg_rate(normal), 1),
            "3b_gozlem_zayif": round(mean([n for n in weak if stats[n]["reg"]], "tri")),
            "3b_gozlem_normal": round(mean([n for n in normal if stats[n]["reg"]], "tri")),
            "3b_gozlem_dokusuz_bolgede_zayif": round(mean([n for n in weak if stats[n]["reg"]], "tri_tl"), 1),
            "psnr_zayif_test": round(mean(weak, "psnr"), 2) if mean(weak, "psnr") else None,
            "psnr_normal_test": round(mean(normal, "psnr"), 2),
            "n_zayif_test": sum(stats[n]["psnr"] is not None for n in weak),
        })
    with open(EXP / "zayif_doku.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(EXP / "zayif_doku_kareler.csv", "w", newline="", encoding="utf-8") as f:
        fr = list(per_frame.values())
        w = csv.DictWriter(f, fieldnames=list(fr[0]))
        w.writeheader()
        w.writerows(fr)
    for r in rows:
        print(r)
    figure(masks, sorted(weak, key=lambda n: -frac[n]))


def figure(masks: dict, weak_sorted: list[str]) -> None:
    """Zayif dokulu bir karede uc cikaricinin anahtar noktalari; 3B noktaya
    donusenler koyu, donusmeyenler acik renk."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    obs = {e: model_obs(e) for e in EXTS}
    kps = {e: keypoints(WORK / "sfm" / e / "r1" / "features.db") for e in EXTS}
    # Uc modelin de kaydettigi en dokusuz kare
    name = next(n for n in weak_sorted if all(n in obs[e] for e in EXTS))
    img = cv2.cvtColor(cv2.imread(str(FRAMES / name)), cv2.COLOR_BGR2RGB)
    fig, axes = plt.subplots(1, 3, figsize=(10, 6.2))
    colors = {"sift": "#2a78d6", "aliked": "#eb6834", "loma": "#1baf7a"}
    for ax, e in zip(axes, EXTS):
        ax.imshow(img)
        kp = kps[e][name]
        xy, has3d = obs[e][name]
        ax.scatter(kp[:, 0], kp[:, 1], s=2, color="#fcfcfb", alpha=0.7, linewidths=0)
        ax.scatter(xy[has3d, 0], xy[has3d, 1], s=7, color=colors[e], linewidths=0)
        ax.set_title(f"{EXTS[e]}\n{len(kp)} anahtar nokta, {int(has3d.sum())} tanesi 3B noktada",
                     fontsize=9)
        ax.axis("off")
    print(f"sekil karesi: {name}, dokusuz alan %{100 * masks[name].mean():.0f}")
    fig.tight_layout()
    out = REPO / "docs" / "figures" / "hafta-04" / "sekil_h4_8_zayif_doku.jpg"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("sekil:", out.relative_to(REPO))


if __name__ == "__main__":
    main()
