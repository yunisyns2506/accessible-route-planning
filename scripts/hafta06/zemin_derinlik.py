"""Boş koridor/sıra arası zeminde Gaussian'ların yükseklik dağılımı (gerçek zemin: y=0, seyrek noktalarla RMS 0,75 cm).
Colab'da Drive bağlıyken: python3 zemin_derinlik.py. Çıktı konsola ve derslik4_cekim2/logs/zemin_derinlik.json dosyasına."""
import json
from pathlib import Path

import numpy as np
from plyfile import PlyData

S = Path('/content/drive/MyDrive/Hafta 6 Çalışmaları/derslik4_cekim2'); U = S / 'runs/unity'; AD = .10
gx = np.arange(-9.2, 9.0 + AD, AD); gz = np.arange(-7.2, 7.25 + AD, AD)
sonuc = {}
for ad, n in (('taban_1080', 'derslik4_cekim2_unity.ply'), ('H2_1080', 'derslik4_cekim2_H2_kapi_acik_unity.ply'), ('H2_1440big', 'derslik4_cekim2_1440big_H2_kapi_acik_unity.ply')):
    p = U / n
    if not p.exists(): print('yok', n); continue
    v = PlyData.read(str(p))['vertex'].data; X = np.c_[v['x'], v['y'], v['z']].astype(float); op = 1 / (1 + np.exp(-v['opacity'].astype(float)))
    s = np.sort(np.exp(np.c_[v['scale_0'], v['scale_1'], v['scale_2']].astype(float)), 1); dc = .5 + .28209479 * np.c_[v['f_dc_0'], v['f_dc_1'], v['f_dc_2']].astype(float); lm = np.clip(.299 * dc[:, 0] + .587 * dc[:, 1] + .114 * dc[:, 2], 0, 1)
    ix = np.floor((X[:, 0] - gx[0]) / AD).astype(int); iz = np.floor((X[:, 2] - gz[0]) / AD).astype(int); k = (ix >= 0) & (ix < len(gx) - 1) & (iz >= 0) & (iz < len(gz) - 1)
    ust = np.zeros((len(gz) - 1, len(gx) - 1)); m = k & (X[:, 1] > .15) & (X[:, 1] < 1.4) & (op > .3); np.add.at(ust, (iz[m], ix[m]), op[m])
    if ad == 'taban_1080': bos_t = ust
    bos = (ust < .3) & (bos_t < .3) if 'bos_t' in globals() else ust < .3
    sec = k & bos[np.clip(iz, 0, bos.shape[0] - 1), np.clip(ix, 0, bos.shape[1] - 1)] & (X[:, 1] > -1.2) & (X[:, 1] < .15) & (op > .1) & (X[:, 0] > -9.2)
    w = op[sec] * s[sec, 2] * s[sec, 1]; y = X[sec, 1]; L = lm[sec]; T = w.sum()
    pay = lambda a, b: round(float(w[(y >= a) & (y < b)].sum() / T * 100), 1)
    bant = [(-1.2, -.5), (-.5, -.2), (-.2, -.08), (-.08, -.03), (-.03, .03), (.03, .08), (.08, .15)]
    sonuc[ad] = {'gaussian': int(sec.sum()), 'bos_hucre': int(bos.sum()), 'agirlik_yuzde': {f'{a:+.2f}..{b:+.2f}': pay(a, b) for a, b in bant}, 'parlaklik_ort': {f'{a:+.2f}..{b:+.2f}': round(float(np.average(L[(y >= a) & (y < b)], weights=w[(y >= a) & (y < b)])), 3) if ((y >= a) & (y < b)).sum() > 20 else None for a, b in bant},
                 'koyu_lum06_agirlik_yuzde': round(float(w[L < .6].sum() / T * 100), 1), 'zemin_alti_8cm_yuzde': pay(-1.2, -.08), 'duzlemde_8cm_yuzde': pay(-.08, .08)}
    print(ad, json.dumps(sonuc[ad], ensure_ascii=False), flush=True)
(S / 'logs/zemin_derinlik.json').write_text(json.dumps(sonuc, indent=1, ensure_ascii=False))
