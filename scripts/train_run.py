"""Bir 3DGS/NeRF egitim kosusu calistirir; sureyi ve tepe VRAM kullanimini olcer.

Kullanim:
    python scripts/train_run.py <kosu_adi> <yontem> <veri_klasoru> <iterasyon> [ek bayraklar...]

Ornek:
    python scripts/train_run.py G1_varsayilan splatfacto data/sinif-01/sfm_exhaustive 15000
    python scripts/train_run.py G2_antialiased splatfacto data/sinif-01/sfm_exhaustive 15000 \
        --pipeline.model.rasterize-mode antialiased

Sonuc: runs/sinif-01/<kosu_adi>/ altinda model, ve run_metrics.json icinde
sure + tepe VRAM kaydi.
"""
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

PYTHON = r"C:\Users\sabod\miniconda3\envs\nerfstudio\python.exe"
OUT_BASE = Path("runs/sinif-01")


def sample_vram(stop: threading.Event, peaks: list) -> None:
    """Egitim boyunca nvidia-smi ile VRAM kullanimini ornekler."""
    while not stop.is_set():
        try:
            out = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=10)
            peaks.append(int(out.stdout.strip().split("\n")[0]))
        except Exception:
            pass
        stop.wait(5)


def main() -> int:
    run_name, method, data_dir, iters = sys.argv[1:5]
    extra = sys.argv[5:]

    out_dir = OUT_BASE / run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

    cmd = [
        PYTHON, "-m", "nerfstudio.scripts.train", method,
        "--data", data_dir,
        "--output-dir", str(out_dir),
        "--experiment-name", run_name,
        "--max-num-iterations", iters,
        "--steps-per-eval-image", "2000",
        "--steps-per-save", str(int(iters)),
        "--viewer.quit-on-train-completion", "True",
    ]
    # cache-images yalnizca splatfacto ailesindeki FullImageDatamanager'da var;
    # nerfacto gibi isin tabanli yontemler VanillaDataManager kullanir.
    if method.startswith("splatfacto"):
        cmd += ["--pipeline.datamanager.cache-images", "cpu"]
    cmd += extra

    log_path = out_dir / "train_log.txt"
    print(f"[{run_name}] {method} baslatiliyor")
    print(" ".join(cmd))

    peaks: list = []
    stop = threading.Event()
    watcher = threading.Thread(target=sample_vram, args=(stop, peaks),
                               daemon=True)
    watcher.start()

    t0 = time.time()
    with open(log_path, "w", encoding="utf-8", errors="replace") as log:
        proc = subprocess.run(cmd, env=env, stdout=log,
                              stderr=subprocess.STDOUT, text=True)
    elapsed = time.time() - t0
    stop.set()
    watcher.join(timeout=10)

    metrics = {
        "run": run_name,
        "method": method,
        "data": data_dir,
        "iterations": int(iters),
        "extra_flags": extra,
        "elapsed_minutes": round(elapsed / 60, 2),
        "peak_vram_mib": max(peaks) if peaks else None,
        "vram_samples": len(peaks),
        "return_code": proc.returncode,
    }
    (out_dir / "run_metrics.json").write_text(json.dumps(metrics, indent=2),
                                              encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
