"""Bir 3DGS .ply'yi çekim yolundan uzak bakış açılarından çizer (gsplat, nerfstudio gerekmez).

Amaç: test kareleri çekim yolunun üzerindedir; Unity/VR'da ise kullanıcı yoldan uzaklaşır. Bu betik
aynı ölçüyle iki sahneyi (Meeting room, Derslik 4) yoldan uzak açılardan çizer:

  * yol  : test karesinin kendi pozu (kontrol; gerçek kare ile yan yana, PSNR yazılı)
  * yan  : aynı poz, kamera sağına R kadar kaydırılmış
  * ust  : aynı poz, yukarı R kadar kaldırılmış ve 15° aşağı bakan
  * don  : aynı konum, 35° sola dönmüş
  * merkez_k : kamera merkezlerinin ortasından, göz yüksekliğinde, 4 yöne yatay bakış
R = kamera merkezlerinin ağırlık merkezine uzaklıklarının medyanının 0,25'i (sahneye göre ölçekli).
Her görünüm için en yakın eğitim kamerasına uzaklık (R biriminde) yazılır.

Kamera zinciri: transforms.json (nerfstudio, OpenGL) -> dataparser_transforms.json (T, s) ile
dışa aktarılan .ply'nin çerçevesine; ply de bu çerçevededir.

Kullanım: /content/ns/bin/python uzak_gorus.py <splat.ply> <transforms.json> <dataparser_transforms.json>
          <kareler_klasoru> <cikti_klasoru> <etiket> [--kareler 0250,0500,0750]
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import torch
from gsplat import rasterization
from PIL import Image, ImageDraw, ImageFont
from plyfile import PlyData

dev = "cuda"
TF = {}


def yukle_ply(p):
    v = PlyData.read(str(p))["vertex"]
    ad = v.data.dtype.names
    f = lambda *k: torch.tensor(np.stack([np.asarray(v[x], np.float32) for x in k], 1), device=dev)
    means = f("x", "y", "z")
    scales = torch.exp(f("scale_0", "scale_1", "scale_2"))
    quats = f("rot_0", "rot_1", "rot_2", "rot_3")
    quats = quats / quats.norm(dim=1, keepdim=True)
    opac = torch.sigmoid(f("opacity")[:, 0])
    dc = f("f_dc_0", "f_dc_1", "f_dc_2")[:, None, :]
    rest_ad = sorted([a for a in ad if a.startswith("f_rest_")], key=lambda a: int(a[7:]))
    rest = f(*rest_ad).reshape(len(means), 3, -1).transpose(1, 2)
    sh = torch.cat([dc, rest], 1)
    deg = int(round(np.sqrt(sh.shape[1]))) - 1
    return means, quats, scales, opac, sh, deg


def kameralar(tf_p, dp_p):
    tf = json.loads(Path(tf_p).read_text())
    TF.update(tf)
    dp = json.loads(Path(dp_p).read_text())
    T = np.eye(4); T[:3] = np.array(dp["transform"]); s = dp["scale"]
    # nerfstudio, applied_transform'u dataparser dönüşümüne katar (transform = T' · A); transforms.json'daki
    # pozlar ise A'yı zaten içerir. Bu yüzden pozlara T · A⁻¹ uygulanır.
    if "applied_transform" in tf:
        A = np.eye(4); A[:3] = np.array(tf["applied_transform"])
        T = T @ np.linalg.inv(A)
    K = np.array([[tf["fl_x"], 0, tf["cx"]], [0, tf["fl_y"], tf["cy"]], [0, 0, 1]])
    cams = {}
    for fr in tf["frames"]:
        c = T @ np.array(fr["transform_matrix"])
        c[:3, 3] *= s
        cams[Path(fr["file_path"]).stem] = c
    return cams, K, int(tf["w"]), int(tf["h"]), set(Path(x).stem for x in tf.get("train_filenames", []))


def ciz(g, c2w_gl, K, w, h):
    means, quats, scales, opac, sh, deg = g
    c2w = c2w_gl.copy(); c2w[:3, 1:3] *= -1          # OpenGL -> OpenCV
    vm = torch.tensor(np.linalg.inv(c2w), dtype=torch.float32, device=dev)[None]
    Kt = torch.tensor(K, dtype=torch.float32, device=dev)[None]
    with torch.no_grad():
        img, _, _ = rasterization(means, quats, scales, opac, sh, vm, Kt, w, h, sh_degree=deg,
                                  near_plane=0.01, render_mode="RGB", rasterize_mode="classic")
    return (img[0].clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)


def rot(axis, deg):
    a = np.radians(deg); axis = axis / np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def bakis(konum, ileri, yukari):
    z = -ileri / np.linalg.norm(ileri)                 # OpenGL: kamera -z'ye bakar
    x = np.cross(yukari, z); x /= np.linalg.norm(x)
    y = np.cross(z, x)
    c = np.eye(4); c[:3, 0], c[:3, 1], c[:3, 2], c[:3, 3] = x, y, z, konum
    return c


def etiketle(img, yazi):
    im = Image.fromarray(img); d = ImageDraw.Draw(im)
    try:
        fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(18, img.shape[0] // 30))
    except OSError:
        fnt = ImageFont.load_default()
    d.rectangle([0, 0, im.width, fnt.size + 14], fill=(0, 0, 0))
    d.text((8, 6), yazi, fill=(255, 255, 255), font=fnt)
    return np.asarray(im)


def psnr(a, b):
    return float(10 * np.log10(255.0 ** 2 / np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)))


def main():
    ap = argparse.ArgumentParser()
    for k in ("ply", "tf", "dp", "kareler", "out", "etiket"):
        ap.add_argument(k)
    ap.add_argument("--kareler_sec", default="0250,0500,0750")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    g = yukle_ply(a.ply)
    cams, K, w, h, train = kameralar(a.tf, a.dp)
    C = np.array([c[:3, 3] for c in cams.values()])
    Ctr = np.array([cams[k][:3, 3] for k in cams if k in train]) if train else C
    m = C.mean(0)
    R = 0.25 * np.median(np.linalg.norm(C - m, axis=1))
    up = np.mean([c[:3, 1] for c in cams.values()], 0); up /= np.linalg.norm(up)
    uz = lambda p: float(np.min(np.linalg.norm(Ctr - p, axis=1)) / R)
    kayit = {"etiket": a.etiket, "R_birim": float(R), "gaussian": int(len(g[0])), "gorunumler": []}

    satirlar = []
    for ad in a.kareler_sec.split(","):
        c = cams[ad]
        r0 = ciz(g, c, K, w, h)
        gp = Path(a.kareler) / f"{ad}.jpg"
        p = float("nan")
        if gp.exists():   # gerçek kare, çizim ile aynı iğne deliği modeline getirilir (bozulma giderilir)
            gt = np.asarray(Image.open(gp).convert("RGB").resize((w, h)))
            dist = np.array([TF.get(k, 0.0) for k in ("k1", "k2", "p1", "p2")])
            if np.any(dist):
                gt = cv2.undistort(gt, K, dist)
            p = psnr(r0, gt)
            Image.fromarray(np.concatenate([etiketle(gt, f"{a.etiket} {ad} · gerçek kare"),
                                            etiketle(r0, f"çizilen (test, görülmedi) · PSNR {p:.2f} dB")], 1)
                            ).save(out / f"{a.etiket}_{ad}_gercek_cizilen.jpg", quality=92)
        sag, ileri = c[:3, 0], -c[:3, 2]
        var = {}
        cy = c.copy(); cy[:3, 3] += R * sag; var["yan"] = cy
        cu = bakis(c[:3, 3] + R * up, rot(np.cross(ileri, up), -15) @ ileri, up); var["ust"] = cu
        cd = c.copy(); cd[:3, :3] = rot(up, 35) @ c[:3, :3]; var["don"] = cd
        kare = [etiketle(r0, f"{ad} yol (test pozu)" + (f" · PSNR {p:.1f}" if p == p else ""))]
        for k, cv in var.items():
            img = ciz(g, cv, K, w, h)
            d = uz(cv[:3, 3])
            kare.append(etiketle(img, f"{ad} {k} · en yakın kamera {d:.2f}R"))
            Image.fromarray(img).save(out / f"{a.etiket}_{ad}_{k}.jpg", quality=92)
            kayit["gorunumler"].append({"kare": ad, "tur": k, "en_yakin_kamera_R": d})
        kayit["gorunumler"].append({"kare": ad, "tur": "yol", "psnr": p})
        satirlar.append(np.concatenate([np.asarray(Image.fromarray(x).resize((w // 2, h // 2))) for x in kare], 1))
    Image.fromarray(np.concatenate(satirlar, 0)).save(out / f"{a.etiket}_yoldan_uzak.jpg", quality=90)

    # oda ortası, göz yüksekliği (kameraların ortalama yüksekliği), 4 yatay yön
    yatay = C[0] - m; yatay -= (yatay @ up) * up; yatay /= np.linalg.norm(yatay)
    merkez = []
    for i, yaw in enumerate((0, 90, 180, 270)):
        cv = bakis(m, rot(up, yaw) @ yatay, up)
        img = ciz(g, cv, K, w, h)
        d = uz(m)
        merkez.append(etiketle(np.asarray(Image.fromarray(img).resize((w // 2, h // 2))),
                               f"{a.etiket} oda ortası {yaw}° · en yakın kamera {d:.2f}R"))
        Image.fromarray(img).save(out / f"{a.etiket}_merkez_{yaw}.jpg", quality=92)
        kayit["gorunumler"].append({"kare": "merkez", "tur": f"yaw{yaw}", "en_yakin_kamera_R": d})
    Image.fromarray(np.concatenate([np.concatenate(merkez[:2], 1), np.concatenate(merkez[2:], 1)], 0)
                    ).save(out / f"{a.etiket}_oda_ortasi.jpg", quality=90)
    (out / f"{a.etiket}_uzak_gorus.json").write_text(json.dumps(kayit, indent=1, ensure_ascii=False))
    print(json.dumps(kayit, ensure_ascii=False))


if __name__ == "__main__":
    main()
