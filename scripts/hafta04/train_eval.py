"""Bir nerfstudio veri klasorunde duz splatfacto egitir ve test karelerinde
kare kare degerlendirir.

Kullanim:
    python scripts/hafta04/train_eval.py <kosu_adi> [--iters 30000]

Ornek:
    python scripts/hafta04/train_eval.py sift_exhaustive_incremental

Egitim ayarlari hafta 3 G1 ile aynidir (splatfacto varsayilanlari, kareler
CPU'da onbellekte); yalnizca iterasyon 30.000'dir. Egitim boyunca sure, tepe
VRAM ve tepe RAM olculur. Degerlendirme ayri bir surecte yapilir ve her test
karesi icin PSNR / SSIM / LPIPS ayri kaydedilir (eval_per_image.json); bu
sayede koşular ortak test kareleri uzerinden karsilastirilabilir.

Cikti: runs/sinif-01/hafta-04/<kosu_adi>/
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import PYTHON, RUNS, WORK, ResourceMonitor, read_json, tool_env, write_json  # noqa: E402

# Rapor gorselleri icin render'i kaydedilecek sabit test kareleri
FIGURE_FRAMES = {"frame_0100.jpg", "frame_0200.jpg", "frame_0300.jpg"}


def find_config(run_dir: Path) -> Path | None:
    configs = sorted(run_dir.rglob("config.yml"))
    return configs[-1] if configs else None


def train(run: str, iters: int) -> dict:
    data = WORK / "ns" / run
    out = RUNS / run
    res = read_json(out / "train_metrics.json")
    if res and res.get("return_code") == 0:
        print(f"[{run}] egitim zaten tamam")
        return res
    cmd = [PYTHON, "-m", "nerfstudio.scripts.train", "splatfacto",
           "--data", str(data), "--output-dir", str(out), "--experiment-name", run,
           "--max-num-iterations", str(iters),
           "--steps-per-eval-image", "2000", "--steps-per-save", str(iters),
           "--viewer.quit-on-train-completion", "True",
           "--pipeline.datamanager.cache-images", "cpu",
           "nerfstudio-data"]
    env = tool_env()
    env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    mon = ResourceMonitor(interval=2.0)
    print(f"[{run}] egitim basliyor ({iters} iterasyon)")
    rc, sec = mon.run(cmd, out / "train_log.txt", env)
    res = {"run": run, "iterations": iters, "return_code": rc,
           "train_minutes": round(sec / 60, 2), **mon.summary(),
           "split": read_json(data / "split.json")}
    write_json(out / "train_metrics.json", res)
    print(f"[{run}] egitim rc={rc} {sec / 60:.1f} dk, VRAM {res['peak_vram_mib']} MiB, "
          f"RAM {res['peak_ram_mib']} MiB")
    return res


def evaluate_inprocess(run: str) -> None:
    """Ayri surecte calisir: modeli yukler, test karelerini tek tek olcer."""
    import torch
    import torchvision.utils as vutils
    from nerfstudio.utils.eval_utils import eval_setup

    out = RUNS / run
    _, pipeline, ckpt, step = eval_setup(find_config(out), test_mode="test")
    pipeline.eval()
    dm = pipeline.datamanager
    names = dm.eval_dataset._dataparser_outputs.image_filenames
    split = read_json(WORK / "ns" / run / "split.json")
    rename = read_json(WORK / "ns" / "_images" / "rename_map.json")
    inv = {v: k for k, v in rename.items()}
    fig_dir = out / "renders"
    rows = []
    for camera, batch in dm.fixed_indices_eval_dataloader:
        with torch.no_grad():
            outputs = pipeline.model.get_outputs_for_camera(camera=camera)
            metrics, images = pipeline.model.get_image_metrics_and_images(outputs, batch)
        orig = inv[Path(names[batch["image_idx"]]).name]
        rows.append({"frame": orig, **{k: float(v) for k, v in metrics.items()}})
        if orig in FIGURE_FRAMES:
            fig_dir.mkdir(exist_ok=True)
            vutils.save_image(images["img"].permute(2, 0, 1).cpu(),
                              fig_dir / f"{Path(orig).stem}_gt_render.png")
    gauss = int(pipeline.model.num_points)
    write_json(out / "eval_per_image.json", {"run": run, "step": step, "checkpoint": str(ckpt),
                                             "num_gaussians": gauss, "test_frames_expected":
                                             split["test_frames"], "per_image": rows})


def evaluate(run: str) -> dict:
    out = RUNS / run
    pe = out / "eval_per_image.json"
    if not pe.exists():
        print(f"[{run}] degerlendirme")
        rc = subprocess.run([PYTHON, __file__, run, "--eval-only"], env=tool_env(),
                            stdout=open(out / "eval_log.txt", "w", encoding="utf-8",
                                        errors="replace"),
                            stderr=subprocess.STDOUT).returncode
        if rc != 0 or not pe.exists():
            print(f"[{run}] degerlendirme HATASI (bkz. eval_log.txt)")
            return {}
    ev = read_json(pe)
    rows = ev["per_image"]
    mean = {k: round(sum(r[k] for r in rows) / len(rows), 4) for k in ("psnr", "ssim", "lpips")}
    tm = read_json(out / "train_metrics.json")
    ply = sorted(out.rglob("*.ply"))
    summary = {"run": run, **mean, "n_test": len(rows), "num_gaussians": ev["num_gaussians"],
               "train_minutes": tm["train_minutes"], "peak_vram_mib": tm["peak_vram_mib"],
               "net_vram_mib": tm["net_vram_mib"], "peak_ram_mib": tm["peak_ram_mib"],
               "train_images": tm["split"]["train"],
               "ply_mib": round(ply[0].stat().st_size / 2**20, 1) if ply else None}
    write_json(out / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--iters", type=int, default=30000)
    ap.add_argument("--eval-only", action="store_true")
    args = ap.parse_args()
    if args.eval_only:
        evaluate_inprocess(args.run)
        return 0
    res = train(args.run, args.iters)
    if res["return_code"] != 0:
        return 1
    return 0 if evaluate(args.run) else 1


if __name__ == "__main__":
    raise SystemExit(main())
