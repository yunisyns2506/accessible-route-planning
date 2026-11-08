"""Renk düzeltmeli test metrikleri: her test karesinde render ile gerçek kare arasına 3x3 + sabit renk
dönüşümü uydurulur, sonra PSNR/SSIM/LPIPS ölçülür. Pozlama farkını ayırır; geometri ve keskinlik farkını ayırmaz.
Hafta 5 yöntemiyle aynı tanım (bilateral grid test karesinde nötr renk verdiği için ham PSNR yanıltıcıdır).

Kullanım: /content/ns/bin/python renk_degerlendir.py <kos_adi> [kare1.jpg kare2.jpg ...]
Çıktı: runs/<kos>/renk_duzeltmeli.json, runs/<kos>/renk/<kare>.jpg (listelenen kareler, düzeltmesiz render)
"""
import json
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from nerfstudio.utils.eval_utils import eval_setup

RUNS = Path("/content/work/runs")


def main(run, kareler):
    out = RUNS / run
    cfg = sorted(out.rglob("config.yml"))[-1]
    _, pipeline, _, _ = eval_setup(cfg, test_mode="test")
    pipeline.eval()
    model, dm = pipeline.model, pipeline.datamanager
    names = dm.eval_dataset._dataparser_outputs.image_filenames
    rows = []
    (out / "renk").mkdir(exist_ok=True)
    for camera, batch in dm.fixed_indices_eval_dataloader:
        with torch.no_grad():
            o = model.get_outputs_for_camera(camera=camera)
            gt = model.composite_with_background(model.get_gt_img(batch["image"]), o["background"]).to(o["rgb"].device)
            pr = o["rgb"].clamp(0, 1)
            X = torch.cat([pr.reshape(-1, 3), torch.ones(pr.numel() // 3, 1, device=pr.device)], 1)
            A = torch.linalg.lstsq(X.double(), gt.reshape(-1, 3).double()).solution.float()
            pc = (X @ A).reshape(pr.shape).clamp(0, 1)
            a, b = gt.permute(2, 0, 1)[None], pc.permute(2, 0, 1)[None]
            rows.append({"frame": Path(names[batch["image_idx"]]).name, "psnr": float(model.psnr(a, b)),
                         "ssim": float(model.ssim(a, b)), "lpips": float(model.lpips(a, b))})
        if rows[-1]["frame"] in kareler:
            Image.fromarray((pr.cpu().numpy() * 255).astype(np.uint8)).save(out / "renk" / rows[-1]["frame"], quality=92)
    ort = {k: round(float(np.mean([r[k] for r in rows])), 4) for k in ("psnr", "ssim", "lpips")}
    (out / "renk_duzeltmeli.json").write_text(json.dumps({"run": run, **ort, "n": len(rows), "per_image": rows}, indent=1))
    print(json.dumps({"run": run, **ort, "n": len(rows)}), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], set(sys.argv[2:]))
