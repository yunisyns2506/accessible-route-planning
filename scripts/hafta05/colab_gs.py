"""Hafta 5 3DGS hattı (Colab, L4): bir SfM koşusundan veri hazırlama, splatfacto
eğitimi, test karelerinde kare kare değerlendirme ve .ply dışa aktarma.

Kullanım (3DGS ortamının Python'u ile):
    /content/ns/bin/python colab_gs.py <cikarici> <eslestirme> <mapper> [--iters 30000]
    /content/ns/bin/python colab_gs.py loma sequential incremental

Veri: SfM'in en büyük modeli nerfstudio biçimine çevrilir. Sahneden kopuk
kameralar (en yakın 3 kameraya uzaklığı medyanın 10 katını aşan) ayıklanır
(hafta 4 ile aynı kural). SABİT TEST LİSTESİ: her 10. kare (0010, 0020, ...,
1000; 100 kare) hiçbir eğitime girmez; SfM'e ise girer.

Eğitim: splatfacto varsayılanları, kareler CPU önbelleğinde, 30.000 iterasyon,
tam çözünürlük (1920x1080; --downscale-factor 1). Süre, tepe RAM ve VRAM ölçülür.
--tag / --extra: koşu adına ek ve ns-train model ayarları (ör. pozlama düzeltme, MCMC).
--res 1440 / 4k: aynı SfM pozlarıyla 2560x1440 / 3840x2160 kareler kullanılır (iç
parametreler 4/3 / 2 ile çarpılır; bozulma katsayıları birimsiz olduğundan
değişmez) ve kareler 8 bit önbellekte tutulur. --method ile
splatfacto-big seçilebilir. Koşu adına çözünürlük ve yöntem eklenir.
Değerlendirme ayrı süreçte yapılır: her test karesi için PSNR / SSIM / LPIPS.
Çıktılar Drive'a kopyalanır.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/content/work")
from colab_sfm import SFM, WORK, ResourceMonitor, read_json, write_json  # noqa: E402

FRAMES = WORK / "frames_1080"
NS = WORK / "ns"
RUNS = WORK / "runs"
DRIVE = Path("/content/drive/MyDrive/hafta5_derslik4")
PY = "/content/ns/bin/python"
SCALE = {"1080": 1, "1440": 4 / 3, "4k": 2}
TEST_EVERY = 10
FIGURE_FRAMES = {"0250.jpg", "0500.jpg", "0750.jpg"}


def sync_drive(run: str) -> None:
    if Path("/content/drive/MyDrive").is_dir():
        subprocess.run(["rsync", "-a", f"{RUNS / run}/", f"{DRIVE}/runs/{run}/"], check=False)
        subprocess.run(["rsync", "-a", "--include", "*.json", "--exclude", "*",
                        f"{NS / run}/", f"{DRIVE}/ns/{run}/"], check=False)


def outlier_cameras(frames: list[dict], k: int = 3, factor: float = 10.0) -> set[int]:
    import numpy as np
    from scipy.spatial import cKDTree
    centers = np.array([f["transform_matrix"] for f in frames])[:, :3, 3]
    d, _ = cKDTree(centers).query(centers, k=k + 1)
    nn = d[:, 1:].mean(1)
    return set(np.where(nn > factor * np.median(nn))[0].tolist())


def make_data(ext: str, match: str, mapper: str, res: str = "1080", method: str = "splatfacto",
              tag: str = "") -> str:
    from nerfstudio.process_data.colmap_utils import colmap_to_json
    run = f"{ext}_{match}_{mapper}"
    run += (f"_{res}" if res != "1080" else "") + \
        (f"_{method.split('-')[-1]}" if method != "splatfacto" else "") + (f"_{tag}" if tag else "")
    out = NS / run
    if (out / "split.json").exists():
        return run
    mp = read_json(SFM / ext / match / mapper / "map.json")
    if not mp or mp.get("return_code") != 0 or not mp.get("models"):
        raise SystemExit(f"SfM sonucu yok: {ext}/{match}/{mapper}")
    main_model = mp["models"][0]["model"]
    out.mkdir(parents=True, exist_ok=True)
    if not (out / "images").exists():
        (out / "images").symlink_to(WORK / f"frames_{res}")
    n = colmap_to_json(recon_dir=SFM / ext / match / mapper / "sparse" / main_model,
                       output_dir=out)
    tf = read_json(out / "transforms.json")
    if SCALE[res] != 1:
        for k in ("fl_x", "fl_y", "cx", "cy"):
            tf[k] = tf[k] * SCALE[res]
        tf["w"], tf["h"] = round(tf["w"] * SCALE[res]), round(tf["h"] * SCALE[res])
    outliers = outlier_cameras(tf["frames"])
    outlier_names = sorted(Path(f["file_path"]).name for i, f in enumerate(tf["frames"])
                           if i in outliers)
    tf["frames"] = [f for i, f in enumerate(tf["frames"]) if i not in outliers]
    all_names = sorted(p.name for p in FRAMES.glob("*.jpg"))
    tests = {nm for nm in all_names if int(nm[:-4]) % TEST_EVERY == 0}
    train, test = [], []
    for fr in tf["frames"]:
        (test if Path(fr["file_path"]).name in tests else train).append(fr["file_path"])
    tf["train_filenames"] = sorted(train)
    tf["val_filenames"] = tf["test_filenames"] = sorted(test)
    write_json(out / "transforms.json", tf)
    write_json(out / "split.json", {
        "run": run, "model": main_model, "input_frames": len(all_names), "registered": n,
        "not_registered": len(all_names) - n, "outlier_cameras": len(outliers),
        "outlier_frames": outlier_names, "train": len(train), "test": len(test),
        "test_total": len(tests), "test_frames": sorted(Path(f).name for f in test)})
    print(f"{run}: {n}/{len(all_names)} poz, kopuk kamera {len(outliers)}, "
          f"eğitim {len(train)}, test {len(test)}/{len(tests)}", flush=True)
    return run


def find_config(run_dir: Path):
    configs = sorted(run_dir.rglob("config.yml"))
    return configs[-1] if configs else None


def train(run: str, iters: int, method: str = "splatfacto", extra: list | None = None) -> dict:
    out = RUNS / run
    res = read_json(out / "train_metrics.json")
    if res and res.get("return_code") == 0:
        return res
    cmd = [PY, "-m", "nerfstudio.scripts.train", method,
           "--data", str(NS / run), "--output-dir", str(out), "--experiment-name", run,
           "--max-num-iterations", str(iters),
           "--steps-per-eval-image", "2000", "--steps-per-save", str(iters),
           "--viewer.quit-on-train-completion", "True", "--vis", "tensorboard",
           "--pipeline.datamanager.cache-images", "cpu",
           # 1440p/4K'da float32 önbellek RAM'e sığmaz (4K: ~90 GB); 8 bit kareler aynı bilgiyi taşır
           *(["--pipeline.datamanager.cache-images-type", "uint8"]
             if ("_1440" in run or "_4k" in run or extra) else []),
           *(extra or []),
           "nerfstudio-data", "--downscale-factor", "1"]
    print(f"[{run}] eğitim başlıyor ({iters} iterasyon)", flush=True)
    mon = ResourceMonitor(interval=2.0)
    rc, sec = mon.run(cmd, out / "train_log.txt")
    res = {"run": run, "method": method, "extra": extra or [], "iterations": iters, "return_code": rc,
           "train_minutes": round(sec / 60, 2), **mon.summary(),
           "split": read_json(NS / run / "split.json")}
    write_json(out / "train_metrics.json", res)
    print(f"[{run}] eğitim rc={rc} {sec / 60:.1f} dk, VRAM {res['peak_vram_mib']} MiB, "
          f"RAM {res['peak_ram_mib']} MiB", flush=True)
    sync_drive(run)
    return res


def evaluate_inprocess(run: str) -> None:
    import torch
    import torchvision.utils as vutils
    from nerfstudio.utils.eval_utils import eval_setup
    out = RUNS / run
    _, pipeline, ckpt, step = eval_setup(find_config(out), test_mode="test")
    pipeline.eval()
    dm = pipeline.datamanager
    names = dm.eval_dataset._dataparser_outputs.image_filenames
    rows = []
    for camera, batch in dm.fixed_indices_eval_dataloader:
        with torch.no_grad():
            outputs = pipeline.model.get_outputs_for_camera(camera=camera)
            metrics, images = pipeline.model.get_image_metrics_and_images(outputs, batch)
        name = Path(names[batch["image_idx"]]).name
        rows.append({"frame": name, **{k: float(v) for k, v in metrics.items()}})
        if name in FIGURE_FRAMES:
            (out / "renders").mkdir(exist_ok=True)
            vutils.save_image(images["img"].permute(2, 0, 1).cpu(),
                              out / "renders" / f"{Path(name).stem}_gt_render.png")
    write_json(out / "eval_per_image.json", {
        "run": run, "step": step, "checkpoint": str(ckpt),
        "num_gaussians": int(pipeline.model.num_points), "per_image": rows})


def evaluate(run: str) -> dict:
    out = RUNS / run
    pe = out / "eval_per_image.json"
    if not pe.exists():
        print(f"[{run}] değerlendirme", flush=True)
        with open(out / "eval_log.txt", "w") as f:
            subprocess.run([PY, __file__, run, "-", "-", "--eval-only"],
                           stdout=f, stderr=subprocess.STDOUT)
    ev = read_json(pe)
    rows = ev["per_image"]
    mean = {k: round(sum(r[k] for r in rows) / len(rows), 4) for k in ("psnr", "ssim", "lpips")}
    tm = read_json(out / "train_metrics.json")
    summary = {"run": run, **mean, "n_test": len(rows), "num_gaussians": ev["num_gaussians"],
               "train_minutes": tm["train_minutes"], "peak_vram_mib": tm["peak_vram_mib"],
               "peak_ram_mib": tm["peak_ram_mib"], "train_images": tm["split"]["train"]}
    write_json(out / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return summary


def export_ply(run: str) -> None:
    out = RUNS / run
    if list((out / "export").glob("*.ply")):
        return
    subprocess.run([PY, "-m", "nerfstudio.scripts.exporter", "gaussian-splat",
                    "--load-config", str(find_config(out)), "--output-dir", str(out / "export")],
                   stdout=open(out / "export_log.txt", "w"), stderr=subprocess.STDOUT)
    sync_drive(run)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ext")
    ap.add_argument("match")
    ap.add_argument("mapper")
    ap.add_argument("--iters", type=int, default=30000)
    ap.add_argument("--eval-only", action="store_true")
    ap.add_argument("--res", choices=list(SCALE), default="1080")
    ap.add_argument("--method", default="splatfacto")
    ap.add_argument("--tag", default="", help="koşu adına eklenir (ör. H)")
    ap.add_argument("--extra", default="", help="ns-train'e eklenecek model ayarları, boşlukla ayrılmış")
    a = ap.parse_args()
    if a.eval_only:
        evaluate_inprocess(a.ext)
        return 0
    run = make_data(a.ext, a.match, a.mapper, a.res, a.method, a.tag)
    if train(run, a.iters, a.method, a.extra.split())["return_code"] != 0:
        return 1
    evaluate(run)
    export_ply(run)
    sync_drive(run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
