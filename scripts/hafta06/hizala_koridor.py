"""Koridor modelini sınıf modelinin Unity çerçevesine taşır (hizalama, eğitim gerekmez; Colab L4, COLMAP SIFT).

Koridor videosu K3 kapısından ~2 m içeri girer; 130-300 numaralı kareler sınıf videosuyla ortak bölgeyi görür.
  1. SIFT: tüm sınıf kareleri + koridorun 130-300 kareleri. Kaba eşleştirme ile ortak görüşlü sınıf kareleri bulunur.
  2. Bu karelerle küçük bir ortak SfM kurulur (mini). Aynı kameralar mini-sınıf ve mini-koridor modellerinde vardır;
     kamera merkezlerinden RANSAC + Umeyama ile iki benzerlik dönüşümü, bunların bileşiminden koridor -> sınıf çıkar.
  3. Koridorun Unity ply'ları sınıf Unity çerçevesine dönüştürülür (konum, ölçek, yönelim, küresel harmonikler).
  4. Kapı duvarı düzleminde kırpma: koridorun sınıf içindeki kısmı ve sınıfın kapı duvarı arkasındaki payı atılır.
Bağımsız denetimler: iki zemin düzlemi arasındaki eğim ve kapıdaki kot farkı; ölçüm hizalamada kullanılmaz.
Çıktı: derslik4_koridor/runs/unity/koridor_*_sinif_cerceve_unity.ply, derslik4_cekim2/runs/unity/*_kapi_kirpik_unity.ply,
       derslik4_koridor/logs/hizalama.json, hizalama_ust.png. İlerleme: logs/hizala.log
"""
import json
import os
import shutil
import site
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

H6 = Path('/content/drive/MyDrive/Hafta 6 Çalışmaları'); S = H6 / 'derslik4_cekim2'; K = H6 / 'derslik4_koridor'
L = K / 'logs'; W = Path('/content/hz'); IM = W / 'images'; COLMAP = '/content/colmap/bin/colmap'; CUDA = '/usr/local/cuda-12.8'
TGZ = H6 / 'kurulum/colmap_4.2.1_u2404_cu128_l4.tgz'; SP = 'sfm/loma/sequential_loop/incremental'
KS_M = 2.10            # sınıf ölçeği, m/birim (tahmini; mezura ile güncellenecek)
ARALIK = range(130, 301)
KIRPMA_PAY = 0.08      # m, kapı duvarı iç yüzeyinin arkası
W.mkdir(exist_ok=True)


def say(m):
    s = time.strftime('%F %T') + ' ' + m; print(s, flush=True)
    with open(L / 'hizala.log', 'a') as f: f.write(s + chr(10))


def kos(*a, log='colmap.log', env=None):
    t = time.time()
    with open(W / log, 'a') as f:
        rc = subprocess.call([str(x) for x in a], stdout=f, stderr=subprocess.STDOUT, env=env)
    if rc:
        shutil.copy(W / log, L / f'hizala_{log}'); say(f'HATA rc={rc}: {a[:2]}'); sys.exit(1)
    return (time.time() - t) / 60


say('başladı; COLMAP kuruluyor')
kur = f'''set -e
pip install -q nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cufft-cu12 nvidia-cuda-runtime-cu12 nvidia-curand-cu12 nvidia-cusparse-cu12 nvidia-cusolver-cu12 nvidia-nvjitlink-cu12 pycolmap-cuda12==4.2.1 plyfile scipy matplotlib
tar xzf "{TGZ}" -C /content
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libboost-program-options-dev libgoogle-glog-dev libopenimageio-dev libmetis-dev libsqlite3-dev libceres-dev libcurl4-openssl-dev libcgal-dev libglew-dev libboost-graph1.83.0 libboost-regex1.83.0 > /dev/null
if [ ! -x {CUDA}/bin/nvcc ]; then
  wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb -O /tmp/ck.deb
  dpkg -i /tmp/ck.deb; apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq cuda-toolkit-12-8 > /dev/null
fi
'''
(W / 'kur.sh').write_text(kur)
if not Path(COLMAP).exists():
    say(f'kurulum {kos("bash", W / "kur.sh", log="kurulum.log"):.1f} dk')
libs = [str(d / 'lib') for sp in site.getsitepackages() if (Path(sp) / 'nvidia').is_dir() for d in sorted((Path(sp) / 'nvidia').iterdir()) if (d / 'lib').is_dir()]
E = {**os.environ, 'LD_LIBRARY_PATH': ':'.join(libs + ['/content/colmap/lib', f'{CUDA}/lib64', os.environ.get('LD_LIBRARY_PATH', '')])}
os.environ['LD_LIBRARY_PATH'] = E['LD_LIBRARY_PATH']
sys.path.insert(0, str(H6 / 'betikler_koridor'))
sys.dont_write_bytecode = True
import numpy as np  # noqa: E402
import pycolmap  # noqa: E402
from plyfile import PlyData, PlyElement  # noqa: E402
from scipy.spatial.transform import Rotation  # noqa: E402
import unity_ply  # noqa: E402

# --- Kareler
(IM / 'sinif').mkdir(parents=True, exist_ok=True); (IM / 'koridor').mkdir(exist_ok=True)
subprocess.check_call(['rsync', '-a', f'{S / "frames_1080"}/', f'{IM / "sinif"}/'])
kor = [f'{i:04d}.jpg' for i in ARALIK if i % 2 == 0]
for n in kor:
    shutil.copy(K / 'frames_1080' / n, IM / 'koridor' / n)
sin = sorted(p.name for p in (IM / 'sinif').glob('*.jpg'))
say(f'kareler: sınıf {len(sin)}, koridor {len(kor)}')
if len(sin) != 1500: say('HATA sınıf kare sayısı'); sys.exit(1)


def yaz(ad, satir):
    (W / ad).write_text(chr(10).join(satir) + chr(10)); return W / ad


DB = W / 'hz.db'  # yeniden çalıştırmada biten çıkarma ve eşleştirmeler atlanır
tum = [f'sinif/{n}' for n in sin] + [f'koridor/{n}' for n in kor]
dk = 0 if DB.exists() else kos(COLMAP, 'feature_extractor', '--database_path', DB, '--image_path', IM, '--image_list_path', yaz('tum.txt', tum),
         '--ImageReader.single_camera_per_folder', 1, '--ImageReader.camera_model', 'OPENCV', '--FeatureExtraction.type', 'SIFT', env=E)
say(f'SIFT çıkarma {dk:.1f} dk')


def esle(ad, cift):
    if (W / (ad + '.ok')).exists():
        say(f'{ad}: atlandı (tamam)'); return
    dk = kos(COLMAP, 'matches_importer', '--database_path', DB, '--match_list_path', yaz(ad, [f'{a} {b}' for a, b in cift]), '--match_type', 'pairs',
             '--FeatureMatching.type', 'SIFT_BRUTEFORCE', env=E)
    say(f'{ad}: {len(cift)} çift, {dk:.1f} dk')
    (W / (ad + '.ok')).touch()


# --- 1. Kaba arama: koridorun her 2. seçili karesi x sınıfın her 3. karesi
esle('kaba.txt', [(f'koridor/{k}', f'sinif/{s}') for k in kor[::2] for s in sin[::3]])
con = sqlite3.connect(DB); ad = dict(con.execute('select image_id, name from images')); puan = {}
for pid, rows in con.execute('select pair_id, rows from two_view_geometries where rows >= 30'):
    i2 = pid % 2147483647; i1 = (pid - i2) // 2147483647
    a, b = ad[i1], ad[i2]
    if a.split('/')[0] != b.split('/')[0]:
        s = a if a.startswith('sinif') else b
        puan[s] = puan.get(s, 0) + rows
con.close()
say(f'ortak görüşlü sınıf karesi: {len(puan)}, en yüksek puanlar: {sorted(puan.values())[-5:]}')
if len(puan) < 15: say('HATA ortak görüş az'); sys.exit(1)
sec = set()
for s in sorted(puan, key=puan.get)[-50:]:
    n = int(s[6:10])
    sec |= {f'sinif/{m:04d}.jpg' for m in (n - 1, n, n + 1) if 1 <= m <= 1500}
sec = sorted(sec)[:150]; kk = [f'koridor/{k}' for k in kor]; mini = sec + kk
say(f'mini SfM: sınıf {len(sec)}, koridor {len(kk)} kare')

# --- 2. Mini SfM
esle('mini.txt', [(mini[i], mini[j]) for i in range(len(mini)) for j in range(i + 1, len(mini))])
O = W / 'mini'; shutil.rmtree(O, ignore_errors=True); O.mkdir()
dk = kos(COLMAP, 'mapper', '--database_path', DB, '--image_path', IM, '--Mapper.image_list_path', yaz('mini_liste.txt', mini), '--output_path', O, env=E)
en = None
for d in sorted(p for p in O.iterdir() if p.is_dir()):
    r = pycolmap.Reconstruction(str(d)); adlar = [im.name for im in r.images.values() if im.has_pose]
    n = (sum(a.startswith('sinif') for a in adlar), sum(a.startswith('koridor') for a in adlar))
    say(f'mini model {d.name}: sınıf {n[0]}, koridor {n[1]}, nokta {r.num_points3D()}')
    if en is None or min(n) > min(en[1]): en = (r, n)
say(f'mini mapper {dk:.1f} dk')
if en is None or min(en[1]) < 15: say('HATA mini model iki videoyu birleştiremedi'); sys.exit(1)
rm = en[0]


def merkezler(r, on=''):
    return {on + im.name: (np.array(im.projection_center()), im.cam_from_world().rotation.matrix()) for im in r.images.values() if im.has_pose}


def model_yolu(D):
    return D / SP / 'sparse' / json.load(open(D / SP / 'map.json'))['models'][0]['model']


MS, MK = model_yolu(S), model_yolu(K)
cm, cs, ck = merkezler(rm), merkezler(pycolmap.Reconstruction(str(MS)), 'sinif/'), merkezler(pycolmap.Reconstruction(str(MK)), 'koridor/')


def umeyama(x, y):
    mx, my = x.mean(0), y.mean(0); X, Y = x - mx, y - my
    U, D, Vt = np.linalg.svd(Y.T @ X / len(x))
    F = np.eye(3); F[2, 2] = np.sign(np.linalg.det(U @ Vt))
    R = U @ F @ Vt; s = np.trace(np.diag(D) @ F) / (X ** 2).sum(1).mean()
    return s, R, my - s * R @ mx


def ransac(hedef, onek):
    ad_ = [n for n in cm if n.startswith(onek) and n in hedef]
    x = np.array([cm[n][0] for n in ad_]); y = np.array([hedef[n][0] for n in ad_])
    esik = 0.02 * np.median(np.linalg.norm(y - np.median(y, 0), axis=1)); rng = np.random.default_rng(0); en_ = None
    for _ in range(3000):
        i = rng.choice(len(x), 3, replace=False); s, R, t = umeyama(x[i], y[i])
        e = np.linalg.norm(s * x @ R.T + t - y, axis=1); ic = e < esik
        if en_ is None or ic.sum() > en_.sum(): en_ = ic
    s, R, t = umeyama(x[en_], y[en_]); e = np.linalg.norm(s * x[en_] @ R.T + t - y[en_], axis=1)
    # Yönelim denetimi: R_hedef = R_mini R^T olmalı (cam_from_world)
    ac = [np.degrees(np.arccos(np.clip((np.trace(hedef[n][1] @ (cm[n][1] @ R.T).T) - 1) / 2, -1, 1))) for n, k in zip(ad_, en_) if k]
    return s, R, t, {'n': len(ad_), 'ic': int(en_.sum()), 'rms_birim': float(np.sqrt((e ** 2).mean())), 'yonelim_medyan_der': float(np.median(ac))}


As, Ar, At, ai = ransac(cs, 'sinif/'); Bs, Br, Bt, bi = ransac(ck, 'koridor/')
c = As / Bs; R = Ar @ Br.T; tau = At - c * R @ Bt
say('mini->sınıf ' + json.dumps(ai) + ' | mini->koridor ' + json.dumps(bi))

# --- 3. Unity çerçevesi
Ms, os_, kutu, _ = unity_ply.hedef_cerceve(MS, KS_M)
kor_json = json.loads((K / 'runs/unity/koridor_1440_big_unity.json').read_text()); Kk = kor_json['olcek_cm_birim'] / 100
Mk, ok, _, _ = unity_ply.hedef_cerceve(MK, Kk)
g = KS_M * c / Kk; Q = Ms @ R @ Mk.T; d = KS_M * Ms @ (c * R @ ok + tau - os_)
if np.linalg.det(Q) < 0: say('HATA Q yansıma içeriyor'); sys.exit(1)
x0, x1, z0, z1 = kutu[0], kutu[2], -kutu[3], -kutu[1]
Cu = np.array([KS_M * Ms @ (c * R @ v[0] + tau - os_) for v in ck.values()])
disari = {'-x': (Cu[:, 0] < x0).sum(), '+x': (Cu[:, 0] > x1).sum(), '-z': (Cu[:, 2] < z0).sum(), '+z': (Cu[:, 2] > z1).sum()}
yan = '+z'  # K3 kapısı +z duvarında: koridor kamera yolu sınıfa bu duvardan giriyor (hizalama_ust.png); koridor L şeklinde olduğundan sayım yanıltıyor
ax = 0 if yan[1] == 'x' else 2; isr = 1 if yan[0] == '+' else -1; ky = (x0 if isr < 0 else x1) if ax == 0 else (z0 if isr < 0 else z1)
say(f'sınıf kutusu x [{x0:.2f},{x1:.2f}] z [{z0:.2f},{z1:.2f}]; koridor kameraları dışarıda: ' + str({k: int(v) for k, v in disari.items()}) + f'; kapı duvarı {yan}')


def oku(p):
    v = PlyData.read(str(p))['vertex']; return v.data, np.c_[v['x'], v['y'], v['z']].astype(np.float64), np.asarray(v['opacity'], dtype=np.float64)


# Kapı duvarı iç yüzü: sınıf Gaussian'larının kutu kenarı çevresindeki yoğunluk tepesi
yol_s = [S / 'runs/unity/derslik4_cekim2_H2_unity.ply', S / 'runs/unity/derslik4_cekim2_1440big_H2_unity.ply']
_, Xs, ops = oku(yol_s[0]); on = 1 / (1 + np.exp(-ops)) > 0.5
b = on & (Xs[:, 1] > 0.3) & (Xs[:, 1] < 2.5) & (np.abs(Xs[:, ax] - ky) < 1.0)
hh, kk_ = np.histogram(Xs[b, ax], bins=np.arange(ky - 1.0, ky + 1.0, 0.02)); hh = np.convolve(hh, np.ones(3) / 3, mode='same')
P = float(kk_[np.argmax(hh)] + 0.01); say(f'kapı duvarı iç yüzü {yan[1]} = {P:.3f} m (kutu kenarı {ky:.3f})')
yanal = 2 if ax == 0 else 0; ya, yb = (z0, z1) if ax == 0 else (x0, x1)
# Yatay düzeltme: sınıf çerçevesinin y=0'ı platform üzerinden kurulmuş ve ~1,5° eğik. Gerçek düşey olarak uzun koridor zemininin normali alınır;
# iki model aynı dönüşümle yatay yapılır ve koridor zemini y=0'a indirilir (göreli hizalama değişmez).
u = Q[:, 1]; ey = np.array([0., 1., 0.]); v = np.cross(u, ey); Vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
Rl = np.eye(3) + Vx + Vx @ Vx / (1 + u @ ey); h = (Rl @ d)[1]; dl = np.array([0., -h, 0.])
egim = float(np.degrees(np.arccos(np.clip(u[1], -1, 1))))
say(f'yatay düzeltme: {egim:.2f}°, kot kaydırma {-h * 100:.1f} cm')


def yaz_ply(d_, cikti):
    PlyData([PlyElement.describe(d_, 'vertex')], byte_order='<').write(str(cikti))
    return cikti.stat().st_size / 1e6


def donustur(t, X, g_, Q_, d_):
    t = t.copy(); Xn = g_ * X @ Q_.T + d_
    t['x'], t['y'], t['z'] = Xn.T.astype(np.float32)
    for i in range(3): t[f'scale_{i}'] = t[f'scale_{i}'] + np.float32(np.log(g_))
    q = np.c_[t['rot_0'], t['rot_1'], t['rot_2'], t['rot_3']].astype(np.float64); q /= np.linalg.norm(q, axis=1, keepdims=True)
    qn = Rotation.from_matrix(Q_ @ Rotation.from_quat(q[:, [1, 2, 3, 0]]).as_matrix()).as_quat()[:, [3, 0, 1, 2]]
    for i in range(4): t[f'rot_{i}'] = qn[:, i].astype(np.float32)
    fr = sorted([a for a in t.dtype.names if a.startswith('f_rest_')], key=lambda a: int(a[7:]))
    if len(fr) == 45:
        Sx = np.stack([t[a] for a in fr], 1).astype(np.float64).reshape(-1, 3, 15) @ unity_ply.sh_matrisi(Q_).T
        for j, a in enumerate(fr): t[a] = Sx.reshape(-1, 45)[:, j].astype(np.float32)
    return t


ozet = {}
for ad_s in ('koridor_1440_big', 'koridor_1440_big_H2'):
    d0, X, op = oku(K / 'runs/unity' / f'{ad_s}_unity.ply')
    Xn = g * X @ Q.T + d
    ic_ = (isr * Xn[:, ax] < isr * P + KIRPMA_PAY) & (Xn[:, yanal] > ya + 0.1) & (Xn[:, yanal] < yb - 0.1)
    t = donustur(d0[~ic_], X[~ic_], g, Rl @ Q, Rl @ d + dl); Xt = np.c_[t['x'], t['y'], t['z']].astype(np.float64)
    mb = yaz_ply(t, K / 'runs/unity' / f'{ad_s}_sinif_cerceve_unity.ply')
    ozet[ad_s] = {'giris': int(len(X)), 'cikis': int(len(t)), 'mb': round(mb, 1)}; say(f'{ad_s}: {ozet[ad_s]}')
    if ad_s.endswith('H2'): XK, opK = Xt, op[~ic_]
for p in yol_s:
    d0, X, _ = oku(p); ic_ = isr * X[:, ax] < isr * P + KIRPMA_PAY
    mb = yaz_ply(donustur(d0[ic_], X[ic_], 1.0, Rl, dl), p.with_name(p.name.replace('_unity.ply', '_kapi_kirpik_unity.ply')))
    ozet[p.name] = {'giris': int(len(X)), 'cikis': int(ic_.sum()), 'mb': round(mb, 1)}; say(f'{p.name}: {ozet[p.name]}')

# --- 4. Denetimler (hizalamada kullanılmadı): yatay düzeltmeden sonra iki modelin zemin kotu
def tepe(y, lo=-0.5, hi=0.5):
    hh_, e = np.histogram(y, bins=np.arange(lo, hi, 0.02)); hh_ = np.convolve(hh_, np.ones(5) / 5, mode='same'); return round(float(e[np.argmax(hh_)] + .01), 2)


Xl = Xs[on] @ Rl.T + dl
sat = []
for x_ in range(-9, 9, 3):
    m = (Xl[:, 0] > x_) & (Xl[:, 0] < x_ + 3) & (Xl[:, 2] > -7) & (Xl[:, 2] < 7) & (Xl[:, 1] < 0.25) & (Xl[:, 1] > -0.5)
    sat.append((x_, tepe(Xl[m, 1])))
kk2 = XK[1 / (1 + np.exp(-opK)) > 0.5]; satk = []
for x_ in range(-18, -3, 3):
    m = (kk2[:, 0] > x_) & (kk2[:, 0] < x_ + 3) & (kk2[:, 2] > 8.6) & (kk2[:, 2] < 11) & (kk2[:, 1] < 0.25) & (kk2[:, 1] > -0.5)
    satk.append((x_, tepe(kk2[m, 1]) if m.sum() > 30 else None))
say(f'denetim, zemin kotu (m): sınıf {sat}; koridor {satk}; ölçek çarpanı g={g:.4f}')

import matplotlib  # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
rng = np.random.default_rng(0)
Xp = Xl; Xp = Xp[rng.choice(len(Xp), min(150000, len(Xp)), replace=False)]
Kp = XK[1 / (1 + np.exp(-opK)) > 0.5]; Kp = Kp[rng.choice(len(Kp), min(150000, len(Kp)), replace=False)]
f, a = plt.subplots(1, 2, figsize=(16, 8))
for g_, (i, j) in zip(a, ((0, 2), (ax, 1))):
    g_.scatter(Xp[:, i], Xp[:, j], s=.1, c='tab:blue', label='sınıf'); g_.scatter(Kp[:, i], Kp[:, j], s=.1, c='tab:orange', label='koridor')
    g_.set_xlabel('xyz'[i] + ' (m)'); g_.set_ylabel('xyz'[j] + ' (m)'); g_.set_aspect('equal'); g_.legend(markerscale=30); g_.grid(alpha=.3)
a[0].plot(Cu[:, 0], Cu[:, 2], 'k-', lw=.5)
a[1].axvline(P, color='r', lw=1, label='kapı duvarı'); a[1].set_ylim(-2, 7)
f.tight_layout(); f.savefig(L / 'hizalama_ust.png', dpi=110)
(L / 'hizalama.json').write_text(json.dumps({'mini_sinif': ai, 'mini_koridor': bi, 'kor_to_sinif': {'c': c, 'R': R.tolist(), 't': tau.tolist()},
                                             'unity': {'g': g, 'Q': Q.tolist(), 'd': d.tolist()}, 'kapi': {'yan': yan, 'P_m': P}, 'egim_der': egim, 'yatay': {'Rl': Rl.tolist(), 'dl': dl.tolist()}, 'zemin_sinif': sat, 'zemin_koridor': satk, 'ks_m': KS_M, 'kk_m': Kk, 'ozet': ozet}, indent=1))
say('HİZALAMA BİTTİ')
