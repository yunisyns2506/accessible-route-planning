"""Hafta 5 ile 06.11 çekiminin eğitim karelerinde bulanıklık karşılaştırması (GPU gerekmez, Colab).
İki çekimin 1080p kareleri aynı yöntemle üretilmiştir (lanczos, -q:v 2). Hafta 5 kareleri videodan yeniden çıkarılır.
Ölçümler sahne içeriğinden de etkilenir; bu yüzden birkaç ölçüt, sandalye kenarları ve örnek kırpımlar birlikte okunmalıdır.
Çıktı: derslik4_cekim2/logs/bulaniklik.json, bulaniklik_pano.jpg, bulaniklik.log
"""
import json
import shutil
import subprocess
import time
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np
from skimage.measure import blur_effect

H5 = Path('/content/drive/MyDrive/hafta5_derslik4')
VIDEO = Path('/content/drive/MyDrive/3dgs videoları/Merkezi Derslik_Derslik4/IMG_0299.MOV')
C2 = Path('/content/drive/MyDrive/Hafta 6 Çalışmaları/derslik4_cekim2')
W = Path('/content/bk')
L = C2 / 'logs'
TABAN = 'loma_sequential_loop_incremental'
OLCUT = ('lap', 'blur', 'ten99', 'sandalye')


def say(m):
    s = time.strftime('%F %T') + ' ' + m
    print(s, flush=True)
    with open(L / 'bulaniklik.log', 'a') as f:
        f.write(s + chr(10))


def hafta5_kareleri():
    d = W / 'h5'
    d.mkdir(parents=True, exist_ok=True)
    if len(list(d.glob('*.jpg'))) == 1000:
        return d
    shutil.copy(VIDEO, W / 'h5.MOV')
    say('hafta 5 videosu kopyalandı')
    kare = (H5 / 'betikler/frame_list.txt').read_text().split()
    sec = '+'.join(f'eq(n\\,{n})' for n in kare)
    (W / 'sec.txt').write_text(f"[0:v]select='{sec}',scale=1920:1080:flags=lanczos[c]")
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-threads', '0', '-i', str(W / 'h5.MOV'), '-filter_complex_script',
                           str(W / 'sec.txt'), '-map', '[c]', '-fps_mode', 'passthrough', '-q:v', '2', str(d / '%04d.jpg')])
    return d


def olc(p):
    im = cv2.imread(str(p))
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    gx, gy = cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)
    m = cv2.magnitude(gx, gy)
    # Turuncu sandalye: iki çekimde de aynı nesne, beyaz duvardan bağımsız kenar ölçüsü
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    tur = cv2.inRange(hsv, (5, 110, 60), (22, 255, 255))
    tur = cv2.dilate(tur, np.ones((9, 9), np.uint8)) > 0
    return {'kare': p.name, 'lap': float(cv2.Laplacian(g, cv2.CV_32F).var()), 'blur': float(blur_effect(g)),
            'ten99': float(np.percentile(m, 99)), 'sandalye': float(np.percentile(m[tur], 95)) if tur.mean() > 0.02 else None,
            'parlak': float(g.mean())}


def ozet(rows, k):
    v = np.array([r[k] for r in rows if r[k] is not None])
    return {'n': len(v), 'p10': round(float(np.percentile(v, 10)), 3), 'medyan': round(float(np.median(v)), 3),
            'p90': round(float(np.percentile(v, 90)), 3)}


def lpips_iliski(rows, renk_json):
    """Test karelerinde: bulanık (blur üst %33) ve keskin (alt %33) karelerin LPIPS ortalaması."""
    kayit = json.load(open(renk_json))
    if 'per_image' not in kayit:  # hafta 5 kaydında kare başına değer yok
        return None
    pi = {r['frame']: r['lpips'] for r in kayit['per_image']}
    x = [(r['blur'], pi[r['kare']]) for r in rows if r['kare'] in pi]
    x.sort()
    u = len(x) // 3
    a = np.array(x)
    return {'n': len(x), 'pearson': round(float(np.corrcoef(a[:, 0], a[:, 1])[0, 1]), 3),
            'keskin_lpips': round(float(a[:u, 1].mean()), 3), 'bulanik_lpips': round(float(a[-u:, 1].mean()), 3)}


def kirp(p):
    """En çok kenar içeren 640x360 bölge, ölçekleme yok."""
    im = cv2.imread(str(p))
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    m = cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    ii = cv2.integral(m)
    s = ii[360:, 640:] - ii[:-360, 640:] - ii[360:, :-640] + ii[:-360, :-640]
    y, x = np.unravel_index(np.argmax(s), s.shape)
    return im[y:y + 360, x:x + 640]


def main():
    say('başladı')
    d5 = hafta5_kareleri()
    say(f'hafta 5 kareleri: {len(list(d5.glob("*.jpg")))}')
    d2 = W / 'c2'
    d2.mkdir(exist_ok=True)
    subprocess.check_call(['rsync', '-a', f'{C2}/frames_1080/', f'{d2}/'])
    say(f'06.11 kareleri: {len(list(d2.glob("*.jpg")))}')
    sonuc, sat = {}, []
    for ad, d, renk in (('hafta5', d5, H5), ('cekim2', d2, C2)):
        with Pool(12) as h:
            rows = h.map(olc, sorted(d.glob('*.jpg')), chunksize=8)
        sonuc[ad] = {k: ozet(rows, k) for k in (*OLCUT, 'parlak')}
        sonuc[ad]['lpips_iliski'] = lpips_iliski(rows, renk / 'runs' / TABAN / 'renk_duzeltmeli.json')
        # 150 karelik dilimlerde medyan bulanıklık (bölüm etkisi)
        sonuc[ad]['dilim_blur'] = [round(float(np.median([r['blur'] for r in rows[i:i + 150]])), 3) for i in range(0, len(rows), 150)]
        sonuc[ad]['satir'] = rows
        say(f'{ad}: ' + json.dumps({k: sonuc[ad][k] for k in (*OLCUT, "parlak", "lpips_iliski", "dilim_blur")}))
        s = sorted((r for r in rows), key=lambda r: r['blur'])
        secim = [s[int(len(s) * q)] for q in (0.1, 0.5, 0.9)]
        sat.append(np.hstack([kirp(d / r['kare']) for r in secim]))
        say(f'{ad} pano kareleri (keskin/orta/bulanık): ' + str([r['kare'] for r in secim]))
    (L / 'bulaniklik.json').write_text(json.dumps(sonuc))
    cv2.imwrite(str(L / 'bulaniklik_pano.jpg'), np.vstack(sat), [cv2.IMWRITE_JPEG_QUALITY, 92])
    say('BULANIKLIK BİTTİ')


if __name__ == '__main__':
    main()
