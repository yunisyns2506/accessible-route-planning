"""Egitilmis bir kosuyu ayrilmis test goruntuleri uzerinde degerlendirir.

nerfstudio'nun Nerfstudio dataparser'i goruntulerin %10'unu egitime hic sokmadan
ayirir (train_split_fraction = 0.9). Bu script `ns-eval` calistirarak o ayrilmis
bolumde PSNR / SSIM / LPIPS olcer -- yani egitim gorunumu degil, gercek test
metrigi uretir.

Kullanim:
    python scripts/eval_run.py runs/sinif-01/G1_varsayilan [...]
"""
import json
import os
import subprocess
import sys
from pathlib import Path

PYTHON = r"C:\Users\sabod\miniconda3\envs\nerfstudio\python.exe"


def find_config(run_dir: Path) -> Path | None:
    configs = sorted(run_dir.rglob("config.yml"))
    return configs[-1] if configs else None


def evaluate(run_dir: Path) -> dict | None:
    config = find_config(run_dir)
    if config is None:
        print(f"[{run_dir.name}] config.yml bulunamadi, atlaniyor")
        return None

    out_json = run_dir / "eval_metrics.json"
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    cmd = [
        PYTHON, "-m", "nerfstudio.scripts.eval",
        "--load-config", str(config),
        "--output-path", str(out_json),
    ]
    print(f"[{run_dir.name}] degerlendiriliyor...")
    log = run_dir / "eval_log.txt"
    with open(log, "w", encoding="utf-8", errors="replace") as fh:
        proc = subprocess.run(cmd, env=env, stdout=fh,
                              stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0 or not out_json.exists():
        print(f"[{run_dir.name}] HATA (bkz. {log})")
        return None

    data = json.loads(out_json.read_text(encoding="utf-8"))
    res = data.get("results", {})

    # Egitim kosusunun kendi kaydiyla birlestir
    merged = {"run": run_dir.name}
    rm = run_dir / "run_metrics.json"
    if rm.exists():
        merged.update(json.loads(rm.read_text(encoding="utf-8")))
    merged.update({
        "psnr": round(res.get("psnr", 0), 3),
        "ssim": round(res.get("ssim", 0), 4),
        "lpips": round(res.get("lpips", 0), 4),
        "fps": round(res.get("fps", 0), 2),
        "num_rays_per_sec": res.get("num_rays_per_sec"),
    })
    (run_dir / "summary.json").write_text(json.dumps(merged, indent=2),
                                          encoding="utf-8")
    return merged


def main() -> None:
    rows = [r for r in (evaluate(Path(a)) for a in sys.argv[1:]) if r]
    if not rows:
        return
    print("\n--- TEST METRIKLERI (ayrilmis %10 goruntu) ---")
    hdr = (f"{'kosu':<20}{'PSNR':>8}{'SSIM':>8}{'LPIPS':>8}"
           f"{'sure dk':>9}{'VRAM MiB':>10}")
    print(hdr)
    for r in rows:
        print(f"{r['run']:<20}{r['psnr']:>8.2f}{r['ssim']:>8.4f}"
              f"{r['lpips']:>8.4f}{r.get('elapsed_minutes', 0):>9}"
              f"{str(r.get('peak_vram_mib', '-')):>10}")


if __name__ == "__main__":
    main()
