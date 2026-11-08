"""Sınıf zeminindeki lekelerin kaynağı: gerçek karelerden ölçüm + model karşılaştırması (GPU gerekmez).

Zemin 10 cm ızgaraya bölünür; her ızgara noktası SfM pozlarıyla tüm karelere izdüşürülür ve renk örneklenir (sandalye gibi
doygun/koyu pikseller atılır). log(parlaklık) = nokta + kare + artık modeli medyanlarla çözülür. Ayrılan etkenler:
  * Pozlama / beyaz denge: kare terimi (kameranın kendi değişimi).
  * Lamba ve pencere yansıması: görüş ışını zeminde aynalanır, tavandaki lambaya ya da pencereye yakınlığına göre artık.
  * Çeken kişinin gölgesi: zemin noktasının kameraya yatay uzaklığına göre artık.
  * Model: Gaussian DC rengi ile gerçek medyan zemin rengi haritası; zemin üstü uçuşan parçalar.
Çıktı: derslik4_cekim2/logs/zemin_tani.png, zemin_tani.json. Kullanım: python3 zemin_tani.py
"""
import json
import subprocess
import sys
from pathlib import Path

import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pycolmap  # noqa: E402
from plyfile import PlyData  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

H6 = Path('/content/drive/MyDrive/Hafta 6 Çalışmaları'); S = H6 / 'derslik4_cekim2'; K = H6 / 'derslik4_koridor'; L = S / 'logs'; W = Path('/content/zt'); (W / 'k').mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(H6 / 'betikler_koridor')); sys.dont_write_bytecode = True
import unity_ply  # noqa: E402

SP = 'sfm/loma/sequential_loop/incremental'; AD = 0.10
subprocess.check_call(['rsync', '-a', f'{S / "frames_1080"}/', f'{W / "k"}/'])
J = json.loads((K / 'logs/hizalama.json').read_text()); Rl, dl = np.array(J['yatay']['Rl']), np.array(J['yatay']['dl'])
MODEL = S / SP / 'sparse' / json.load(open(S / SP / 'map.json'))['models'][0]['model']
Ms, o_, kutu, _ = unity_ply.hedef_cerceve(MODEL, 2.10)
r = pycolmap.Reconstruction(str(MODEL)); fx, fy, cx, cy, k1, k2, p1, p2 = next(iter(r.cameras.values())).params
gx = np.arange(-9.2, 9.0, AD); gz = np.arange(-7.2, 7.25, AD); XX, ZZ = np.meshgrid(gx, gz, indexing='xy'); Pu = np.c_[XX.ravel(), np.zeros(XX.size), ZZ.ravel()]
P = (((Pu - dl) @ Rl) / 2.10) @ Ms + o_
ims = sorted([im for im in r.images.values() if im.has_pose], key=lambda i: i.name); Cu = []
ip, fr, lum, rg, bg = [], [], [], [], []; gor, kabul = np.zeros(len(P)), np.zeros(len(P))
for f, im in enumerate(ims):
    M = im.cam_from_world().matrix(); R, t = M[:3, :3], M[:3, 3]; Cu.append((2.10 * ((-R.T @ t) - o_) @ Ms.T) @ Rl.T + dl)
    pc = P @ R.T + t; z = pc[:, 2]; ok = (z > .4) & (z < 15)
    xn, yn = pc[:, 0] / np.where(ok, z, 1), pc[:, 1] / np.where(ok, z, 1); ok &= (np.abs(xn) < 1.05) & (np.abs(yn) < .6)
    idx = np.where(ok)[0]
    if not len(idx): continue
    x, y = xn[idx], yn[idx]; r2 = x * x + y * y; rad = 1 + k1 * r2 + k2 * r2 * r2
    u = fx * (x * rad + 2 * p1 * x * y + p2 * (r2 + 2 * x * x)) + cx; v = fy * (y * rad + 2 * p2 * x * y + p1 * (r2 + 2 * y * y)) + cy
    m = (u > 3) & (u < 1916) & (v > 3) & (v < 1076); idx, u, v = idx[m], np.rint(u[m]).astype(int), np.rint(v[m]).astype(int)
    img = cv2.blur(cv2.imread(str(W / 'k' / im.name)), (5, 5)); px = img[v, u].astype(float) + 1
    mx, mn = px.max(1), px.min(1); gor[idx] += 1; iyi = (mx > 64) & (mx < 250) & ((mx - mn) / mx < .35)
    kabul[idx[iyi]] += 1; idx, px = idx[iyi], px[iyi]
    b, g, rr = px.T; ip.append(idx.astype(np.int32)); fr.append(np.full(len(idx), f, np.int32)); lum.append(np.log((.114 * b + .587 * g + .299 * rr)).astype(np.float32)); rg.append(np.log(rr / g).astype(np.float32)); bg.append(np.log(b / g).astype(np.float32))
Cu = np.array(Cu); ip, fr = np.concatenate(ip), np.concatenate(fr); lum, rg, bg = np.concatenate(lum), np.concatenate(rg), np.concatenate(bg)
print('örnek', len(ip), flush=True)


def coz(y):
    a = np.zeros(len(P)); b = np.zeros(len(ims))
    for _ in range(8):
        a[:] = np.nan; s = pd.Series(y - b[fr]).groupby(ip).median(); a[s.index.values] = s.values
        s = pd.Series(y - a[ip]).groupby(fr).median(); b[s.index.values] = s.values; b -= np.median(b)
    return a, b


a, b = coz(lum); res = lum - a[ip] - b[fr]; _, b_rg = coz(rg); _, b_bg = coz(bg)
Y = lambda v: round(float(v) * 100, 2)  # log farkı -> yaklaşık %
oz = {'poz_std_yuzde': Y(np.std(b)), 'poz_p5_p95_yuzde': [Y(np.percentile(b, 5)), Y(np.percentile(b, 95))], 'poz_ardisik_medyan_yuzde': Y(np.median(np.abs(np.diff(b)))), 'poz_ardisik_p99_yuzde': Y(np.percentile(np.abs(np.diff(b)), 99)),
      'wb_rg_std_yuzde': Y(np.std(b_rg)), 'wb_bg_std_yuzde': Y(np.std(b_bg)), 'artik_std_yuzde': Y(np.std(res)), 'artik_p5_p95_yuzde': [Y(np.percentile(res, 5)), Y(np.percentile(res, 95))], 'ornek': int(len(res))}
v = PlyData.read(str(S / 'runs/unity/derslik4_cekim2_1440big_H2_kapi_acik_unity.ply'))['vertex'].data
G = np.c_[v['x'], v['y'], v['z']].astype(float); op = 1 / (1 + np.exp(-v['opacity'].astype(float))); dc = .5 + .28209479 * np.c_[v['f_dc_0'], v['f_dc_1'], v['f_dc_2']].astype(float); gl = np.clip((.299 * dc[:, 0] + .587 * dc[:, 1] + .114 * dc[:, 2]), 0, 1)
sA = np.exp(np.c_[v['scale_0'], v['scale_1'], v['scale_2']].astype(float)); sA = np.sort(sA, 1); alan = sA[:, 2] * sA[:, 1]; sh = np.sum([v[f'f_rest_{i}'].astype(float) ** 2 for i in range(45)], 0)
ms = (op > .5) & (gl > .9) & (G[:, 1] > 2.6); H = float(np.median(G[ms, 1])); ty = cKDTree(G[ms][:, [0, 2]])
zp = float(np.percentile(G[(op > .5) & (G[:, 2] < -6.5), 2], 20)); mw = (op > .5) & (gl > .55) & (np.abs(G[:, 2] - zp) < .8) & (G[:, 1] > .9) & (G[:, 1] < 4.2); tw = cKDTree(G[mw][:, [0, 1]])
oz['isik_kot_m'] = round(H, 2); oz['pencere_duzlem_z_m'] = round(zp, 2); oz['isik_nokta'] = int(ms.sum()); oz['pencere_nokta'] = int(mw.sum())
Pi = Pu[ip]; Cf = Cu[fr]; dh = np.hypot(Pi[:, 0] - Cf[:, 0], Pi[:, 2] - Cf[:, 2]); Cm = Cf * [1, -1, 1]; d = Pi - Cm
s_ = (H - Pi[:, 1]) / d[:, 1]; dI, _ = ty.query(np.c_[Pi[:, 0] + s_ * d[:, 0], Pi[:, 2] + s_ * d[:, 2]], workers=-1)
sw = (zp - Pi[:, 2]) / np.where(np.abs(d[:, 2]) < 1e-6, 1e-6, d[:, 2]); hit = (sw > 0); yw = Pi[:, 1] + sw * d[:, 1]; hit &= (yw > .9) & (yw < 4.2); dW = np.full(len(ip), np.inf); dW[hit] = tw.query(np.c_[Pi[hit, 0] + sw[hit] * d[hit, 0], yw[hit]], workers=-1)[0]


def bin_tab(x, sinir, m):
    out = []
    for i in range(len(sinir) - 1):
        k = m & (x >= sinir[i]) & (x < sinir[i + 1])
        out.append({'aralik': [sinir[i], sinir[i + 1]], 'n': int(k.sum()), 'artik_medyan_yuzde': Y(np.median(res[k])) if k.sum() > 50 else None})
    return out


uzak = dh > 2.5
oz['lamba'] = bin_tab(dI, [0, .15, .3, .6, 1, 2, 4, 99], uzak & ~np.isfinite(dW)); oz['pencere'] = bin_tab(dW, [0, .15, .4, .8, 1.5, 3, 99], uzak & (dI > 1.0)); oz['golge'] = bin_tab(dh, [0, .4, .7, 1, 1.5, 2, 3, 5, 8, 20], (dI > 1.) & ~(dW < 1.5))
Pk = pd.DataFrame({'p': ip, 'r': res}); q = Pk.groupby('p').r.quantile([.1, .9]).unstack(); dag = np.full(len(P), np.nan); dag[q.index.values] = (q[.9] - q[.1]).values
n_x, n_z = XX.shape[1], XX.shape[0]; kab = kabul / np.maximum(gor, 1); print('kabul oranı yüzdelik', np.nanpercentile(kab[gor > 25], [10, 25, 50, 75, 90]).round(2), flush=True); ciplak = (kab > .55) & (gor > 25) & np.isfinite(a) & (np.exp(np.nan_to_num(a)) / 255 > .55)
def harita(X, w, deger=None):
    ix = np.clip(np.floor((X[:, 0] - (gx[0] - AD / 2)) / AD).astype(int), -1, n_x); iz = np.clip(np.floor((X[:, 2] - (gz[0] - AD / 2)) / AD).astype(int), -1, n_z); k = (ix >= 0) & (ix < n_x) & (iz >= 0) & (iz < n_z)
    A = np.zeros((n_z, n_x)); B = np.zeros((n_z, n_x)); np.add.at(A, (iz[k], ix[k]), w[k]); np.add.at(B, (iz[k], ix[k]), (deger[k] if deger is not None else 1) * w[k]); return A, B
yer = (np.abs(G[:, 1]) < .08) & (op > .2); W_y, D_y = harita(G[yer], (op * alan)[yer], gl[yer]); W_s, S_y = harita(G[yer], (op * alan)[yer], sh[yer])
gercek = np.full(XX.shape, np.nan); gercek[ciplak.reshape(XX.shape)] = (np.exp(a) / 255).reshape(XX.shape)[ciplak.reshape(XX.shape)]
mdl = D_y / np.where(W_y > 1e-9, W_y, np.nan); ora = np.log(mdl / gercek); yuk = (G[:, 1] > .12) & (G[:, 1] < 1.5) & (op > .2); W_u, _ = harita(G[yuk], op[yuk]); shm = S_y / np.where(W_s > 1e-9, W_s, np.nan)
g_ = np.isfinite(ora); oz['model_gercek'] = {'hucre': int(g_.sum()), 'medyan_oran_yuzde': Y(np.nanmedian(ora)), 'std_yuzde': Y(np.nanstd(ora)), 'en_az_10_koyu_yuzde': Y(np.mean(ora[g_] < -.10)), 'en_az_20_koyu_yuzde': Y(np.mean(ora[g_] < -.20))}
if g_.sum() > 100:
    kot = ora[g_] < -.15; ug = W_u[g_]
    oz['leke_iliski'] = {'gercek_dagilim_koyu_hucre': Y(np.nanmedian(dag.reshape(XX.shape)[g_][kot])), 'gercek_dagilim_diger': Y(np.nanmedian(dag.reshape(XX.shape)[g_][~kot])), 'ucusan_koyu_hucre_toplam_op': round(float(np.median(ug[kot])), 3), 'ucusan_diger': round(float(np.median(ug[~kot])), 3), 'SH_koyu': float(np.nanmedian(shm[g_][kot])), 'SH_diger': float(np.nanmedian(shm[g_][~kot]))}
(L / 'zemin_tani.json').write_text(json.dumps(oz, indent=1, ensure_ascii=False)); print(json.dumps(oz, ensure_ascii=False), flush=True)
fig, ax = plt.subplots(2, 4, figsize=(20, 9)); e = [gx[0], gx[-1], gz[-1], gz[0]]
for a_, im_, bas, vm in ((ax[0, 0], gercek, 'Gerçek zemin (medyan renk, 10 cm)', (.45, .95)), (ax[0, 1], mdl, 'Model zemin (DC renk)', (.45, .95))):
    p = a_.imshow(im_, extent=e, cmap='gray', vmin=vm[0], vmax=vm[1]); a_.set_title(bas); plt.colorbar(p, ax=a_, fraction=.03)
p = ax[0, 2].imshow(ora * 100, extent=e, cmap='RdBu', vmin=-40, vmax=40); ax[0, 2].set_title('Model / gerçek (%; mavi: model daha parlak)'); plt.colorbar(p, ax=ax[0, 2], fraction=.03)
p = ax[0, 3].imshow(np.log1p(W_u), extent=e, cmap='magma'); ax[0, 3].set_title('Zemin üstü Gaussian (0,12–1,5 m)'); plt.colorbar(p, ax=ax[0, 3], fraction=.03)
ax[1, 0].plot(b * 100, lw=.6); ax[1, 0].plot(b_rg * 100, lw=.4, label='R/G'); ax[1, 0].plot(b_bg * 100, lw=.4, label='B/G'); ax[1, 0].set_title('Kare parlaklığı ve beyaz denge (%)'); ax[1, 0].legend()
for a_, k_, bas, xl in ((ax[1, 1], 'golge', 'Kameraya yatay uzaklık (gölge)', 'm'), (ax[1, 2], 'lamba', 'Yansıyan ışın, lambaya uzaklık', 'm'), (ax[1, 3], 'pencere', 'Yansıyan ışın, pencereye uzaklık', 'm')):
    t = [x for x in oz[k_] if x['artik_medyan_yuzde'] is not None]; a_.plot([(x['aralik'][0] + min(x['aralik'][1], 12)) / 2 for x in t], [x['artik_medyan_yuzde'] for x in t], 'o-'); a_.axhline(0, color='k', lw=.5); a_.set_title(bas); a_.set_xlabel(xl); a_.set_ylabel('zemin parlaklığı farkı (%)'); a_.grid(alpha=.3)
fig.tight_layout(); fig.savefig(L / 'zemin_tani.png', dpi=95); print('TANI BİTTİ', flush=True)
