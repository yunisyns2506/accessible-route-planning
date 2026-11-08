"""Sınıf + koridor: mezura ölçeği, temizlik ve tek PLY (Unity'de tek nesne = tüm Gaussian'lar birlikte sıralanır).

Girdi: *_kapi_acik_unity.ply (kapi_ac.py; ortak yatay çerçeve, zemin y=0, 210 cm/birim).
Ölçek: 212,51 cm/birim (olcum_sonuc.py). Eşikler kuru çalıştırmayla seçildi, metre cinsindendir:
  opaklık < 0,05; en uzun eksen > 1,0 m; iğne (oran > 30 ve eksen > 0,15 m ya da oran > 15 ve eksen > 0,3 m);
  yalnız kalan (8 komşu ortalaması > 0,8 m); koridorda kamera yolundan > 15 m (avlu ötesi, görüş dışı).
Çıktı: Hafta 6 Çalışmaları/birlesik/. Kullanım: python3 birlestir.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pycolmap
from plyfile import PlyData, PlyElement
from scipy.spatial import cKDTree

H6 = Path('/content/drive/MyDrive/Hafta 6 Çalışmaları'); S = H6 / 'derslik4_cekim2'; K = H6 / 'derslik4_koridor'; O = H6 / 'birlesik'; O.mkdir(exist_ok=True)
sys.path.insert(0, str(H6 / 'betikler_koridor')); sys.dont_write_bytecode = True
import unity_ply  # noqa: E402

SP = 'sfm/loma/sequential_loop/incremental'; F = 212.51 / 210.0


def yol(D):
    return D / SP / 'sparse' / json.load(open(D / SP / 'map.json'))['models'][0]['model']


J = json.loads((K / 'logs/hizalama.json').read_text()); c, R, tau = J['kor_to_sinif']['c'], np.array(J['kor_to_sinif']['R']), np.array(J['kor_to_sinif']['t']); Rl, dl = np.array(J['yatay']['Rl']), np.array(J['yatay']['dl'])
Ms, o_, _, _ = unity_ply.hedef_cerceve(yol(S), 2.10)
C = np.array([im.projection_center() for im in pycolmap.Reconstruction(str(yol(K))).images.values() if im.has_pose]); YOL = ((2.10 * (c * C @ R.T + tau - o_) @ Ms.T) @ Rl.T + dl) * F


def temizle(p, koridor):
    t = PlyData.read(str(p))['vertex'].data.copy()
    for a in 'xyz': t[a] = t[a] * np.float32(F)
    for i in range(3): t[f'scale_{i}'] = t[f'scale_{i}'] + np.float32(np.log(F))
    X = np.c_[t['x'], t['y'], t['z']].astype(float); s = np.sort(np.exp(np.c_[t['scale_0'], t['scale_1'], t['scale_2']].astype(float)), 1); op = 1 / (1 + np.exp(-t['opacity'].astype(float)))
    oran = s[:, 2] / s[:, 1]; d8 = cKDTree(X).query(X, k=9, workers=-1)[0][:, 1:].mean(1)
    M = {'opaklik': op < .05, 'buyuk': s[:, 2] > 1., 'igne': ((oran > 30) & (s[:, 2] > .15)) | ((oran > 15) & (s[:, 2] > .3)), 'yalniz': d8 > .8}
    if koridor: M['uzak'] = cKDTree(YOL).query(X, workers=-1)[0] > 15
    at = np.logical_or.reduce(list(M.values()))
    oz = {'giris': len(t), 'cikis': int((~at).sum()), **{k: int(v.sum()) for k, v in M.items()}}
    print(p.name, oz, flush=True)
    return t[~at], oz


kor, ok = temizle(K / 'runs/unity/koridor_1440_big_H2_kapi_acik_unity.ply', True); ozet = {'olcek_cm_birim': 212.51, 'koridor': ok}
for ad, g in (('sinif1080', 'derslik4_cekim2_H2_kapi_acik_unity.ply'), ('sinif1440', 'derslik4_cekim2_1440big_H2_kapi_acik_unity.ply')):
    sin, os_ = temizle(S / 'runs/unity' / g, False)
    if sin.dtype != kor.dtype: raise SystemExit('alanlar farklı')
    cik = O / f'birlesik_{ad}_koridor_unity.ply'
    PlyData([PlyElement.describe(np.concatenate([sin, kor]), 'vertex')], byte_order='<').write(str(cik))
    ozet[ad] = {**os_, 'toplam': len(sin) + len(kor), 'mb': round(cik.stat().st_size / 1e6, 1)}; print(cik.name, ozet[ad], flush=True)
    v = PlyData.read(str(cik))['vertex']; A = np.c_[v['x'], v['y'], v['z']]; print('  aralık (m)', np.percentile(A, [1, 99], axis=0).round(2).tolist(), 'NaN', int(np.isnan(A).sum()), flush=True)
(O / 'birlesik_ozet.json').write_text(json.dumps(ozet, indent=1))
print('BİRLEŞTİRME BİTTİ', flush=True)
