"""Sınıf zeminini gerçek karelerden üretilen düz, görüşe bağlı olmayan bir Gaussian katmanıyla değiştirir (eğitim yok).

Zemin 5 cm ızgaraya bölünür. Her hücre yakın ve yeterince dik bakan karelere izdüşürülür, sandalye gibi pikseller renkle elenir,
kare parlaklık farkları medyanla düzeltilir (log parlaklık = hücre + kare). Hücre rengi kalan örneklerin medyanı olduğu için tek
bakıştan gelen yansımalar büyük ölçüde kaybolur. Örneği olmayan hücreler (sandalye altı) cv2.inpaint ile doldurulur.
Birleşik dosyada ana zemindeki y < zemin + 3 cm Gaussian'lar silinir, yerine ızgara başına bir yassı Gaussian konur.
Platform ön kenarı Gaussian yükseklik dağılımından bulunur. Çıktı: birlesik/*_gercek_zemin_unity.ply, zemin_harita.png
"""
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import pycolmap
from plyfile import PlyData, PlyElement

H6 = Path('/content/drive/MyDrive/Hafta 6 Çalışmaları'); S = H6 / 'derslik4_cekim2'; K = H6 / 'derslik4_koridor'; O = H6 / 'birlesik'; W = Path('/content/zg'); (W / 'k').mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(H6 / 'betikler_koridor')); sys.dont_write_bytecode = True
import unity_ply  # noqa: E402

F = 212.51 / 210.0; AD = 0.05; SP = 'sfm/loma/sequential_loop/incremental'; Y0 = -0.015 * F; SIG = 0.033; EPS = 0.002
subprocess.check_call(['rsync', '-a', f'{S / "frames_1080"}/', f'{W / "k"}/'])
J = json.loads((K / 'logs/hizalama.json').read_text()); Rl, dl = np.array(J['yatay']['Rl']), np.array(J['yatay']['dl']); G = json.loads((S / 'logs/olcum08/geometri_sinif.json').read_text()); Pl = json.loads((K / 'logs/kapi.json').read_text())['Pl']
MODEL = S / SP / 'sparse' / json.load(open(S / SP / 'map.json'))['models'][0]['model']; Ms, o_, _, _ = unity_ply.hedef_cerceve(MODEL, 2.10)
t0 = PlyData.read(str(O / 'birlesik_sinif1080_koridor_unity.ply'))['vertex'].data; A = np.c_[t0['x'], t0['y'], t0['z']].astype(float); opk = 1 / (1 + np.exp(-t0['opacity'].astype(float)))
b_ = (opk > .5) & (np.abs(A[:, 2]) < 4); xs = np.arange(-11.6 * F, -7.8 * F, .05); fr_ = []
for x in xs:
    m = b_ & (A[:, 0] >= x) & (A[:, 0] < x + .05); u = ((A[m, 1] > .40 * F) & (A[m, 1] < .52 * F)).sum(); a = ((A[m, 1] > -.06) & (A[m, 1] < .05)).sum(); fr_.append(u / max(u + a, 1))
fr_ = np.array(fr_); kes = np.where(fr_ > .5)[0]; X_E = float(xs[kes.max()] + .05 + .03) if len(kes) else -9.2 * F
X1 = float(np.array(G['x+']['m'])[0]) * F; Z0 = float(np.array(G['z-']['m'])[2]) * F; Z1 = Pl * F
print('platform kenarı x', round(X_E, 3), 'bölge', round(X1, 3), round(Z0, 3), round(Z1, 3), 'oran örnek', np.round(fr_[::8], 2).tolist(), flush=True)
gx = np.arange(X_E, X1, AD); gz = np.arange(Z0, Z1, AD); XX, ZZ = np.meshgrid(gx, gz, indexing='xy'); Pm = np.c_[XX.ravel(), np.full(XX.size, Y0), ZZ.ravel()]
P = (((Pm / F - dl) @ Rl) / 2.10) @ Ms + o_
r = pycolmap.Reconstruction(str(MODEL)); fx, fy, cx, cy, k1, k2, p1, p2 = next(iter(r.cameras.values())).params; ims = sorted([i for i in r.images.values() if i.has_pose], key=lambda i: i.name)
ip, fr, BGR = [], [], []
for f, im in enumerate(ims):
    M = im.cam_from_world().matrix(); R, t = M[:3, :3], M[:3, 3]; C = ((2.10 * ((-R.T @ t) - o_) @ Ms.T) @ Rl.T + dl) * F
    pc = P @ R.T + t; z = pc[:, 2]; dh = np.hypot(Pm[:, 0] - C[0], Pm[:, 2] - C[2]); h = C[1] - Y0
    ok = (z > .35) & (z < 10) & ((h / np.hypot(h, dh)) > .16); xn, yn = pc[:, 0] / np.where(ok, z, 1), pc[:, 1] / np.where(ok, z, 1); ok &= (np.abs(xn) < 1.05) & (np.abs(yn) < .6)
    idx = np.where(ok)[0]
    if not len(idx): continue
    x, y = xn[idx], yn[idx]; r2 = x * x + y * y; rad = 1 + k1 * r2 + k2 * r2 * r2; u = fx * (x * rad + 2 * p1 * x * y + p2 * (r2 + 2 * x * x)) + cx; v = fy * (y * rad + 2 * p2 * x * y + p1 * (r2 + 2 * y * y)) + cy
    m = (u > 2) & (u < 1917) & (v > 2) & (v < 1077); idx, u, v = idx[m], np.rint(u[m]).astype(int), np.rint(v[m]).astype(int)
    px = cv2.blur(cv2.imread(str(W / 'k' / im.name)), (3, 3))[v, u]; mx, mn = px.max(1).astype(float), px.min(1).astype(float); iy = (mx > 90) & (mx < 252) & ((mx - mn) / np.maximum(mx, 1) < .36)
    ip.append(idx[iy].astype(np.int32)); fr.append(np.full(int(iy.sum()), f, np.int16)); BGR.append(px[iy])
ip, fr = np.concatenate(ip), np.concatenate(fr); BGR = np.concatenate(BGR).astype(np.float32); LL = np.log(.114 * BGR[:, 0] + .587 * BGR[:, 1] + .299 * BGR[:, 2]); print('örnek', len(ip), flush=True)
sec = (ip % 7 == 0); bx = np.zeros(len(ims)); a = np.full(len(P), np.nan)
for _ in range(6):
    s = pd.Series(LL[sec] - bx[fr[sec]]).groupby(ip[sec]).median(); a[:] = np.nan; a[s.index.values] = s.values
    k_ = np.isfinite(a[ip]) & sec; s = pd.Series(LL[k_] - a[ip[k_]]).groupby(fr[k_]).median(); bx[s.index.values] = s.values; bx -= np.median(bx)
LC = LL - bx[fr]; orta = pd.Series(LC).groupby(ip).transform('median').values; yk = np.abs(LC - orta) < .15
df = pd.DataFrame({'p': ip[yk], 'b': (BGR[yk, 0] * np.exp(-bx[fr[yk]])), 'g': (BGR[yk, 1] * np.exp(-bx[fr[yk]])), 'r': (BGR[yk, 2] * np.exp(-bx[fr[yk]]))}); say = df.groupby('p').b.size(); med = df.groupby('p').median()
Img = np.zeros((*XX.shape, 3), np.float32); Mask = np.ones(XX.shape, np.uint8); ids = med.index.values[say.reindex(med.index).values >= 4]; ix = np.unravel_index(ids, XX.shape); Img[ix] = med.loc[ids, ['b', 'g', 'r']].values; Mask[ix] = 0
# Sandalye altı: çevredeki zeminden 10%'dan koyu hücreler (sandalye ve gölge kalıntısı) yakın temiz zeminin rengiyle doldurulur
v0 = (Mask == 0).astype(np.float32); nb = lambda v_: cv2.GaussianBlur(Img * v_[..., None], (0, 0), 20) / np.maximum(cv2.GaussianBlur(v_, (0, 0), 20)[..., None], 1e-3)
Gri = lambda a_: .114 * a_[..., 0] + .587 * a_[..., 1] + .299 * a_[..., 2]
bg = nb(v0); kir = (v0 > 0) & (Gri(Img) < .90 * Gri(bg)); kir = cv2.dilate(kir.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0; bg2 = nb((v0 > 0).astype(np.float32) * (~kir).astype(np.float32)); ham0 = Img.copy(); Img[kir] = bg2[kir]; print('sandalye altı doldurulan %', round(float(kir.mean()) * 100, 1), flush=True)
ham = ham0; dolu = 1 - Mask; print('dolu hücre oranı', round(float(dolu.mean()) * 100, 1), flush=True)
Dl = cv2.inpaint(np.clip(Img, 0, 255).astype(np.uint8), Mask, 7, cv2.INPAINT_TELEA); Yum = cv2.GaussianBlur(Dl, (0, 0), .7)
ku = lambda a_: cv2.resize(a_, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
cv2.imwrite(str(O / 'zemin_harita.png'), np.vstack([ku(np.clip(ham, 0, 255).astype(np.uint8)), ku(Yum)]))
if '--yaz' in sys.argv:
    fld = t0.dtype.names; n = XX.size; yeni = np.zeros(n, t0.dtype); yeni['x'], yeni['z'] = XX.ravel().astype(np.float32), ZZ.ravel().astype(np.float32); yeni['y'] = np.float32(Y0)
    rgb = (Yum[..., ::-1].astype(np.float32) / 255.).reshape(-1, 3)
    for i in range(3): yeni[f'f_dc_{i}'] = (rgb[:, i] - .5) / .28209479
    yeni['opacity'] = np.float32(np.log(.995 / .005)); yeni['scale_0'] = yeni['scale_2'] = np.float32(np.log(SIG)); yeni['scale_1'] = np.float32(np.log(EPS)); yeni['rot_0'] = 1
    oz = {'platform_x': X_E, 'hucre': n, 'dolu_yuzde': round(float(dolu.mean()) * 100, 1), 'ornek': int(len(ip))}
    for ad in ('sinif1080', 'sinif1440'):
        t = PlyData.read(str(O / f'birlesik_{ad}_koridor_unity.ply'))['vertex'].data; B = np.c_[t['x'], t['y'], t['z']].astype(float); sil = (B[:, 0] > X_E) & (B[:, 0] < X1) & (B[:, 2] > Z0) & (B[:, 2] < Z1) & (B[:, 1] < Y0 + .03)
        c = O / f'birlesik_{ad}_koridor_gercek_zemin_unity.ply'; PlyData([PlyElement.describe(np.concatenate([t[~sil], yeni]), 'vertex')], byte_order='<').write(str(c)); oz[ad] = {'silinen': int(sil.sum()), 'toplam': int((~sil).sum()) + n, 'mb': round(c.stat().st_size / 1e6, 1)}; print(ad, oz[ad], flush=True)
    (O / 'gercek_zemin_ozet.json').write_text(json.dumps(oz, indent=1)); print('ZEMİN YAZILDI', flush=True)
print('BİTTİ', flush=True)
