import sys
from pathlib import Path
import numpy as np
import cv2
import torch

def evaluate_model(config_path="outputs-photos/processed/splatfacto/2026-10-12_144911/config.yml", out_dir="models/hafta-04_v2_fotograf/renders"):
    from nerfstudio.utils.eval_utils import eval_setup

    cfg_p = Path(config_path)
    if not cfg_p.exists():
        # Search latest
        base = Path("outputs-photos/processed/splatfacto")
        runs = sorted([d for d in base.iterdir() if d.is_dir()])
        if runs:
            cfg_p = runs[-1] / "config.yml"
        else:
            print("Model config bulunamadı.")
            return

    print("Model yükleniyor:", cfg_p)
    config, pipeline, checkpoint_path, step = eval_setup(cfg_p)
    dataset = pipeline.datamanager.train_dataset

    out_p = Path(out_dir)
    out_p.mkdir(parents=True, exist_ok=True)

    indices = [0, 15, 30, 45, len(dataset) - 1]
    psnrs = []

    for idx in indices:
        camera = dataset.cameras[idx : idx + 1]
        with torch.no_grad():
            outputs = pipeline.model.get_outputs_for_camera(camera)
        
        rgb = (np.clip(outputs["rgb"].cpu().numpy(), 0, 1) * 255).astype(np.uint8)
        gt = (np.clip(dataset[idx]["image"].cpu().numpy(), 0, 1) * 255).astype(np.uint8)
        
        mse = np.mean((rgb.astype(np.float32) - gt.astype(np.float32)) ** 2)
        psnr = 10 * np.log10(255.0**2 / (mse + 1e-10))
        psnrs.append(psnr)
        
        cv2.imwrite(str(out_p / f"photo_render_{idx}.png"), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(out_p / f"photo_gt_{idx}.png"), cv2.cvtColor(gt, cv2.COLOR_RGB2BGR))
        print(f"Kamera {idx}: PSNR = {psnr:.2f} dB")

    print(f"\nOrtalama PSNR: {np.mean(psnrs):.2f} dB")

if __name__ == "__main__":
    evaluate_model()
