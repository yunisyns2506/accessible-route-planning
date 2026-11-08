"""K3 kapısı sınıf çekiminde kapalı, koridor çekiminde açıktı: birleşik sahnede kapı bölgesi koridor modelinden alınır.

hizala_koridor.py'nin dönüşümleri (hizalama.json) kullanılır; hizalama yeniden hesaplanmaz. Ortak çerçeve yatay, zemin y=0.
  * Kapı yeri: sınıf modelinde +z duvarındaki koyu gri kapı kanadı (renk) + koridor kamera yolunun duvarı geçtiği x.
  * Kapı kutusu: kapı genişliği + pay, duvardan sınıf içine DERIN m, zeminden kapı üstü + pay.
  * Sınıf: kutunun içi ve kapı duvarının arkası atılır (kapalı kapı gider, açıklık kalır).
  * Koridor: sınıf içinde kalan kısmı atılır, kapı kutusunun içi tutulur (kanat ve açıklık iki yönden koridor modelinden gelir).
Çıktı: runs/unity/*_kapi_acik_unity.ply, logs/kapi_kontrol.png, logs/kapi.json. İlerleme: logs/hizala.log
"""
import json
import sys
import time
from pathlib import Path

H6 = Path('/content/drive/MyDrive/Hafta 6 Çalışmaları')
S = H6 / 'derslik4_cekim2'; K = H6 / 'derslik4_koridor'; L = K / 'logs'; SP = 'sfm/loma/sequential_loop/incremental'
DERIN = 1.3; PAY_X = 0.15; PAY_UST = 0.15; KIRPMA = 0.08
sys.path.insert(0, str(H6 / 'betikler_koridor')); sys.dont_write_bytecode = True
import numpy as np  # noqa: E402
import pycolmap  # noqa: E402
from plyfile import PlyData, PlyElement  # noqa: E402
from scipy.spatial.transform import Rotation  # noqa: E402
import unity_ply  # noqa: E402


def say(m):
    s = time.strftime('%F %T') + ' ' + m; print(s, flush=True)
    with open(L / 'hizala.log', 'a') as f: f.write(s + chr(10))


J = json.loads((L / 'hizalama.json').read_text())
g, Q, d = J['unity']['g'], np.array(J['unity']['Q']), np.array(J['unity']['d'])
Rl, dl = np.array(J['yatay']['Rl']), np.array(J['yatay']['dl']); c, R, tau = J['kor_to_sinif']['c'], np.array(J['kor_to_sinif']['R']), np.array(J['kor_to_sinif']['t'])
if J['kapi']['yan'] != '+z': say('HATA kapı duvarı +z değil'); sys.exit(1)
Qk, dk_ = Rl @ Q, Rl @ d + dl


def model_yolu(D):
    return D / SP / 'sparse' / json.load(open(D / SP / 'map.json'))['models'][0]['model']


Ms, os_, kutu, _ = unity_ply.hedef_cerceve(model_yolu(S), J['ks_m'])
x0, x1 = kutu[0], kutu[2]
r = pycolmap.Reconstruction(str(model_yolu(K)))
kam = sorted((im.name, np.array(im.projection_center())) for im in r.images.values() if im.has_pose)
Cu = np.array([J['ks_m'] * Ms @ (c * R @ v + tau - os_) for _, v in kam]) @ Rl.T + dl
Pl = float((np.array([(x0 + x1) / 2, 1.0, J['kapi']['P_m']]) @ Rl.T + dl)[2])
isaret = np.sign(Cu[:, 2] - Pl); gec = np.where(isaret[:-1] * isaret[1:] < 0)[0]
xg = [float(Cu[i, 0] + (Cu[i + 1, 0] - Cu[i, 0]) * (Pl - Cu[i, 2]) / (Cu[i + 1, 2] - Cu[i, 2])) for i in gec if abs(Cu[i + 1, 2] - Cu[i, 2]) < 3]
if not xg: say('HATA kamera yolu kapı düzlemini geçmiyor'); sys.exit(1)
xc = float(np.median(xg)); say(f'kapı düzlemi z={Pl:.3f} m; kamera geçişleri x={[round(v, 2) for v in xg]}, medyan {xc:.2f}')


def oku(p):
    t = PlyData.read(str(p))['vertex'].data
    return t, np.c_[t['x'], t['y'], t['z']].astype(np.float64), 1 / (1 + np.exp(-t['opacity'].astype(np.float64))), np.clip(np.c_[t['f_dc_0'], t['f_dc_1'], t['f_dc_2']] * 0.28209479 + 0.5, 0, 1)


yol_s = [S / 'runs/unity/derslik4_cekim2_H2_unity.ply', S / 'runs/unity/derslik4_cekim2_1440big_H2_unity.ply']
_, X0, op, rgb = oku(yol_s[0]); Xs = X0 @ Rl.T + dl
gri = (rgb.max(1) < 0.5) & (rgb.max(1) - rgb.min(1) < 0.12) & (op > 0.5)
b = gri & (np.abs(Xs[:, 2] - Pl) < 0.3) & (Xs[:, 1] > 0.4) & (Xs[:, 1] < 1.9)
h, e = np.histogram(Xs[b, 0], bins=np.arange(x0 - 1, x1 + 1, 0.05)); h = np.convolve(h, np.ones(3) / 3, mode='same')
yuksek = h > 0.15 * h.max(); ar, i = [], 0
while i < len(h):
    if yuksek[i]:
        j = i
        while j + 1 < len(h) and (yuksek[j + 1] or (j + 2 < len(h) and yuksek[j + 2])): j += 1
        ar.append((float(e[i]), float(e[j + 1]))); i = j + 1
    else:
        i += 1
ar = [a for a in ar if a[1] - a[0] > 0.5]
if not ar: say('HATA koyu kapı kanadı bulunamadı'); sys.exit(1)
xa, xb = min(ar, key=lambda a: 0 if a[0] <= xc <= a[1] else min(abs(a[0] - xc), abs(a[1] - xc)))
say(f'koyu bölgeler x: {[(round(a, 2), round(b_, 2)) for a, b_ in ar]}; seçilen kapı {xa:.2f}..{xb:.2f} ({xb - xa:.2f} m)')
if not 0.7 < xb - xa < 2.6: say('HATA kapı genişliği beklenmedik'); sys.exit(1)
m = gri & (Xs[:, 0] > xa) & (Xs[:, 0] < xb) & (np.abs(Xs[:, 2] - Pl) < 0.3) & (Xs[:, 1] > 0.4) & (Xs[:, 1] < 3.3)
ust = float(np.percentile(Xs[m, 1], 99)); XA, XB, UST = xa - PAY_X, xb + PAY_X, ust + PAY_UST
say(f'kapı üstü {ust:.2f} m; kutu x {XA:.2f}..{XB:.2f}, z {Pl - DERIN:.2f}..{Pl + KIRPMA:.2f}, y -0.2..{UST:.2f}')


def kutuda(X): return (X[:, 0] > XA) & (X[:, 0] < XB) & (X[:, 2] > Pl - DERIN) & (X[:, 2] < Pl + KIRPMA) & (X[:, 1] > -0.2) & (X[:, 1] < UST)


def donustur(t, X, g_, Q_, d_):
    t = t.copy(); Xn = g_ * X @ Q_.T + d_
    t['x'], t['y'], t['z'] = Xn.T.astype(np.float32)
    for i_ in range(3): t[f'scale_{i_}'] = t[f'scale_{i_}'] + np.float32(np.log(g_))
    q = np.c_[t['rot_0'], t['rot_1'], t['rot_2'], t['rot_3']].astype(np.float64); q /= np.linalg.norm(q, axis=1, keepdims=True)
    qn = Rotation.from_matrix(Q_ @ Rotation.from_quat(q[:, [1, 2, 3, 0]]).as_matrix()).as_quat()[:, [3, 0, 1, 2]]
    for i_ in range(4): t[f'rot_{i_}'] = qn[:, i_].astype(np.float32)
    fr = sorted([a for a in t.dtype.names if a.startswith('f_rest_')], key=lambda a: int(a[7:]))
    if len(fr) == 45:
        Sx = np.stack([t[a] for a in fr], 1).astype(np.float64).reshape(-1, 3, 15) @ unity_ply.sh_matrisi(Q_).T
        for j_, a in enumerate(fr): t[a] = Sx.reshape(-1, 45)[:, j_].astype(np.float32)
    return t


def yaz(t, p):
    PlyData([PlyElement.describe(t, 'vertex')], byte_order='<').write(str(p)); return round(p.stat().st_size / 1e6, 1)


oz = {}
for p in yol_s:
    t, X, _, _ = oku(p); Xl = X @ Rl.T + dl
    tut = (Xl[:, 2] < Pl + KIRPMA) & ~kutuda(Xl)
    cik = p.with_name(p.name.replace('_unity.ply', '_kapi_acik_unity.ply')); oz[p.name] = {'giris': len(X), 'kutudan_atilan': int(kutuda(Xl).sum()), 'cikis': int(tut.sum()), 'mb': yaz(donustur(t[tut], X[tut], 1.0, Rl, dl), cik)}
    say(f'{p.name}: {oz[p.name]}')
    if p == yol_s[0]: Xsc, rs = Xl[tut], np.clip(np.c_[t['f_dc_0'], t['f_dc_1'], t['f_dc_2']][tut] * 0.28209479 + 0.5, 0, 1); ops = 1 / (1 + np.exp(-t['opacity'][tut].astype(np.float64)))
for ad in ('koridor_1440_big', 'koridor_1440_big_H2'):
    t, X, _, _ = oku(K / 'runs/unity' / f'{ad}_unity.ply'); Xl = g * X @ Qk.T + dk_
    ic_ = (Xl[:, 2] < Pl + KIRPMA) & (Xl[:, 0] > x0 + 0.1) & (Xl[:, 0] < x1 - 0.1); tut = ~ic_ | kutuda(Xl)
    oz[ad] = {'giris': len(X), 'kutuda_tutulan': int(kutuda(Xl).sum()), 'cikis': int(tut.sum()), 'mb': yaz(donustur(t[tut], X[tut], g, Qk, dk_), K / 'runs/unity' / f'{ad}_kapi_acik_unity.ply')}
    say(f'{ad}: {oz[ad]}')
    if ad.endswith('H2'): Xkc, rk = Xl[tut], np.clip(np.c_[t['f_dc_0'], t['f_dc_1'], t['f_dc_2']][tut] * 0.28209479 + 0.5, 0, 1); opk = 1 / (1 + np.exp(-t['opacity'][tut].astype(np.float64)))

import matplotlib  # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
Xa, ca = np.vstack([Xsc[ops > .5], Xkc[opk > .5]]), np.vstack([rs[ops > .5], rk[opk > .5]])
f, a = plt.subplots(1, 3, figsize=(20, 7))
for ax_, (z_a, z_b, bas) in zip(a[:2], ((Pl - DERIN - .1, Pl, 'içeriden: sınıf tarafı, duvar düzleminin önü'), (Pl + .08, Pl + .8, 'dışarıdan: koridor tarafı'))):
    m = (Xa[:, 2] > z_a) & (Xa[:, 2] < z_b) & (Xa[:, 0] > XA - 2.5) & (Xa[:, 0] < XB + 2.5) & (Xa[:, 1] > -.3) & (Xa[:, 1] < 3.6)
    o = np.argsort(Xa[m, 2]); o = o if z_b > Pl + .1 else o[::-1]
    ax_.scatter(Xa[m, 0][o], Xa[m, 1][o], s=1.2, c=ca[m][o]); ax_.plot([XA, XB, XB, XA, XA], [0, 0, UST, UST, 0], 'r-', lw=1); ax_.set_title(bas); ax_.set_aspect('equal'); ax_.set_facecolor('k')
m = (Xsc[:, 0] > XA - 3) & (Xsc[:, 0] < XB + 3) & (np.abs(Xsc[:, 2] - Pl) < 3); n = (Xkc[:, 0] > XA - 3) & (Xkc[:, 0] < XB + 3) & (np.abs(Xkc[:, 2] - Pl) < 3)
a[2].scatter(Xsc[m, 0], Xsc[m, 2], s=.3, c='tab:blue', label='sınıf'); a[2].scatter(Xkc[n, 0], Xkc[n, 2], s=.3, c='tab:orange', label='koridor')
a[2].plot([XA, XB, XB, XA, XA], [Pl - DERIN, Pl - DERIN, Pl + KIRPMA, Pl + KIRPMA, Pl - DERIN], 'r-'); a[2].set_aspect('equal'); a[2].legend(markerscale=15); a[2].set_title('üstten')
f.tight_layout(); f.savefig(L / 'kapi_kontrol.png', dpi=100)
(L / 'kapi.json').write_text(json.dumps({'Pl': Pl, 'kutu': {'x': [XA, XB], 'z': [Pl - DERIN, Pl + KIRPMA], 'y': [-.2, UST]}, 'kapi_x': [xa, xb], 'ust': ust, 'ozet': oz}, indent=1))
say('KAPI BİTTİ')
