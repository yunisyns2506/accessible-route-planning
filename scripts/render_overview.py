"""Egitilmis bir modelden rapor icin genel gorunum render eder.

Kapali bir ic mekanda sahnenin disindan bakmak ise yaramaz: tavan ve duvarlar
hic gorulmemis bir aciyla rasterize edildigi icin Gaussianlar igne gibi cikar.
Bu nedenle iki gorunum uretilir:

  1. Genis aci ic mekan - gercek bir egitim kamerasinin pozu korunur, yalnizca
     odak uzakligi kucultulerek daha genis bir alan kadraja alinir.
  2. Kat plani - tavan ve ust duvarlar kirpilip (crop box) sahneye yukaridan
     bakilir; sira duzeni ve gecis koridorlari gorunur hale gelir.

Kullanim:
    python scripts/render_overview.py runs/sinif-01/G2_antialiased_30k
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch

from nerfstudio.cameras.cameras import Cameras, CameraType
from nerfstudio.data.scene_box import OrientedBox
from nerfstudio.utils.eval_utils import eval_setup

OUT = Path("docs/figures/kaynak")
W, H = 1280, 960


def make_camera(c2w: torch.Tensor, fx: float, device) -> Cameras:
    return Cameras(
        camera_to_worlds=c2w[None].to(device),
        fx=torch.tensor([[fx]], device=device),
        fy=torch.tensor([[fx]], device=device),
        cx=torch.tensor([[W / 2]], device=device),
        cy=torch.tensor([[H / 2]], device=device),
        width=torch.tensor([[W]], dtype=torch.int32, device=device),
        height=torch.tensor([[H]], dtype=torch.int32, device=device),
        camera_type=CameraType.PERSPECTIVE,
    )


def save(model, cam, path: Path) -> None:
    with torch.no_grad():
        out = model.get_outputs_for_camera(cam)
    rgb = (np.clip(out["rgb"].cpu().numpy(), 0, 1) * 255).astype(np.uint8)
    cv2.imwrite(str(path), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"  {path}")


def main() -> None:
    run_dir = Path(sys.argv[1])
    cfg = sorted(run_dir.rglob("config.yml"))[-1]
    _, pipeline, _, _ = eval_setup(cfg)
    model, device = pipeline.model, pipeline.device
    OUT.mkdir(parents=True, exist_ok=True)
    stem = run_dir.name

    cams = pipeline.datamanager.train_dataset.cameras
    centers = cams.camera_to_worlds[:, :3, 3].cpu().numpy()
    # En kucuk yayilimli eksen dusey eksendir (sabit yukseklikte yuruyus)
    up_axis = int(np.argmin(centers.std(axis=0)))
    cam_z = float(np.median(centers[:, up_axis]))
    print(f"dusey eksen: {'xyz'[up_axis]}  kamera yuksekligi: {cam_z:.2f}")

    base_fx = float(cams.fx[0]) * W / float(cams.width[0])

    # --- 1. Genis acili ic mekan gorunumleri ---
    # Yuruyus yolu boyunca esit arayla uc gercek kamera secilir, odak uzakligi
    # 0,55 katina dusurulerek kadraj genisletilir.
    for i, idx in enumerate(np.linspace(0, len(centers) - 1, 3, dtype=int), 1):
        c2w = cams.camera_to_worlds[int(idx)].clone()
        save(model, make_camera(c2w, base_fx * 0.55, device),
             OUT / f"{stem}_genisaci_{i}.jpg")

    # --- 2. Kat plani: tavan kirpilip yukaridan bakis ---
    pts = model.means.detach().cpu().numpy()
    lo = np.percentile(pts, 2, axis=0)
    hi = np.percentile(pts, 98, axis=0)
    center = (lo + hi) / 2
    # Dusey eksende: zeminden kamera yuksekliginin biraz ustune kadar tut
    center[up_axis] = (lo[up_axis] + cam_z + 0.25) / 2
    size = hi - lo
    size[up_axis] = (cam_z + 0.25) - lo[up_axis]
    model.crop_box = OrientedBox(
        R=torch.eye(3, device=device),
        T=torch.tensor(center, dtype=torch.float32, device=device),
        S=torch.tensor(size, dtype=torch.float32, device=device),
    )
    kept = int(model.crop_box.within(model.means).sum())
    print(f"kirpma sonrasi Gaussian: {kept:,} / {len(pts):,}")

    eye = center.copy()
    eye[up_axis] = cam_z + 0.25 + float(size[up_axis]) * 1.1
    fwd = np.zeros(3); fwd[up_axis] = -1.0          # asagi bak
    right = np.array([1.0, 0.0, 0.0])
    if up_axis == 0:
        right = np.array([0.0, 1.0, 0.0])
    true_up = np.cross(right, fwd)
    rot = np.stack([right, true_up, -fwd], axis=1)
    c2w = torch.from_numpy(
        np.concatenate([rot, eye.reshape(3, 1)], axis=1).astype(np.float32))
    save(model, make_camera(c2w, base_fx * 0.5, device),
         OUT / f"{stem}_katplani.jpg")
    model.crop_box = None


if __name__ == "__main__":
    main()
