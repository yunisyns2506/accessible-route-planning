"""Derslik 4 2. çekim, H2: aynı SfM pozları + aynı kareler, 1080p splatfacto 30k + bilateral grid (pozlama düzeltme).
COLMAP gerekmez; yalnız 3DGS ortamı kurulur. Sonra taban ve H2 renk düzeltmeli ölçülür, beyaz yüzeyli test
karelerinden karşılaştırma panosu ve Unity ply üretilir. İlerleme: derslik4_cekim2/logs/h2.log
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

H6 = Path('/content/drive/MyDrive/Hafta 6 Çalışmaları'); D = H6 / 'derslik4_cekim2'; W = Path('/content/work'); L = D / 'logs'
TABAN = 'loma_sequential_loop_incremental'; H2 = TABAN + '_H2'; SP = 'sfm/loma/sequential_loop/incremental'
CUDA = '/usr/local/cuda-12.8'; PY = '/content/ns/bin/python'
E = {**os.environ, 'CUDA_HOME': CUDA, 'PATH': f'/content/ns/bin:{CUDA}/bin:' + os.environ['PATH'], 'TORCH_CUDA_ARCH_LIST': '8.9'}


def say(m):
    s = time.strftime('%F %T') + ' ' + m; print(s, flush=True)
    with open(L / 'h2.log', 'a') as f: f.write(s + chr(10))


def kos(cmd, log, env=None, kritik=True):
    t = time.time()
    with open(log, 'a') as f:
        rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=W, env=env, shell=isinstance(cmd, str))
    if rc and kritik:
        say(f'HATA rc={rc}: {log}'); sys.exit(1)
    return (time.time() - t) / 60, rc


say('H2 hattı başladı; ortam kuruluyor')
kur = r'''set -e
pip install -q nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cufft-cu12 nvidia-cuda-runtime-cu12 nvidia-curand-cu12 nvidia-cusparse-cu12 nvidia-cusolver-cu12 nvidia-nvjitlink-cu12 pycolmap-cuda12==4.2.1 psutil plyfile scipy opencv-python-headless
if [ ! -x /usr/local/cuda-12.8/bin/nvcc ]; then
  wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb -O /tmp/ck.deb
  dpkg -i /tmp/ck.deb; apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq cuda-toolkit-12-8 > /dev/null
fi
unset UV_SYSTEM_PYTHON
pip install -q uv
[ -x /content/ns/bin/python ] || uv venv /content/ns --python 3.11 -q
uv pip install -q --python /content/ns/bin/python torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu124
uv pip install -q --python /content/ns/bin/python nerfstudio==1.1.5 gsplat==1.4.0 psutil ninja plyfile torch==2.4.1 torchvision==0.19.1 --extra-index-url https://download.pytorch.org/whl/cu124
'''
(W / 'kur_ns.sh').write_text(kur)
dk, _ = kos(['bash', 'kur_ns.sh'], L / 'h2_kurulum.log'); say(f'ortam tamam {dk:.1f} dk')
for src, dst, ex in [(D / 'frames_1080', W / 'frames_1080', []), (D / 'sfm', W / 'sfm', ['--exclude', '*.db', '--exclude', '*.db-*']), (D / 'runs' / TABAN, W / 'runs' / TABAN, [])]:
    dst.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(['rsync', '-a', *ex, f'{src}/', f'{dst}/'])
n = len(list((W / 'frames_1080').glob('*.jpg'))); say(f'veri kopyalandı: {n} kare')
if n != 1500: say('HATA kare sayısı'); sys.exit(1)
say('H2 eğitimi başladı (1080p, 30k)')
dk, _ = kos([PY, '-u', 'colab_gs.py', 'loma', 'sequential_loop', 'incremental', '--tag', 'H2', '--extra=--pipeline.model.use-bilateral-grid True'], L / 'h2_gs.log', E)
R = W / 'runs' / H2
say(f'H2 bitti {dk:.1f} dk: ' + (R / 'summary.json').read_text().replace(chr(10), ' '))

# Unity (hafta 5 salon boyutuna göre tahmini ölçek; mezura ölçüleriyle güncellenecek)
M = W / SP / 'sparse' / json.load(open(W / SP / 'map.json'))['models'][0]['model']
kos(['python3', 'unity_ply.py', str(R / 'export/splat.ply'), str(next(R.rglob('dataparser_transforms.json'))), str(M), '210', str(D / 'runs/unity/derslik4_cekim2_H2_unity.ply')], L / 'h2_unity.log')
say('Unity ply hazır')

# Renk düzeltmeli karşılaştırma + beyaz yüzeyli karelerden pano
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
test = sorted(p.name for p in (W / 'frames_1080').glob('*.jpg') if int(p.stem) % 10 == 0)
oran = {}
for nm in test:
    g = np.asarray(Image.open(W / 'frames_1080' / nm).convert('L').resize((480, 270)), dtype=np.float32)
    gr = np.abs(np.diff(g, axis=0))[:, :-1] + np.abs(np.diff(g, axis=1))[:-1, :]
    oran[nm] = float(((g[:-1, :-1] > 150) & (gr < 3)).mean())
beyaz = sorted(oran, key=oran.get)[-4:]
say('beyaz yüzeyli test kareleri: ' + str({k: round(oran[k], 2) for k in beyaz}))
kos([PY, '-c', f"import sys; sys.path.insert(0,'/content/work'); import colab_gs; print(colab_gs.make_data('loma','sequential_loop','incremental'))"], L / 'h2_renk.log', E)
for run in (TABAN, H2):
    _, rc = kos([PY, '-u', 'renk_degerlendir.py', run, *beyaz], L / 'h2_renk.log', E, kritik=False)
    if rc == 0:
        say('renk düzeltmeli ' + run + ': ' + json.dumps({k: json.load(open(W / 'runs' / run / 'renk_duzeltmeli.json'))[k] for k in ('psnr', 'ssim', 'lpips')}))
    else:
        say(f'renk düzeltmeli başarısız: {run}')
try:
    sat = []
    for nm in beyaz:
        ims = [Image.open(W / 'frames_1080' / nm), Image.open(W / 'runs' / TABAN / 'renk' / nm), Image.open(R / 'renk' / nm)]
        sat.append([i.convert('RGB').resize((640, 360)) for i in ims])
    pano = Image.new('RGB', (1920, 360 * len(sat)))
    for y, s in enumerate(sat):
        for x, i in enumerate(s):
            pano.paste(i, (640 * x, 360 * y))
    pano.save(L / 'h2_pano_gercek_taban_h2.jpg', quality=88)
except Exception as e:
    say(f'pano yok: {e}')
subprocess.call(['rsync', '-a', f'{W}/runs/', f'{D}/runs/'])
say('H2 HAT BİTTİ')
