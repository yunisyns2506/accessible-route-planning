"""Deney: sınıf zemininin altına yerleşmiş Gaussian'ları gerçek zemin düzlemine indirir (yeniden eğitim yok).

Yalnız sınıfın ana zemini (platform ve koridor dışarıda). y < -0,03 m olan Gaussian'lar:
  * y ~ [-0,008, 0] m (sıralama çakışmasın diye küçük dağılım),
  * şekli yatay düzleme izdüşürülür (kovaryansın xz bloğu korunur, normal yönünde 3 mm),
  * görüşe bağlı renk (f_rest) sıfırlanır: yansımayı taklit eden terimler zeminde kalmasın. Taban rengi (DC) ve opaklık aynı.
Girdi/çıktı: Hafta 6 Çalışmaları/birlesik/. Kullanım: python3 zemin_duzle.py
"""
import json
from pathlib import Path

import numpy as np
from plyfile import PlyData, PlyElement
from scipy.spatial.transform import Rotation

O = Path('/content/drive/MyDrive/Hafta 6 Çalışmaları/birlesik'); F = 212.51 / 210.0
X0, X1, Z0, Z1 = -9.2 * F, 9.0 * F, -7.2 * F, 7.4 * F; EPS = 0.003
rng = np.random.default_rng(0); ozet = {}
for ad in ('sinif1080', 'sinif1440'):
    t = PlyData.read(str(O / f'birlesik_{ad}_koridor_unity.ply'))['vertex'].data.copy()
    X = np.c_[t['x'], t['y'], t['z']].astype(float); bolge = (X[:, 0] > X0) & (X[:, 0] < X1) & (X[:, 2] > Z0) & (X[:, 2] < Z1)
    m = bolge & (X[:, 1] < -0.03); n = int(m.sum())
    q = np.c_[t['rot_1'][m], t['rot_2'][m], t['rot_3'][m], t['rot_0'][m]].astype(float); q /= np.linalg.norm(q, axis=1, keepdims=True)
    R = Rotation.from_quat(q).as_matrix(); s2 = np.exp(2 * np.c_[t['scale_0'][m], t['scale_1'][m], t['scale_2'][m]].astype(float))
    S = (R * s2[:, None, :]) @ R.transpose(0, 2, 1)
    A = np.empty((n, 2, 2)); A[:, 0, 0], A[:, 0, 1], A[:, 1, 0], A[:, 1, 1] = S[:, 0, 0], S[:, 0, 2], S[:, 2, 0], S[:, 2, 2]
    lam, v = np.linalg.eigh(A); lam = np.maximum(lam, 1e-8)
    e0 = np.c_[v[:, 0, 0], np.zeros(n), v[:, 1, 0]]; e2 = np.c_[v[:, 0, 1], np.zeros(n), v[:, 1, 1]]; e1 = np.cross(e2, e0)
    qn = Rotation.from_matrix(np.stack([e0, e1, e2], 2)).as_quat()
    t['y'][m] = rng.uniform(-.008, 0, n).astype(np.float32)
    for i, k in enumerate((1, 2, 3, 0)): t[f'rot_{k}'][m] = qn[:, i].astype(np.float32)
    t['scale_0'][m], t['scale_1'][m], t['scale_2'][m] = (.5 * np.log(lam[:, 0])).astype(np.float32), np.full(n, np.log(EPS), np.float32), (.5 * np.log(lam[:, 1])).astype(np.float32)
    for i in range(45): t[f'f_rest_{i}'][m] = 0
    c = O / f'birlesik_{ad}_koridor_zemin_duz_unity.ply'; PlyData([PlyElement.describe(t, 'vertex')], byte_order='<').write(str(c))
    Y = np.asarray(t['y'], float)[bolge]; ozet[ad] = {'toplam': len(t), 'tasinan': n, 'tasinan_yuzde': round(100 * n / len(t), 2), 'bolgede_zemin_alti_kalan': int((Y < -.03).sum()), 'mb': round(c.stat().st_size / 1e6, 1)}
    print(ad, ozet[ad], flush=True)
(O / 'zemin_duz_ozet.json').write_text(json.dumps(ozet, indent=1)); print('ZEMİN DÜZLEME BİTTİ', flush=True)
