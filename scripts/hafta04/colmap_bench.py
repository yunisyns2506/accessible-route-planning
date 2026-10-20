"""COLMAP 4.2.1 yontem karsilastirmasi: bir ozellik cikarici icin tum
eslestirme stratejisi x SfM yontemi kombinasyonlarini kosar ve olcer.

Kullanim:
    python scripts/hafta04/colmap_bench.py <sift|aliked|loma> [--only MATCH ...]

Her kombinasyon BIR KEZ kosulur (sabit tohum: --default_random_seed 1). Ayni
sonucu verecek tekrarlar yapilmaz; ozellik cikarma bir kez yapilir ve tum
eslestirmeler onu, her mapper da ilgili eslestirmenin veritabanini kullanir.

Eslestirme: exhaustive (karesel; bina olceginde uygulanamaz, kalite ust siniri
olarak tutulur), sequential, sequential_loop (sequential + sozluk agaciyla
dongu tespiti; video ile bina gezintisinde gercekci secenek), vocab_tree.
SfM: incremental, global, hierarchical_leaf100. Varsayilan hierarchical mapper
500 karenin altinda sahneyi bolmedigi icin bu veride incremental ile ayni isi
yapar; bu nedenle yaprak boyutu 100'e indirilerek sahnenin gercekten bolunup
birlestirildigi (bina olcegindeki davranisin kucuk ornegi) hali kosulur.

Her asama icin sure, tepe RAM ve tepe VRAM kaydedilir; mapper ciktilarinin
model istatistikleri cikarilir. Tamamlanmis asamalar yeniden kosulmaz.

Cikti: data/sinif-01/hafta-04/sfm/<cikarici>/r1/<eslestirme>/database.db
       data/sinif-01/hafta-04/sfm/<cikarici>/r1/<eslestirme>/<mapper>/
("r1" tek koşuyu belirtir; ilk denemede SIFT icin baslatilan varsayilan
hierarchical sonuclari da bu klasorde kalir ve incremental ile esdegerligi
raporda tek satirla belirtilir.)
"""
import argparse
import re
import shutil
import sqlite3
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from common import (COLMAP, FRAMES, MODELS, PYCOLMAP, PYTHON, WORK,  # noqa: E402
                    ResourceMonitor, read_json, tool_env, write_json)
from nerfstudio.data.utils.colmap_parsing_utils import (  # noqa: E402
    read_images_binary, read_points3D_binary)

# Her cikarici kendi varsayilan eslestiricisiyle eslenir (hoca notu:
# ALIKED + LightGlue). Diger tum COLMAP ayarlari varsayilandir.
EXTRACTORS = {
    "sift": {
        "extract": ["--FeatureExtraction.type", "SIFT"],
        "match": ["--FeatureMatching.type", "SIFT_BRUTEFORCE"],
        "vocab_tree": MODELS / "vocab_tree_faiss_flickr100K_words32K.bin",
    },
    "aliked": {
        "extract": ["--FeatureExtraction.type", "ALIKED_N16ROT",
                    "--AlikedExtraction.n16rot_model_path", str(MODELS / "aliked-n16rot.onnx")],
        "match": ["--FeatureMatching.type", "ALIKED_LIGHTGLUE",
                  "--AlikedMatching.lightglue_model_path", str(MODELS / "aliked-lightglue.onnx")],
        "vocab_tree": MODELS / "vocab_tree_faiss_flickr100K_words64K_aliked_n16rot.bin",
    },
    "loma": {
        "extract": ["--FeatureExtraction.type", "LOMA_B",
                    "--LomaExtraction.detector_model_path", str(MODELS / "loma_detector.onnx"),
                    "--LomaExtraction.descriptor_model_path",
                    str(MODELS / "loma_descriptor_dedode_g.onnx")],
        "match": ["--FeatureMatching.type", "LOMA_B",
                  "--LomaMatching.b_model_path", str(MODELS / "loma_matcher_B.onnx")],
        # LoMa icin resmi sozluk agaci yok; ayni veritabanindan kurulur.
        "vocab_tree": None,
    },
}

MATCHERS = {"exhaustive": ("exhaustive_matcher", []),
            "sequential": ("sequential_matcher", []),
            "sequential_loop": ("sequential_matcher", ["--SequentialMatching.loop_detection", "1"]),
            "vocab_tree": ("vocab_tree_matcher", []),
            # Bina olcegi vekili: varsayilan 100 aday, 349 karede verinin %29'u
            # (neredeyse exhaustive). 5.000 karelik binada 100 aday ~%2'ye denk
            # gelir; ayni orani burada uretmek icin 349 x 0,02 ~ 7 aday.
            "vocab_tree_k7": ("vocab_tree_matcher", ["--VocabTreeMatching.num_images", "7"])}
TREE_OPTION = {"sequential_loop": "--SequentialMatching.vocab_tree_path",
               "vocab_tree": "--VocabTreeMatching.vocab_tree_path",
               "vocab_tree_k7": "--VocabTreeMatching.vocab_tree_path"}
MAPPERS = {"incremental": ("mapper", []),
           "global": ("global_mapper", []),
           "hierarchical_leaf100": ("hierarchical_mapper",
                                    ["--HierarchicalMapper.leaf_max_num_images", "100"])}


def failure_reason(log: Path) -> str:
    """Log'daki son hata satirini kisa neden olarak dondurur."""
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    errs = [ln for ln in lines if re.match(r"^[EF]\d{8}", ln) or "rror" in ln]
    return (errs[-1] if errs else (lines[-1] if lines else "log bos"))[-300:]


def db_stats(db: Path) -> dict:
    con = sqlite3.connect(db)
    kp = con.execute("select count(*), avg(rows), sum(rows) from keypoints").fetchone()
    tvg = con.execute("select count(*), sum(rows) from two_view_geometries "
                      "where rows > 0").fetchone()
    pairs = con.execute("select count(*) from matches").fetchone()[0]
    con.close()
    return {"images": kp[0], "mean_keypoints": round(kp[1] or 0, 1),
            "total_keypoints": kp[2], "matched_pairs": pairs,
            "verified_pairs": tvg[0], "verified_inlier_matches": tvg[1] or 0}


def model_stats(model_dir: Path) -> dict:
    images = read_images_binary(str(model_dir / "images.bin"))
    points = read_points3D_binary(str(model_dir / "points3D.bin"))
    track = np.array([len(p.image_ids) for p in points.values()])
    err = np.array([p.error for p in points.values()])
    obs_per_img = [int((im.point3D_ids >= 0).sum()) for im in images.values()]
    return {
        "model": model_dir.name,
        "registered_images": len(images),
        "registered_names": sorted(im.name for im in images.values()),
        "points3D": len(points),
        "mean_track_length": round(float(track.mean()), 3) if len(track) else 0.0,
        "median_track_length": float(np.median(track)) if len(track) else 0.0,
        "mean_reproj_error_px": round(float(err.mean()), 4) if len(err) else 0.0,
        "mean_obs_per_image": round(float(np.mean(obs_per_img)), 1) if obs_per_img else 0.0,
    }


def run_stage(out_json: Path, cmd: list, log: Path, extra: dict | None = None,
              env: dict | None = None) -> dict:
    done = read_json(out_json)
    if done and done.get("return_code") == 0:
        print(f"  atlandi (tamam): {out_json.parent.name}/{out_json.name}")
        return done
    mon = ResourceMonitor()
    rc, sec = mon.run(cmd, log, env)
    res = {"return_code": rc, "elapsed_s": round(sec, 1), **mon.summary(), **(extra or {})}
    if rc != 0:
        # Windows'ta cokme kodlari buyuk isaretsiz sayi olarak doner (or. 0xC0000409)
        res["failure"] = (f"surec coktu (0x{rc:08X}); " if rc > 255 else "") + failure_reason(log)
    write_json(out_json, res)
    print(f"  {out_json.parent.name}/{out_json.stem}: rc={rc} {sec / 60:.2f} dk "
          f"RAM {res['peak_ram_mib']} MiB VRAM {res['peak_vram_mib']} MiB")
    return res


def own_vocab_tree(base: Path, feat_db: Path) -> tuple[Path | None, float | None]:
    """Resmi agaci olmayan cikarici (LoMa) icin ayni veriden sozluk agaci kurar.

    COLMAP'in vocab_tree_builder komutu yalnizca 128 boyutlu tanimlayici
    destekler; LoMa 256 boyutlu oldugu icin agac pycolmap ile kurulur
    (build_vocab_tree.py, ayarlar komutun varsayilanlariyla ayni).
    """
    tree = base / "vocab_tree_own.bin"
    env = tool_env()
    env["PYTHONPATH"] = PYCOLMAP
    vb = run_stage(base / "vocab_build.json",
                   [PYTHON, str(Path(__file__).parent / "build_vocab_tree.py"), feat_db, tree],
                   base / "vocab_build.log", env=env)
    if vb["return_code"] != 0:
        return None, None
    return tree, vb["elapsed_s"]


def match_stage(cfg: dict, base: Path, feat_db: Path, mname: str) -> Path | None:
    """Eslestirmeyi bir kez yapar; veritabani yolunu dondurur."""
    mdir = base / mname
    mdir.mkdir(exist_ok=True)
    db = mdir / "database.db"
    m_json = mdir / "match.json"
    done = read_json(m_json)
    if done and done.get("return_code") == 0:
        return db
    if done and done.get("status") == "N/A":
        return None
    cmd_name, extra_args = MATCHERS[mname]
    extra_args, extra_info = list(extra_args), {}
    if mname in TREE_OPTION:
        tree = cfg["vocab_tree"]
        if tree is None:
            tree, build_s = own_vocab_tree(base, feat_db)
            if tree is None:
                write_json(m_json, {"return_code": -1, "status": "N/A",
                                    "failure": "vocab_tree_builder: " +
                                    (read_json(base / "vocab_build.json") or {}).get("failure", "")})
                print(f"  {mname} N/A (sozluk agaci kurulamadi)")
                return None
            extra_info["vocab_tree_build_s"] = build_s
        extra_args += [TREE_OPTION[mname], tree]
        extra_info["vocab_tree"] = Path(tree).name
    shutil.copy2(feat_db, db)
    print(f"  eslestirme: {mname}")
    mt = run_stage(m_json, [COLMAP, cmd_name, "--database_path", db, *cfg["match"],
                            *extra_args, "--default_random_seed", "1"],
                   mdir / "match.log", extra_info)
    if mt["return_code"] != 0:
        return None
    mt["db"] = db_stats(db)
    write_json(m_json, mt)
    return db


def map_stage(db: Path, pdir: Path, frames: Path, pname: str, n_input: int) -> None:
    sparse = pdir / "sparse"
    p_json = pdir / "map.json"
    done = read_json(p_json)
    if done and done.get("return_code") == 0 and "models" in done:
        return
    shutil.rmtree(sparse, ignore_errors=True)
    sparse.mkdir(parents=True, exist_ok=True)
    cmd_name, extra_args = MAPPERS[pname]
    print(f"  {pdir.parent.name} + {pname}")
    mp = run_stage(p_json, [COLMAP, cmd_name, "--database_path", db, "--image_path", frames,
                            "--output_path", sparse, *extra_args,
                            "--default_random_seed", "1"],
                   pdir / "map.log")
    models = sorted(d for d in sparse.iterdir() if (d / "images.bin").exists())
    stats = [model_stats(d) for d in models]
    if not stats:
        mp["status"] = "N/A"
        mp.setdefault("failure", failure_reason(pdir / "map.log"))
    else:
        main_m = max(stats, key=lambda s: s["registered_images"])
        mp.update({
            "status": "ok",
            "input_frames": n_input,
            "n_models": len(stats),
            "main_model": main_m["model"],
            "registered_main": main_m["registered_images"],
            "registration_rate_main": round(main_m["registered_images"] / n_input, 4),
            "registered_any": len({n for s in stats for n in s["registered_names"]}),
            "points3D": main_m["points3D"],
            "mean_track_length": main_m["mean_track_length"],
            "median_track_length": main_m["median_track_length"],
            "mean_reproj_error_px": main_m["mean_reproj_error_px"],
            "mean_obs_per_image": main_m["mean_obs_per_image"],
        })
    mp["models"] = stats
    write_json(p_json, mp)
    if stats:
        print(f"    modeller={len(stats)} ana={mp['registered_main']}/{n_input} "
              f"nokta={mp['points3D']} iz={mp['mean_track_length']} "
              f"hata={mp['mean_reproj_error_px']} px")
    else:
        print(f"    N/A: {mp['failure'][:150]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("extractor", choices=EXTRACTORS)
    ap.add_argument("--only", choices=MATCHERS, nargs="*")
    ap.add_argument("--frames", type=Path, default=FRAMES, help="deneme icin baska kare klasoru")
    ap.add_argument("--work", type=Path, default=WORK / "sfm", help="deneme icin baska cikti koku")
    args = ap.parse_args()

    cfg = EXTRACTORS[args.extractor]
    frames = args.frames
    base = args.work / args.extractor / "r1"
    base.mkdir(parents=True, exist_ok=True)
    n_input = len(list(frames.glob("*.jpg")))

    # 1) Ozellik cikarma: cikarici basina bir kez
    feat_db = base / "features.db"
    ex_json = base / "extract.json"
    if not (read_json(ex_json) or {}).get("return_code") == 0:
        feat_db.unlink(missing_ok=True)
    print(f"[{args.extractor}] ozellik cikarma")
    ex = run_stage(ex_json, [COLMAP, "feature_extractor", "--database_path", feat_db,
                             "--image_path", frames, "--ImageReader.single_camera", "1",
                             "--ImageReader.camera_model", "OPENCV", *cfg["extract"],
                             "--default_random_seed", "1"],
                   base / "extract.log")
    if ex["return_code"] != 0:
        return 1
    if "db" not in ex:
        ex["db"] = db_stats(feat_db)
        write_json(ex_json, ex)

    # 2) Eslestirme ve 3) mapper
    for mname in args.only or MATCHERS:
        print(f"[{args.extractor}] {mname}")
        db = match_stage(cfg, base, feat_db, mname)
        if db is None:
            continue
        for pname in MAPPERS:
            map_stage(db, base / mname / pname, frames, pname, n_input)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
