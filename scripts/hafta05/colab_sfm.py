"""Hafta 5 SfM hattı (Colab, L4): üç yöntem, aşama aşama ölçümlü.

Yöntemler:
    loma + sequential_loop + incremental
    loma + sequential_loop + hierarchical (leaf=250)
    sift + exhaustive      + incremental

LoMa için döngü tespiti: COLMAP 4.2.1'in vocab_tree_builder komutu tanımlayıcı
boyutunu sabit 128 aldığından 256 boyutlu LoMa'da çöküyordu (hafta 4). Kütüphane
256 boyutu desteklediği için komut, boyutu veritabanından alacak şekilde yamalandı
(src/colmap/exe/vocab_tree.cc, tek satır). Sözlük ağacı bu çekimin LoMa
tanımlayıcılarından kurulur (400 bin rastgele tanımlayıcı, 8.192 görsel kelime) ve
sequential eşleştirmede her 10 karede 50 adayla döngü tespiti yapılır. Böylece
video sonunda başlangıca dönülen bölüm ilk karelere bağlanır.

Özellik çıkarma çıkarıcı başına bir kez yapılır; her eşleştirme bu veritabanının
kopyası üzerinde, her mapper ilgili eşleştirmenin veritabanı üzerinde koşar.
Tüm kareler (test kareleri dahil) SfM'e girer; test kareleri yalnız 3DGS
eğitiminden çıkarılır. Her aşamada süre, tepe RAM ve tepe VRAM kaydedilir;
tamamlanmış aşamalar yeniden koşulmaz. Her aşamadan sonra sonuçlar Drive'a
kopyalanır.

Kullanım: python colab_sfm.py A   (LoMa: çıkarma, sözlük ağacı, eşleştirme, 2 SfM)
          python colab_sfm.py C   (SIFT exhaustive + incremental)
"""
import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import threading
import time
from pathlib import Path

import psutil

COLMAP = "/content/colmap/bin/colmap"
WORK = Path("/content/work")
FRAMES = WORK / "frames_1080"
SFM = WORK / "sfm"
DRIVE = Path("/content/drive/MyDrive/hafta5_derslik4")
LOMA_TREE = SFM / "loma" / "vocab_tree_loma_8192.bin"
SEED = ["--default_random_seed", "1"]

# LoMa modelleri COLMAP varsayılanı olarak ilk kullanımda indirilir (SHA256 doğrulamalı).
EXTRACTORS = {
    "loma": {"extract": ["--FeatureExtraction.type", "LOMA_B"],
             "match": ["--FeatureMatching.type", "LOMA_B"]},
    "sift": {"extract": ["--FeatureExtraction.type", "SIFT"],
             "match": ["--FeatureMatching.type", "SIFT_BRUTEFORCE"]},
}
BLOCKS = {
    "A": ("loma", {"sequential_loop": ["incremental", "hierarchical_leaf250"]}),
    "C": ("sift", {"exhaustive": ["incremental"]}),
}
MATCHERS = {"exhaustive": ("exhaustive_matcher", []),
            "sequential_loop": ("sequential_matcher",
                                ["--SequentialMatching.loop_detection", "1",
                                 "--SequentialMatching.vocab_tree_path", str(LOMA_TREE),
                                 "--SequentialMatching.loop_detection_period", "10",
                                 "--SequentialMatching.loop_detection_num_images", "50"])}
MAPPERS = {"incremental": ("mapper", []),
           "hierarchical_leaf250": ("hierarchical_mapper",
                                    ["--HierarchicalMapper.leaf_max_num_images", "250"])}


def tool_env() -> dict:
    """ONNX Runtime (CUDA 12) için pip'teki nvidia-*-cu12 kütüphanelerini yola ekler."""
    env = dict(os.environ)
    import site
    libs = []
    for sp in site.getsitepackages():
        nv = Path(sp) / "nvidia"
        if nv.is_dir():
            libs += [str(d / "lib") for d in sorted(nv.iterdir()) if (d / "lib").is_dir()]
    env["LD_LIBRARY_PATH"] = ":".join(libs + [env.get("LD_LIBRARY_PATH", "")])
    return env


def gpu_mem_used():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used",
                              "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10)
        return int(out.stdout.strip().split("\n")[0])
    except Exception:
        return None


class ResourceMonitor:
    """Süreç ağacının tepe RAM'ini ve GPU'nun tepe VRAM'ini 1 sn aralıkla örnekler."""

    def __init__(self, interval: float = 1.0):
        self.interval, self.vram_base = interval, gpu_mem_used()
        self.vram_peak = self.rss_peak = 0
        self._stop, self._pid = threading.Event(), None

    def _loop(self):
        while not self._stop.is_set():
            v = gpu_mem_used()
            if v is not None:
                self.vram_peak = max(self.vram_peak, v)
            try:
                p = psutil.Process(self._pid)
                rss = sum(q.memory_info().rss for q in [p] + p.children(recursive=True))
                self.rss_peak = max(self.rss_peak, rss)
            except psutil.Error:
                pass
            self._stop.wait(self.interval)

    def run(self, cmd: list, log: Path) -> tuple[int, float]:
        log.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        with open(log, "w") as f:
            f.write(" ".join(map(str, cmd)) + "\n\n")
            f.flush()
            proc = subprocess.Popen(cmd, env=tool_env(), stdout=f, stderr=subprocess.STDOUT)
            self._pid = proc.pid
            th = threading.Thread(target=self._loop, daemon=True)
            th.start()
            rc = proc.wait()
        sec = time.time() - t0
        self._stop.set()
        th.join(timeout=15)
        return rc, sec

    def summary(self) -> dict:
        return {"peak_ram_mib": round(self.rss_peak / 2**20),
                "peak_vram_mib": self.vram_peak or None, "vram_base_mib": self.vram_base}


def read_json(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def write_json(p: Path, d: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def sync_drive() -> None:
    """Veritabanları dışındaki tüm çıktıları (modeller, json, log) Drive'a kopyalar."""
    if Path("/content/drive/MyDrive").is_dir():
        subprocess.run(["rsync", "-a", "--exclude", "*.db", "--exclude", "*.db-*",
                        f"{SFM}/", f"{DRIVE}/sfm/"], check=False)


def run_stage(out_json: Path, cmd: list, log: Path, extra: dict | None = None) -> dict:
    done = read_json(out_json)
    if done and done.get("return_code") == 0:
        print(f"  atlandı (tamam): {out_json.relative_to(SFM)}", flush=True)
        return done
    print(f"  başladı: {out_json.relative_to(SFM)}  {time.strftime('%H:%M:%S')}", flush=True)
    mon = ResourceMonitor()
    rc, sec = mon.run(cmd, log)
    res = {"return_code": rc, "elapsed_s": round(sec, 1), **mon.summary(), **(extra or {})}
    write_json(out_json, res)
    print(f"  bitti: {out_json.relative_to(SFM)} rc={rc} {sec / 60:.1f} dk "
          f"RAM {res['peak_ram_mib']} MiB VRAM {res['peak_vram_mib']} MiB", flush=True)
    sync_drive()
    if rc != 0:
        raise SystemExit(f"aşama başarısız, log: {log}")
    return res


def db_stats(db: Path) -> dict:
    con = sqlite3.connect(db)
    kp = con.execute("select count(*), avg(rows) from keypoints").fetchone()
    tvg = con.execute("select count(*) from two_view_geometries where rows > 0").fetchone()[0]
    pairs = con.execute("select count(*) from matches").fetchone()[0]
    # Döngü çiftleri: çekim sırasında 10 kareden uzak, doğrulanmış çiftler
    loops = sum(abs(p // 2147483647 - p % 2147483647) > 10 for (p,) in
                con.execute("select pair_id from two_view_geometries where rows > 0"))
    con.close()
    return {"images": kp[0], "mean_keypoints": round(kp[1] or 0, 1),
            "matched_pairs": pairs, "verified_pairs": tvg, "verified_non_sequential_pairs": loops}


def model_stats(sparse: Path) -> dict:
    import pycolmap
    models = []
    for d in sorted(p for p in sparse.iterdir() if p.is_dir()):
        r = pycolmap.Reconstruction(str(d))
        models.append({"model": d.name, "registered": r.num_reg_images(),
                       "points3D": r.num_points3D(),
                       "mean_track_length": round(r.compute_mean_track_length(), 3),
                       "mean_reproj_error_px": round(r.compute_mean_reprojection_error(), 4)})
    models.sort(key=lambda m: -m["registered"])
    return {"n_models": len(models), "models": models}


def extract(ext: str) -> Path:
    base = SFM / ext
    feat_db = base / "features.db"
    run_stage(base / "extract.json",
              [COLMAP, "feature_extractor", "--database_path", feat_db,
               "--image_path", FRAMES, "--ImageReader.single_camera", "1",
               "--ImageReader.camera_model", "OPENCV", *EXTRACTORS[ext]["extract"], *SEED],
              base / "extract.log")
    return feat_db


def build_tree(feat_db: Path) -> None:
    """Bu çekimin LoMa tanımlayıcılarından sözlük ağacı kurar (yamalı vocab_tree_builder)."""
    run_stage(SFM / "loma" / "vocab_tree.json",
              [COLMAP, "vocab_tree_builder", "--database_path", feat_db,
               "--vocab_tree_path", LOMA_TREE, "--num_visual_words", "8192",
               "--max_num_descriptors", "400000", *SEED],
              SFM / "loma" / "vocab_tree.log")


def main(block: str) -> None:
    n_frames = len(list(FRAMES.glob("*.jpg")))
    ext, matchers = BLOCKS[block]
    print(f"== blok {block}: {ext} ({n_frames} kare)", flush=True)
    cfg, base = EXTRACTORS[ext], SFM / ext
    feat_db = extract(ext)
    if "sequential_loop" in matchers:
        build_tree(feat_db)
    for match, mappers in matchers.items():
        mdir = base / match
        db = mdir / "database.db"
        if not read_json(mdir / "match.json") or read_json(mdir / "match.json")["return_code"]:
            mdir.mkdir(parents=True, exist_ok=True)
            shutil.copy(feat_db, db)
        cmd_name, extra = MATCHERS[match]
        run_stage(mdir / "match.json",
                  [COLMAP, cmd_name, "--database_path", db, *cfg["match"], *extra, *SEED],
                  mdir / "match.log")
        write_json(mdir / "db_stats.json", db_stats(db))
        for mapper in mappers:
            pdir = mdir / mapper
            sparse = pdir / "sparse"
            sparse.mkdir(parents=True, exist_ok=True)
            cmd_name, extra = MAPPERS[mapper]
            res = run_stage(pdir / "map.json",
                            [COLMAP, cmd_name, "--database_path", db, "--image_path", FRAMES,
                             "--output_path", sparse, *extra, *SEED],
                            pdir / "map.log")
            if "n_models" not in res:
                res.update(model_stats(sparse))
                res["input_frames"] = n_frames
                write_json(pdir / "map.json", res)
                best = res["models"][0] if res["models"] else {}
                print(f"    {ext}/{match}/{mapper}: {res['n_models']} model, en büyüğü "
                      f"{best.get('registered')} / {n_frames} kare", flush=True)
                sync_drive()
    print(f"BLOK {block} BİTTİ", time.strftime("%H:%M:%S"), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("block", choices=list(BLOCKS))
    main(ap.parse_args().block)
