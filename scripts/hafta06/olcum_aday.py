"""Üçgenlenmiş noktaların hepsinin göründüğü aday kareleri listeler (nesne eşleştirmesini doğrulamak ve gözlem eklemek için)."""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

d = Path(sys.argv[1]); N = json.loads((d / 'noktalar.json').read_text()); adlar = sys.argv[2].split(','); adet = int(sys.argv[3]) if len(sys.argv) > 3 else 12
j = json.loads((d / 'poz_sinif.json').read_text()); f1, f2, cx, cy, k1, k2, p1, p2 = j['kamera']['params']
A = np.array([[f1, 0, cx], [0, f2, cy], [0, 0, 1.]]); dist = np.array([k1, k2, p1, p2]); X = np.array([N[a]['X'] for a in adlar]); s = []
for k, v in j['pozlar'].items():
    P = np.array(v); pc = X @ P[:3, :3].T + P[:3, 3]
    if (pc[:, 2] < 0.3).any(): continue
    if (np.abs(pc[:, :2] / pc[:, 2:]) > [1.05, 0.6]).any(): continue  # görüş alanı dışı: bozulma modeli katlanır
    p, _ = cv2.projectPoints(X, cv2.Rodrigues(P[:3, :3])[0], P[:3, 3], A, dist); p = p[:, 0]
    if ((p < 40) | (p > [1880, 1040])).any(): continue
    s.append((float(np.ptp(p[:, 0]) + np.ptp(p[:, 1])), k, p.round().astype(int).tolist()))
for t in sorted(s, reverse=True)[:adet]:
    print(t[1], round(t[0]), t[2])
print('toplam', len(s))
