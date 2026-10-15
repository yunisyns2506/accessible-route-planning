"""Egitilmis bir modelin AYRILMIS TEST goruntulerinden render/gercek karsilastirmasi uretir.

Egitim gorunumu degil, modelin hic gormedigi test kameralari kullanilir.
Her secilen kamera icin yan yana (gercek | render) bir JPG yazilir ve o kameranin
PSNR degeri goruntunun uzerine not dusulur.

Kullanim:
    python scripts/render_compare.py runs/sinif-01/G1_varsayilan [...]
"""
import glob
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import torch

from nerfstudio.utils.eval_utils import eval_setup

OUT_DIR = Path("docs/figures/render")


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    mse = np.mean((a.astype(np.float32) - b.astype(np.float32)) ** 2)
    return float(10 * np.log10(255.0 ** 2 / (mse + 1e-10)))


def label(img: np.ndarray, text: str) -> np.ndarray:
    out = img.copy()
    cv2.rectangle(out, (0, 0), (out.shape[1], 46), (0, 0, 0), -1)
    cv2.putText(out, text, (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                (255, 255, 255), 2, cv2.LINE_AA)
    return out


def process(run_dir: Path, n_views: int = 3) -> dict | None:
    cfgs = sorted(run_dir.rglob("config.yml"))
    if not cfgs:
        print(f"[{run_dir.name}] config.yml yok, atlaniyor")
        return None

    config, pipeline, _, step = eval_setup(cfgs[-1])
    ds = pipeline.datamanager.eval_dataset
    if len(ds) == 0:
        print(f"[{run_dir.name}] test goruntusu yok")
        return None

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    idxs = np.linspace(0, len(ds) - 1, num=min(n_views, len(ds)), dtype=int)
    scores = []

    for i in idxs:
        camera = ds.cameras[int(i): int(i) + 1].to(pipeline.device)
        with torch.no_grad():
            out = pipeline.model.get_outputs_for_camera(camera)
        rgb = (np.clip(out["rgb"].cpu().numpy(), 0, 1) * 255).astype(np.uint8)
        gt = (np.clip(ds[int(i)]["image"].cpu().numpy(), 0, 1) * 255).astype(np.uint8)
        if gt.shape != rgb.shape:
            gt = cv2.resize(gt, (rgb.shape[1], rgb.shape[0]))

        p = psnr(rgb, gt)
        scores.append(p)

        pair = np.hstack([label(gt, "GERCEK FOTOGRAF"),
                          label(rgb, f"RENDER  PSNR {p:.2f} dB")])
        name = f"{run_dir.name}_test{int(i):02d}.jpg"
        cv2.imwrite(str(OUT_DIR / name),
                    cv2.cvtColor(pair, cv2.COLOR_RGB2BGR),
                    [cv2.IMWRITE_JPEG_QUALITY, 88])
        print(f"  test kamera {int(i):>3}: PSNR {p:6.2f} dB  -> {name}")

    # Gaussian sayisi yalnizca splatfacto ailesinde anlamlidir; NeRF tabanli
    # yontemlerde (nerfacto vb.) boyle bir alan yoktur.
    means = getattr(pipeline.model, "means", None)
    n_gauss = int(means.shape[0]) if means is not None else 0
    res = {
        "run": run_dir.name,
        "step": int(step),
        "test_images": len(ds),
        "sampled_psnr_mean": round(float(np.mean(scores)), 3),
        "num_gaussians": n_gauss,
    }
    print(f"[{run_dir.name}] ort. PSNR {res['sampled_psnr_mean']} dB"
          + (f", {n_gauss:,} Gaussian" if n_gauss else " (Gaussian temsili degil)"))
    (run_dir / "render_compare.json").write_text(json.dumps(res, indent=2),
                                                 encoding="utf-8")
    del pipeline
    torch.cuda.empty_cache()
    return res


def main() -> None:
    args = sys.argv[1:] or sorted(glob.glob("runs/sinif-01/*"))
    rows = [r for r in (process(Path(a)) for a in args) if r]
    if rows:
        print("\n--- OZET ---")
        for r in rows:
            print(f"{r['run']:<22}{r['sampled_psnr_mean']:>8.2f} dB"
                  f"{r['num_gaussians']:>12,} Gaussian")


if __name__ == "__main__":
    main()
