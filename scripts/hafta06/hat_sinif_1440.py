"""Derslik 4 sınıf (06.11 çekimi): 1440p splatfacto-big + H2, sürdürmeli (hat_1440.py'nin 07.11 tekrarı).
hat_1440.py 07.11 gecesi %46'da sanal makine değişince kayboldu; burada eğitim egit_surdur.py ile koşar
(kontrol noktası 10 dk'da bir Drive'a, yeniden çalıştırılınca oradan sürer). 1440p kareler de Drive'a yazılır.
Koridor hattından sonra aynı oturumda çalışır: /content/work koridordan ayrılır (work_koridor), betikler oradan alınır.
İlerleme: derslik4_cekim2/logs/h1440b.log
"""
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

H6 = Path('/content/drive/MyDrive/Hafta 6 Çalışmaları'); D = H6 / 'derslik4_cekim2'; W = Path('/content/work'); L = D / 'logs'
BASE = 'loma_sequential_loop_incremental'; H2 = BASE + '_H2'; YENI = BASE + '_1440_big_H2'; SP = 'sfm/loma/sequential_loop/incremental'
CUDA = '/usr/local/cuda-12.8'; PY = '/content/ns/bin/python'
E = {**os.environ, 'CUDA_HOME': CUDA, 'PATH': f'/content/ns/bin:{CUDA}/bin:' + os.environ['PATH'], 'TORCH_CUDA_ARCH_LIST': '8.9', 'MALLOC_ARENA_MAX': '2'}


def say(m):
    s = time.strftime('%F %T') + ' ' + m; print(s, flush=True)
    with open(L / 'h1440b.log', 'a') as f: f.write(s + chr(10))


def kos(cmd, log, env=None, kritik=True):
    t = time.time()
    with open(log, 'a') as f:
        rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=W, env=env)
    if rc and kritik:
        say(f'HATA rc={rc}: {log}'); sys.exit(1)
    return (time.time() - t) / 60, rc


say('hat başladı')
# Çalışma klasörü: koridorunki ayrılır, betikler oradan (koridor yolları bu klasöre çevrilir)
K = Path('/content/work_koridor')
if W.exists() and (W / 'hat_koridor.py').exists() and not K.exists():
    W.rename(K)
W.mkdir(exist_ok=True)
for b in ('colab_sfm.py', 'colab_gs.py', 'egit_surdur.py', 'unity_ply.py', 'renk_degerlendir.py'):
    if not (W / b).exists():
        (W / b).write_text((K / b).read_text().replace('/derslik4_koridor', '/derslik4_cekim2'))
if not (Path(PY).exists() and Path('/content/colmap/bin/colmap').exists()):
    say('HATA ortam yok (koridor hattı kurmuş olmalıydı)'); sys.exit(1)
# Görüntü ve maske pin_memory kapalı (1500 karede RAM doluyordu); sürdürme yaması koridor hattında uygulandı
F = Path('/content/ns/lib/python3.11/site-packages/nerfstudio/data/datamanagers/full_images_datamanager.py'); s = F.read_text()
s = s.replace('cache["image"] = cache["image"].pin_memory()', 'cache["image"] = cache["image"].contiguous()  # pin_memory kapali (RAM)')
s = s.replace('cache["mask"] = cache["mask"].pin_memory()', 'cache["mask"] = cache["mask"].contiguous()  # pin_memory kapali (RAM)')
F.write_text(s)
if s.count('pin_memory kapali') != 2 or 'surdurme yamasi' not in Path('/content/ns/lib/python3.11/site-packages/nerfstudio/engine/trainer.py').read_text():
    say('HATA yamalar eksik'); sys.exit(1)
say('ortam hazır (pin_memory kapalı, sürdürme yaması var)')

for src, dst, ex in [(D / 'frames_1080', W / 'frames_1080', []), (D / 'sfm', W / 'sfm', ['--exclude', '*.db', '--exclude', '*.db-*']), (D / 'runs' / H2, W / 'runs' / H2, [])]:
    dst.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(['rsync', '-a', *ex, f'{src}/', f'{dst}/'])
n = len(list((W / 'frames_1080').glob('*.jpg'))); say(f'1080p kareler, SfM, H2 koşusu kopyalandı: {n} kare')
if n != 1500: say('HATA kare sayısı'); sys.exit(1)

# 1440p kareler: Drive'da varsa oradan; yoksa hat_cekim2 ile aynı birleştirme ve kare listesiyle videodan
(D / 'frames_1440').mkdir(exist_ok=True)
if len(list((D / 'frames_1440').glob('*.jpg'))) == 1500:
    subprocess.check_call(['rsync', '-a', f'{D / "frames_1440"}/', f'{W / "frames_1440"}/'])
    say('1440p kareler Drive\'dan alındı')
else:
    ayar = json.loads((L / 'kare_ayari.json').read_text()); kirpma = ayar['kirpma_sn']; parca_sn = ayar['parca_sn']
    parcalar = {}
    for ad in os.listdir(H6):
        a = unicodedata.normalize('NFC', ad).lower().replace('ç', 'c')
        if a.startswith('derslik4_cekim2_part') and a.endswith(('.mov', '.mp4')):
            parcalar[a.split('part')[1][0]] = H6 / ad
    yerel, sat = [], []
    for i, k in enumerate(sorted(parcalar)):
        q = W / f'part{i + 1}{parcalar[k].suffix.lower()}'
        shutil.copy(parcalar[k], q); yerel.append(q)
        sat.append(f"file '{q}'")
        if i > 0: sat.append(f'inpoint {kirpma[i - 1][1]:.3f}')
        if i < len(parcalar) - 1: sat.append(f'outpoint {parca_sn[i] - kirpma[i][0]:.3f}')
    (W / 'liste.txt').write_text(chr(10).join(sat) + chr(10))
    say('videolar kopyalandı')
    kos(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'liste.txt', '-map', '0:v:0', '-c', 'copy', '-an', 'derslik4.mov'], L / 'h1440b_cikarma.log')
    kareler = [r['frame'] for r in csv.DictReader(open(L / 'video_analiz' / 'secilen_kareler_1500.csv'))]
    q = chr(39); sel = '+'.join('eq(n' + chr(92) + ',' + k + ')' for k in kareler)
    (W / 'select1440.txt').write_text('[0:v]select=' + q + sel + q + ',scale=2560:1440:flags=lanczos[c]')
    (W / 'frames_1440').mkdir(exist_ok=True)
    dk, _ = kos(['ffmpeg', '-v', 'error', '-y', '-threads', '0', '-i', 'derslik4.mov', '-filter_complex_script', 'select1440.txt', '-map', '[c]', '-fps_mode', 'passthrough', '-q:v', '2', 'frames_1440/%04d.jpg'], L / 'h1440b_cikarma.log')
    n = len(list((W / 'frames_1440').glob('*.jpg'))); say(f'1440p kareler: {n} ({dk:.1f} dk)')
    if n != 1500: say('HATA 1440p kare sayısı'); sys.exit(1)
    for p in yerel: p.unlink()
    (W / 'derslik4.mov').unlink()
    subprocess.call(['rsync', '-a', f'{W / "frames_1440"}/', f'{D / "frames_1440"}/'])

# Hiza denetimi: 1440p kare küçültülünce aynı 1080p kareyi vermeli
import cv2  # noqa: E402
import numpy as np  # noqa: E402
ps = []
for i in range(1, 1501, 50):
    a = cv2.imread(str(W / 'frames_1440' / f'{i:04d}.jpg')); b = cv2.imread(str(W / 'frames_1080' / f'{i:04d}.jpg'))
    ps.append(cv2.PSNR(cv2.resize(a, (1920, 1080), interpolation=cv2.INTER_AREA), b))
say(f'hiza denetimi ({len(ps)} kare): en düşük PSNR {min(ps):.1f} dB, medyan {float(np.median(ps)):.1f} dB')
if min(ps) < 33: say('HATA kareler hizalı değil'); sys.exit(1)

d = (json.loads((D / 'ckpt' / YENI / 'durum.json').read_text()) if (D / 'ckpt' / YENI / 'durum.json').exists() else {})
say('eğitim ' + (f'sürüyor (son kayıtlı adım {d.get("son_adim")})' if d.get('son_adim') else 'başladı') + ' (1440p, splatfacto-big, H2, 30k)')
dk, _ = kos([PY, '-u', 'egit_surdur.py', '1440', 'splatfacto-big', 'H2', str(D), '--extra', '--pipeline.model.use-bilateral-grid True'], L / 'h1440b_gs.log', E)
R = W / 'runs' / YENI
say(f'eğitim bitti ({dk:.1f} dk bu oturumda): ' + (R / 'summary.json').read_text().replace(chr(10), ' '))

# Unity (tahmini ölçek 210 cm/birim; mezura ölçüleriyle güncellenecek)
M = W / SP / 'sparse' / json.load(open(W / SP / 'map.json'))['models'][0]['model']
kos(['python3', 'unity_ply.py', str(R / 'export/splat.ply'), str(next(R.rglob('dataparser_transforms.json'))), str(M), '210', str(D / 'runs/unity/derslik4_cekim2_1440big_H2_unity.ply')], L / 'h1440b_unity.log')
say('Unity ply hazır')
subprocess.call(['rsync', '-a', f'{R}/', f'{D}/runs/{YENI}/'])

# Karşılaştırma: en ayrıntılı 4 test karesi (kırpım) + beyaz duvarlı 2 kare (tüm kare); gerçek / H2 1080p / 1440 big H2
test = sorted(p.name for p in (W / 'frames_1080').glob('*.jpg') if int(p.stem) % 10 == 0)
kenar = {nm: float(cv2.Laplacian(cv2.imread(str(W / 'frames_1080' / nm), cv2.IMREAD_GRAYSCALE), cv2.CV_32F).var()) for nm in test}
ayrinti = sorted(kenar, key=kenar.get)[-4:]; sec = ayrinti + ['0190.jpg', '0420.jpg']
say('pano kareleri: ' + str(sec))
kos([PY, '-c', "import sys; sys.path.insert(0,'/content/work'); import colab_gs; print(colab_gs.make_data('loma','sequential_loop','incremental',tag='H2'))"], L / 'h1440b_renk.log', E)
for run in (H2, YENI):
    _, rc = kos([PY, '-u', 'renk_degerlendir.py', run, *sec], L / 'h1440b_renk.log', E, kritik=False)
    if rc == 0:
        say('renk düzeltmeli ' + run + ': ' + json.dumps({k: json.load(open(W / 'runs' / run / 'renk_duzeltmeli.json'))[k] for k in ('psnr', 'ssim', 'lpips')}))
    else:
        say(f'renk düzeltmeli başarısız: {run}')
try:
    def oku(p): return cv2.resize(cv2.imread(str(p)), (1920, 1080), interpolation=cv2.INTER_AREA)
    sat = []
    for nm in sec:
        g = oku(W / 'frames_1080' / nm); h2 = oku(W / 'runs' / H2 / 'renk' / nm); bg = oku(W / 'runs' / YENI / 'renk' / nm)
        if nm in ayrinti:
            gr = cv2.cvtColor(g, cv2.COLOR_BGR2GRAY)
            m = cv2.magnitude(cv2.Sobel(gr, cv2.CV_32F, 1, 0), cv2.Sobel(gr, cv2.CV_32F, 0, 1))
            ii = cv2.integral(m); s = ii[360:, 640:] - ii[:-360, 640:] - ii[360:, :-640] + ii[:-360, :-640]
            y, x = np.unravel_index(np.argmax(s), s.shape)
            sat.append(np.hstack([i[y:y + 360, x:x + 640] for i in (g, h2, bg)]))
        else:
            sat.append(np.hstack([cv2.resize(i, (640, 360), interpolation=cv2.INTER_AREA) for i in (g, h2, bg)]))
    cv2.imwrite(str(L / 'h1440_pano_gercek_h2_1440big.jpg'), np.vstack(sat), [cv2.IMWRITE_JPEG_QUALITY, 92])
except Exception as e:
    say(f'pano yok: {e}')
subprocess.call(['rsync', '-a', f'{W}/runs/{YENI}/', f'{D}/runs/{YENI}/'])
say('1440 HAT BİTTİ')
