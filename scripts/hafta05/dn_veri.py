"""DN-Splatter verisi (Colab sistem Python'u; pycolmap + transformers).

1. Kareler yeniden adlandırılır: kare k -> (k - 10) mod 1000. coolermap ayrıştırıcısı test karelerini
   sıralı listede her 10. sıradan seçer (0, 10, 20, ...); bu kaydırmayla test kareleri tam olarak bizim
   sabit test listemiz (0010, 0020, ..., 1000) olur ve eğitime girmez.
2. COLMAP modeli (LoMa + sequential + döngü + incremental) aynı yeni adlarla images.bin'e yazılır;
   cameras.bin ve points3D.bin değişmez. Kareler ve poz/iç parametreler tabandakiyle aynıdır.
3. Monoküler derinlik: Depth Anything V2 Metric Indoor (Large). Her karede seyrek COLMAP noktalarının
   derinliğine ölçek + kayma en küçük kareler (sapanları atarak) uydurulur; <ad>_aligned.npy (1080x1920,
   COLMAP birimi) olarak mono_depth/ altına yazılır. Hizalama istatistikleri derinlik_hizalama.json'da.

Kullanım: python3 dn_veri.py
"""
import json
import struct
from pathlib import Path

import numpy as np
import pycolmap
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

W = Path("/content/work")
SP = W / "sfm/loma/sequential_loop/incremental/sparse/0"
D = W / "dn/derslik4"
MODEL = "depth-anything/Depth-Anything-V2-Metric-Indoor-Large-hf"


def yeni(ad: str) -> str:
    return f"{(int(ad[:4]) - 10) % 1000:04d}.jpg"


def images_bin_yeniden_adlandir(src: Path, dst: Path) -> int:
    b = src.read_bytes(); o = 0
    n, = struct.unpack_from("<Q", b, o); o += 8
    out = [struct.pack("<Q", n)]
    for _ in range(n):
        head = b[o:o + 64]; o += 64                       # id, q(4), t(3), camera_id
        e = b.index(b"\x00", o); ad = b[o:e].decode(); o = e + 1
        m, = struct.unpack_from("<Q", b, o); o += 8
        pts = b[o:o + 24 * m]; o += 24 * m
        out += [head, yeni(ad).encode() + b"\x00", struct.pack("<Q", m), pts]
    assert o == len(b), "images.bin beklenmeyen biçim"
    dst.write_bytes(b"".join(out))
    return n


def main():
    (D / "colmap/sparse/0").mkdir(parents=True, exist_ok=True)
    (D / "images").mkdir(exist_ok=True); (D / "mono_depth").mkdir(exist_ok=True)
    for f in sorted((W / "frames_1080").glob("*.jpg")):
        t = D / "images" / yeni(f.name)
        if not t.exists():
            t.symlink_to(f)
    n = images_bin_yeniden_adlandir(SP / "images.bin", D / "colmap/sparse/0/images.bin")
    for nm in ("cameras.bin", "points3D.bin"):
        (D / "colmap/sparse/0" / nm).write_bytes((SP / nm).read_bytes())
    print("kare", len(list((D / "images").glob("*.jpg"))), "colmap görüntü", n, flush=True)

    r = pycolmap.Reconstruction(str(SP))
    proc = AutoImageProcessor.from_pretrained(MODEL)
    net = AutoModelForDepthEstimation.from_pretrained(MODEL).cuda().eval().half()
    stats = {}
    for im in sorted(r.images.values(), key=lambda i: i.name):
        out = D / "mono_depth" / (yeni(im.name)[:-4] + "_aligned.npy")
        if out.exists():
            continue
        cam = r.cameras[im.camera_id]; T = im.cam_from_world().matrix()
        ids = [p.point3D_id for p in im.points2D if p.has_point3D()]
        xyz = np.array([r.points3D[i].xyz for i in ids]); pc = xyz @ T[:, :3].T + T[:, 3]
        pc = pc[pc[:, 2] > 0]
        uv = np.array([cam.img_from_cam(q) for q in pc]); z = pc[:, 2]
        img = Image.open(W / "frames_1080" / im.name).convert("RGB")
        with torch.no_grad():
            x = proc(images=img, return_tensors="pt")["pixel_values"].cuda().half()
            d = net(pixel_values=x).predicted_depth[None].float()
            d = torch.nn.functional.interpolate(d, size=(img.height, img.width), mode="bicubic", align_corners=False)[0, 0]
        d = d.clamp(min=1e-3).cpu().numpy()
        ui = np.clip(np.round(uv[:, 0]).astype(int), 0, img.width - 1); vi = np.clip(np.round(uv[:, 1]).astype(int), 0, img.height - 1)
        dm = d[vi, ui]; keep = np.ones(len(z), bool)
        for _ in range(3):                                    # ölçek + kayma, sapanları at
            A = np.c_[dm[keep], np.ones(keep.sum())]; s, b = np.linalg.lstsq(A, z[keep], rcond=None)[0]
            res = np.abs(s * dm + b - z); keep = res < max(3 * np.median(res[keep]), 1e-6)
        al = (s * d + b).astype(np.float32)
        np.save(out, al)
        stats[yeni(im.name)] = {"nokta": int(len(z)), "olcek": float(s), "kayma": float(b),
                                "medyan_goreli_hata": float(np.median(np.abs(s * dm + b - z) / z))}
    old = json.loads((D / "derinlik_hizalama.json").read_text()) if (D / "derinlik_hizalama.json").exists() else {}
    old.update(stats); (D / "derinlik_hizalama.json").write_text(json.dumps(old, indent=1))
    g = np.array([v["medyan_goreli_hata"] for v in old.values()])
    print(f"derinlik: {len(list((D / 'mono_depth').glob('*_aligned.npy')))} kare, medyan göreli hata %{100 * np.median(g):.1f}", flush=True)


if __name__ == "__main__":
    main()
