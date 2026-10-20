"""Hafta 4 koşularinin olcumlerini toplar ve karsilastirma tablolarini yazar.

Kullanim:
    python scripts/hafta04/collect.py

Ciktilar (experiments/hafta-04_sinif-01/):
    sfm_runs.csv         her SfM kombinasyonu (tek koşu)
    scale_estimate.csv   olculen birim maliyetlerle bina olcegi sure kestirimi
    gs_summary.csv       3DGS egitimleri; hem kendi test kareleri hem ortak kesisim
    gs_common_frames.txt ortak kesisimde kullanilan test kareleri

Geometrik dogruluk: her modelin kamera pozlari referans modele (LoMa +
exhaustive + incremental; 349 karenin tamamini kapsar, SIFT + exhaustive +
incremental ile bagimsiz olarak ortusur) RANSAC benzerlik donusumuyla
hizalanir. "Dogru pozlanan kare" = ana modelde olup referansla olcegin %5'i
icinde ortusen kare sayisi; orani 349 kareye gore verilir (kayit + dogruluk
tek sayida). Ayrica donme ve kamera merkezi hatalarinin medyan / %90 dilimi.
"""
import csv
import statistics as st
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from common import COLMAP, EXP, RUNS, WORK, read_json, tool_env, write_json  # noqa: E402
from nerfstudio.data.utils.colmap_parsing_utils import (  # noqa: E402
    qvec2rotmat, read_images_binary)

SFM = WORK / "sfm"
EXTRACTORS = ["sift", "aliked", "loma"]
MATCHERS = ["exhaustive", "sequential", "sequential_loop", "vocab_tree", "vocab_tree_k7"]
MAPPERS = ["incremental", "global", "hierarchical_leaf100", "hierarchical"]
SCALE_N = [349, 1000, 5000, 10000]
REFERENCE = ("loma", 1, "exhaustive", "incremental")  # (cikarici, koşu, eslestirme, mapper)


def model_dir(ext, rep, match, mapper) -> Path | None:
    p = SFM / ext / f"r{rep}" / match / mapper
    mp = read_json(p / "map.json")
    if not mp or mp.get("status") != "ok":
        return None
    return p / "sparse" / mp["main_model"]


def scene_scale(model: Path) -> float:
    ims = read_images_binary(str(model / "images.bin"))
    centers = np.array([-qvec2rotmat(im.qvec).T @ im.tvec for im in ims.values()])
    return float(np.median(np.linalg.norm(centers - centers.mean(0), axis=1)))


def outlier_count(model: Path) -> int:
    """make_ns_data.py ile ayni kural: en yakin 3 kameraya ortalama uzakligi
    medyanin 10 katini asan (sahneden kopuk) kamera sayisi."""
    from scipy.spatial import cKDTree
    ims = read_images_binary(str(model / "images.bin"))
    c = np.array([-qvec2rotmat(im.qvec).T @ im.tvec for im in ims.values()])
    d, _ = cKDTree(c).query(c, k=4)
    nn = d[:, 1:].mean(1)
    return int((nn > 10 * np.median(nn)).sum())


def poses(model: Path) -> dict:
    ims = read_images_binary(str(model / "images.bin"))
    return {im.name: (qvec2rotmat(im.qvec), -qvec2rotmat(im.qvec).T @ im.tvec)
            for im in ims.values()}


def umeyama(x: np.ndarray, y: np.ndarray):
    """x -> y benzerlik donusumu (olcek, donme, oteleme), en kucuk kareler."""
    mx, my = x.mean(0), y.mean(0)
    u, d, vt = np.linalg.svd((y - my).T @ (x - mx) / len(x))
    s_ = np.eye(3)
    if np.linalg.det(u @ vt) < 0:
        s_[2, 2] = -1
    r = u @ s_ @ vt
    scale = np.trace(np.diag(d) @ s_) / (x - mx).var(0).sum()
    return scale, r, my - scale * r @ mx


def compare(m1: Path, m2: Path, out: Path) -> dict | None:
    """m2'nin kamera pozlarini m1'e (referans) gore karsilastirir (onbellekli).

    Ortak karelerin kamera merkezleri RANSAC ile kestirilen benzerlik
    donusumuyla hizalanir (aykiri kameralara dayanikli). aligned_pct, referansla
    olcegin %5'i icinde ortusen kamera oranidir; dusukse model referanstan
    farkli bir geometri kurmustur (or. katlanma). Merkez hatasi referans
    kameralarin merkezden medyan uzakligina bolunerek yuzde verilir.
    Not: COLMAP model_comparer farkli ozellik turlerinden (or. SIFT - ALIKED)
    gelen modelleri hizalayamadigi icin bu yontem kullanilir.
    """
    cache = out / "compare.json"
    if cache.exists() and "aligned_count" in (read_json(cache) or {}):
        return read_json(cache)
    ref, q = poses(m1), poses(m2)
    common = sorted(set(ref) & set(q))
    if len(common) < 10:
        res = {"ok": False, "common_images": len(common)}
    else:
        a = np.array([q[k][1] for k in common])
        b = np.array([ref[k][1] for k in common])
        ref_scale = float(np.median(np.linalg.norm(b - b.mean(0), axis=1)))
        # RANSAC: 3 kameralik orneklerden benzerlik donusumu; esik referans
        # olceginin %5'i. En cok kamerayi aciklayan donusum, icerdekilerle
        # yeniden kestirilir. Sabit tohum: sonuc tekrarlanabilir.
        rng = np.random.default_rng(0)
        best = None
        for _ in range(2000):
            idx = rng.choice(len(common), 3, replace=False)
            sc, r, t = umeyama(a[idx], b[idx])
            err = np.linalg.norm((sc * (r @ a.T)).T + t - b, axis=1)
            n_in = int((err < 0.05 * ref_scale).sum())
            if best is None or n_in > best:
                best, keep = n_in, err < 0.05 * ref_scale
        sc, r, t = umeyama(a[keep], b[keep])
        err = np.linalg.norm((sc * (r @ a.T)).T + t - b, axis=1)
        scale = ref_scale
        rot = np.array([np.degrees(np.arccos(np.clip(
            (np.trace(ref[k][0] @ (q[k][0] @ r.T).T) - 1) / 2, -1, 1))) for k in common])
        res = {"ok": True, "common_images": len(common),
               "median_rot_deg": round(float(np.median(rot)), 3),
               "p90_rot_deg": round(float(np.percentile(rot, 90)), 3),
               "median_center_pct": round(100 * float(np.median(err)) / scale, 3),
               "p90_center_pct": round(100 * float(np.percentile(err, 90)) / scale, 3),
               "aligned_pct": round(100 * float(keep.mean()), 1),
               "aligned_count": int(keep.sum())}
    write_json(cache, res)
    return res


def verified_pairs(db: Path, min_inliers: int) -> set[int]:
    import sqlite3
    con = sqlite3.connect(db)
    ids = {r[0] for r in con.execute(
        "select pair_id from two_view_geometries where rows >= ?", (min_inliers,))}
    con.close()
    return ids


def pair_recall(ext: str, match: str) -> dict:
    """Eslestirme stratejisinin, exhaustive'in dogruladigi ciftlerin yuzde kacini
    buldugu. 'Guclu' ciftler (>= 100 inlier) SfM'i tasiyan baglantilardir."""
    base = SFM / ext / "r1"
    exh, db = base / "exhaustive" / "database.db", base / match / "database.db"
    if match == "exhaustive" or not exh.exists() or not db.exists():
        return {}
    out = {}
    for name, k in (("pair_recall", 15), ("strong_pair_recall", 100)):
        ref = verified_pairs(exh, k)
        out[name] = round(len(ref & verified_pairs(db, k)) / len(ref), 4) if ref else None
    return out


def stage(p: Path) -> dict:
    return read_json(p) or {}


def sfm_rows() -> list[dict]:
    ref = model_dir(*REFERENCE)
    rows = []
    for ext in EXTRACTORS:
        base = SFM / ext / "r1"
        ex = stage(base / "extract.json")
        if not ex:
            continue
        for match in MATCHERS:
            mt = stage(base / match / "match.json")
            for mapper in MAPPERS:
                mp = stage(base / match / mapper / "map.json")
                if not mt or (mt.get("return_code") == 0 and not mp):
                    continue
                status = mp.get("status") or mt.get("status") or "N/A"
                row = {
                    "extractor": ext, "matching": match, "mapper": mapper,
                    "status": status,
                    "failure": (mp.get("failure") or mt.get("failure") or "")[:200]
                    if status != "ok" else "",
                    "mean_keypoints": ex.get("db", {}).get("mean_keypoints"),
                    "matched_pairs": mt.get("db", {}).get("matched_pairs"),
                    "verified_pairs": mt.get("db", {}).get("verified_pairs"),
                    "extract_s": ex.get("elapsed_s"),
                    "match_s": round((mt.get("elapsed_s") or 0) + (mt.get("vocab_tree_build_s") or 0), 1)
                    if mt.get("elapsed_s") is not None else None,
                    "map_s": mp.get("elapsed_s"),
                }
                parts = [row[k] for k in ("extract_s", "match_s", "map_s")]
                row.update(pair_recall(ext, match))
                row["total_min"] = round(sum(parts) / 60, 2) if None not in parts else None
                row["peak_ram_mib"] = max((s.get("peak_ram_mib") or 0) for s in (ex, mt, mp))
                row["peak_vram_mib"] = max((s.get("peak_vram_mib") or 0) for s in (ex, mt, mp))
                for k in ("input_frames", "n_models", "registered_main",
                          "registration_rate_main", "registered_any", "points3D",
                          "mean_track_length", "median_track_length",
                          "mean_reproj_error_px", "mean_obs_per_image"):
                    row[k] = mp.get(k)
                row.update({"ref_common": None, "ref_rot_deg": None, "ref_center_pct": None})
                m = model_dir(ext, 1, match, mapper)
                row["outlier_cameras"] = outlier_count(m) if m is not None else None
                row["correct_posed"] = None
                if m is not None and m == ref:
                    row["correct_posed"] = row["registered_main"]
                if m is not None and ref is not None and m != ref:
                    c = compare(ref, m, m.parent.parent / "cmp_ref_loma")
                    if c.get("ok"):
                        row["correct_posed"] = c["aligned_count"]
                    if c.get("ok"):
                        row.update({"ref_common": c["common_images"],
                                    "ref_rot_deg": c["median_rot_deg"],
                                    "ref_rot_p90_deg": c["p90_rot_deg"],
                                    "ref_center_pct": c["median_center_pct"],
                                    "ref_center_p90_pct": c["p90_center_pct"],
                                    "ref_aligned_pct": c["aligned_pct"]})
                row["correct_posed_pct"] = (round(100 * row["correct_posed"] / row["input_frames"], 1)
                                            if row["correct_posed"] is not None else None)
                rows.append(row)
    return rows


def scale_rows() -> list[dict]:
    """Cikarma ve eslestirme suresini kare sayisina gore kestirir.

    Cikarma kare basina sabit maliyetlidir (dogrusal). Eslestirmede cift basina
    maliyet olculur; cift sayisi exhaustive icin N(N-1)/2, diger stratejilerde
    kare basina sabit (olculen cift / kare) kabul edilir. Mapper suresi kare
    sayisiyla dogrusal olmayan bicimde buyudugu icin kestirilmez.
    """
    out = []
    for ext in EXTRACTORS:
        base = SFM / ext / "r1"
        ex = stage(base / "extract.json")
        if not ex.get("db"):
            continue
        n0 = ex["db"]["images"]
        per_img = ex["elapsed_s"] / n0
        for match in MATCHERS:
            mt = stage(base / match / "match.json")
            if not mt.get("db") or not mt["db"]["matched_pairs"]:
                continue
            pairs0 = mt["db"]["matched_pairs"]
            per_pair = mt["elapsed_s"] / pairs0
            row = {"extractor": ext, "matching": match, "measured_pairs": pairs0,
                   "ms_per_pair": round(1000 * per_pair, 2),
                   "s_per_image_extract": round(per_img, 3)}
            for n in SCALE_N:
                pairs = n * (n - 1) / 2 if match == "exhaustive" else pairs0 / n0 * n
                row[f"pairs_{n}"] = int(pairs)
                row[f"hours_{n}"] = round((per_img * n + per_pair * pairs) / 3600, 2)
            out.append(row)
    return out


def gs_rows() -> tuple[list[dict], list[str]]:
    # "_" ile baslayan klasorler (or. aykiri kameralar ayiklanmadan egitilen
    # ilk deneme) karsilastirmaya girmez; raporda ayrica anlatilir.
    runs = sorted(p.parent for p in RUNS.glob("[!_]*/eval_per_image.json")) if RUNS.exists() else []
    per = {r.name: read_json(r / "eval_per_image.json")["per_image"] for r in runs}
    common = sorted(set.intersection(*[{x["frame"] for x in v} for v in per.values()])) \
        if per else []
    rows = []
    for r in runs:
        s = read_json(r / "summary.json") or {}
        cm = [x for x in per[r.name] if x["frame"] in common]
        for k in ("psnr", "ssim", "lpips"):
            s[f"common_{k}"] = round(st.mean(x[k] for x in cm), 4) if cm else None
        s["n_common"] = len(cm)
        rows.append(s)
    return rows, common


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"yazildi: {path.relative_to(EXP.parent.parent)} ({len(rows)} satir)")


def main() -> None:
    EXP.mkdir(parents=True, exist_ok=True)
    rows = sfm_rows()
    write_csv(EXP / "sfm_runs.csv", rows)
    write_csv(EXP / "scale_estimate.csv", scale_rows())
    g, common = gs_rows()
    write_csv(EXP / "gs_summary.csv", g)
    if common:
        (EXP / "gs_common_frames.txt").write_text("\n".join(common) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
