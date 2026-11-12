"""Hafta 6 ölçek ve hata analizi: karelerde elle işaretlenen uç noktalar SfM pozlarıyla üçgenlenir.

Girdi: olcum/isaretler.json {"nokta": {"model": "sinif|koridor", "goz": {"kare": [u, v], ...}}}
       olcum/poz_sinif.json, poz_koridor.json (cam_from_world 3x4, OPENCV iç parametreleri), kareler/
Çıktı: olcum/noktalar.json (3B nokta, yeniden izdüşüm hatası), olcum/isaret_kontrol.jpg (yakın kırpımlar).
Her işaret cv2.cornerSubPix ile en fazla 4 px inceltilir; işaretin gerçek bir köşe olması gerekir.
kareler/ klasöründe olmayan karelerde (yalnız Drive'daki frames_1080'de bulunanlar) işaret inceltilmeden kullanılır.

Kullanım: python olcum_hesap.py <olcum_klasoru> [--kontrol]
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

K = {}


def yukle(d, ad):
    j = json.loads((d / f'poz_{ad}.json').read_text())
    f1, f2, cx, cy, k1, k2, p1, p2 = j['kamera']['params']
    return np.array([[f1, 0, cx], [0, f2, cy], [0, 0, 1.]]), np.array([k1, k2, p1, p2.__float__()]), {k: np.array(v) for k, v in j['pozlar'].items()}


def ucgenle(goz, A, dist, poz):
    M = []
    for k, uv in goz.items():
        x = cv2.undistortPoints(np.array([[uv]], float), A, dist)[0, 0]
        P = poz[k]; M += [x[0] * P[2] - P[0], x[1] * P[2] - P[1]]
    X = np.linalg.svd(np.array(M))[2][-1]
    return X[:3] / X[3]


def izdus(X, k, A, dist, poz):
    P = poz[k]; p, _ = cv2.projectPoints(X.reshape(1, 3), cv2.Rodrigues(P[:3, :3])[0], P[:3, 3], A, dist)
    return p[0, 0]


def main(d):
    isaret = json.loads((d / 'isaretler.json').read_text(encoding='utf-8'))
    gri = {}
    def g(n):
        if n not in gri:
            im = cv2.imread(str(d / 'kareler' / f'{n}.jpg')); gri[n] = None if im is None else cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        return gri[n]
    ic = {a: yukle(d, a) for a in {v['model'] for v in isaret.values()}}
    sonuc = {}; satirlar = []
    for ad, v in isaret.items():
        A, dist, poz = ic[v['model']]; on = 'k' if v['model'] == 'koridor' else ''
        goz = {}
        for k, uv in v['goz'].items():
            c = np.array([[uv]], np.float32)
            if g(on + k) is None: goz[k] = list(map(float, uv)); continue
            inc = cv2.cornerSubPix(g(on + k), c.copy(), (5, 5), (-1, -1), (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, .01))[0, 0]
            goz[k] = inc.tolist() if np.linalg.norm(inc - uv) < 4 else list(map(float, uv))
        X = ucgenle(goz, A, dist, poz)
        hata = {k: float(np.linalg.norm(izdus(X, k, A, dist, poz) - goz[k])) for k in goz}
        sonuc[ad] = {'model': v['model'], 'X': X.tolist(), 'hata_px': hata, 'goz': goz}
        print(f'{ad:12s} ' + ' '.join(f'{k}:{e:.1f}' for k, e in hata.items()))
        tiles = []
        for k, uv in goz.items():
            im = cv2.imread(str(d / 'kareler' / f'{on + k}.jpg'))
            if im is None: continue
            u, v_ = int(round(uv[0])), int(round(uv[1])); r = 40
            a = np.full((2 * r, 2 * r, 3), 40, np.uint8); y0, x0 = max(0, v_ - r), max(0, u - r); kes = im[y0:v_ + r, x0:u + r]
            a[y0 - (v_ - r):y0 - (v_ - r) + kes.shape[0], x0 - (u - r):x0 - (u - r) + kes.shape[1]] = kes
            a = cv2.resize(a, (240, 240), interpolation=cv2.INTER_NEAREST); cv2.drawMarker(a, (120, 120), (0, 255, 0), cv2.MARKER_CROSS, 40, 1)
            cv2.putText(a, f'{ad} {k} {hata[k]:.1f}', (2, 14), cv2.FONT_HERSHEY_SIMPLEX, .42, (0, 255, 255), 1); tiles.append(a)
        while len(tiles) < 4: tiles.append(np.zeros((240, 240, 3), np.uint8))
        satirlar.append(np.hstack(tiles[:4]))
    sh = [np.vstack(satirlar[i:i + 4]) for i in range(0, len(satirlar), 4)]
    for i, s in enumerate(sh):
        cv2.imwrite(str(d / f'isaret_kontrol_{i}.jpg'), s, [cv2.IMWRITE_JPEG_QUALITY, 85])
    (d / 'noktalar.json').write_text(json.dumps(sonuc, indent=1))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
