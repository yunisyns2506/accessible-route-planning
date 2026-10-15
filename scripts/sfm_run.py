"""Tek bir COLMAP SfM kosusu calistirir ve suresini kaydeder.

Kullanim:
    python scripts/sfm_run.py <matching_method> <cikti_klasoru>

Ornek:
    python scripts/sfm_run.py sequential data/sinif-01/sfm_sequential
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PYTHON = r"C:\Users\sabod\miniconda3\envs\nerfstudio\python.exe"
TOOLS = [r"C:\Users\sabod\tools\colmap", r"C:\Users\sabod\tools\ffmpeg"]
FRAMES = Path("data/sinif-01/frames_1fps")


def main() -> int:
    method = sys.argv[1]
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PATH"] = os.pathsep.join(TOOLS + [env.get("PATH", "")])
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    cmd = [
        PYTHON, "-m", "nerfstudio.scripts.process_data", "images",
        "--data", str(FRAMES),
        "--output-dir", str(out_dir),
        "--matching-method", method,
        "--verbose",
    ]

    log_path = out_dir / "colmap_log.txt"
    print(f"[{method}] baslatiliyor -> {out_dir}")
    print(" ".join(cmd))

    t0 = time.time()
    with open(log_path, "w", encoding="utf-8", errors="replace") as log:
        proc = subprocess.run(cmd, env=env, stdout=log,
                              stderr=subprocess.STDOUT, text=True)
    elapsed = time.time() - t0

    timing = {
        "matching_method": method,
        "output_dir": str(out_dir),
        "input_frames": len(list(FRAMES.glob("*.jpg"))),
        "elapsed_seconds": round(elapsed, 1),
        "elapsed_minutes": round(elapsed / 60, 2),
        "return_code": proc.returncode,
    }
    (out_dir / "timing.json").write_text(json.dumps(timing, indent=2),
                                        encoding="utf-8")
    print(json.dumps(timing, indent=2))
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
