"""Hafta 6 · Derslik 4 koridoru (06.11 çekimi, 0,5×, 4K 30 fps): kare seçimi, SfM, sonra iki eğitim:
1) 1440p splatfacto-big, 2) aynı ayarlar + H2 (bilateral grid). Sınıf hattıyla aynı yöntem (LoMa + sequential/döngü
+ incremental, 30k), farkı: kare aralığı 0,4 sn (koridorda ileri yürüyüş, sınıfta 0,8 sn) ve doğrudan 1440p.

Sürdürme: her aşama bittiğinde Drive'a yazılır; hat yeniden başlatılınca biten aşamalar atlanır, eğitimler
egit_surdur.py ile son kontrol noktasından sürer (en çok ~10 dk kayıp). Eğitimden önce sürdürmenin çalıştığı
1080p kısa bir koşuyla denetlenir (300 adım + sürdürüp 800 adım).
Kullanım: python3 hat_koridor.py   (betikler /content/work'te). İlerleme: derslik4_koridor/logs/hat.log
"""
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

H6 = Path('/content/drive/MyDrive/Hafta 6 Çalışmaları'); D = H6 / 'derslik4_koridor'; W = Path('/content/work')
L = D / 'logs'; AN = L / 'video_analiz'; VIDEO = H6 / 'derslik4_koridor.mov'
ARALIK = 0.4  # sn; koridorda ileri yürürken bakış hızlı değişir, sınıftan sık örneklenir
SP = 'sfm/loma/sequential_loop/incremental'; BASE = 'loma_sequential_loop_incremental'
PY = '/content/ns/bin/python'; CUDA = '/usr/local/cuda-12.8'
E = {**os.environ, 'CUDA_HOME': CUDA, 'PATH': f'/content/ns/bin:{CUDA}/bin:' + os.environ['PATH'],
     'TORCH_CUDA_ARCH_LIST': '8.9', 'MALLOC_ARENA_MAX': '2'}
KOSULAR = [('', ''), ('H2', '--pipeline.model.use-bilateral-grid True')]  # (etiket, ek ayar)
for k in ('frames_1080', 'frames_1440', 'sfm', 'runs/unity', 'ns', 'ckpt', 'logs/video_analiz'):
    (D / k).mkdir(parents=True, exist_ok=True)


def say(m):
    s = time.strftime('%F %T') + ' ' + m; print(s, flush=True)
    with open(L / 'hat.log', 'a') as f: f.write(s + chr(10))


def kos(cmd, log, env=None, kritik=True):
    t = time.time()
    with open(log, 'a') as f:
        rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=W, env=env)
    if rc and kritik:
        say(f'HATA rc={rc}: {log}'); sys.exit(1)
    return (time.time() - t) / 60, rc


def jpg(d): return len(list(Path(d).glob('*.jpg')))


say('hat başladı')
# --- Kurulum (COLMAP hazır derlemesi + 3DGS ortamı); yollar bu klasöre çevrilir
for b in ('colab_sfm.py', 'colab_gs.py', 'kurulum.sh'):
    s = (W / b).read_text(); (W / b).write_text(s.replace('/meetingroom', '/derslik4_koridor'))
if not (Path('/content/colmap/bin/colmap').exists() and Path(PY).exists()):
    dk, _ = kos(['bash', 'kurulum.sh'], L / 'kurulum_cikti.log')
    if 'KURULUM BİTTİ' not in (L / 'kurulum.log').read_text().splitlines()[-1]:
        say('HATA kurulum (kurulum_colmap.log / kurulum_ns.log)'); sys.exit(1)
    say(f'kurulum tamam {dk:.1f} dk')
subprocess.call('pip install -q psutil opencv-python-headless plyfile scipy', shell=True)
# nerfstudio sürdürme yaması: kontrol noktası yüklenince iyileştiriciler yeni (yeniden boyutlanan) parametrelerle kurulur
TR = Path('/content/ns/lib/python3.11/site-packages/nerfstudio/engine/trainer.py'); s = TR.read_text()
if 'surdurme yamasi' not in s:
    s, n = re.subn(r'^(\s*)self\.optimizers\.load_optimizers\(loaded_state\["optimizers"\]\)',
                   r'\1self.optimizers = self.setup_optimizers()  # surdurme yamasi' + '\n' + r'\1self.optimizers.load_optimizers(loaded_state["optimizers"])',
                   s, flags=re.M)
    if n == 0: say('HATA trainer.py yaması uygulanamadı'); sys.exit(1)
    TR.write_text(s)
say('ortam hazır; nerfstudio sürdürme yaması uygulandı')

# --- Kareler: Drive'da varsa oradan, yoksa videodan (1080p ve 1440p aynı geçişte)
ayar_p = L / 'kare_ayari.json'
if ayar_p.exists() and jpg(D / 'frames_1080') == json.loads(ayar_p.read_text())['N'] == jpg(D / 'frames_1440'):
    N = json.loads(ayar_p.read_text())['N']
    for k in ('frames_1080', 'frames_1440'):
        subprocess.check_call(['rsync', '-a', f'{D / k}/', f'{W / k}/'])
    say(f'kareler Drive\'dan alındı: {N}')
else:
    V = W / 'koridor.mov'; shutil.copy(VIDEO, V)
    p = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                   'stream=codec_name,width,height,avg_frame_rate,duration,nb_frames:stream_side_data=rotation', '-of', 'json', str(V)]))['streams'][0]
    a, b = p['avg_frame_rate'].split('/'); fps = int(a) / int(b); sure = float(p['duration'])
    rot = (p.get('side_data_list') or [{}])[0].get('rotation', 0)
    if p['width'] != 3840 or p['height'] != 2160 or int(rot) % 180:
        say('HATA video 4K yatay değil: ' + json.dumps(p)); sys.exit(1)
    N = max(200, min(1500, round(sure / ARALIK))); ESIK = round(15 * 30 / fps, 2)
    ayar_p.write_text(json.dumps({'video': p, 'fps': fps, 'N': N, 'esik_px_kare': ESIK, 'aralik_sn': sure / N}, indent=1))
    say(f'video: {sure / 60:.2f} dk, {fps:.2f} fps, {p["codec_name"]} | N={N} aralık={sure / N:.2f} sn eşik={ESIK}')
    if not (AN / 'video_olcutleri.npz').exists():
        dk, _ = kos(['python3', '-u', 'video_analiz.py', str(V), str(AN), '3840'], L / 'analiz.log'); say(f'analiz {dk:.1f} dk')
    s = (W / 'kare_secimi.py').read_text(); (W / 'kare_secimi.py').write_text(s.replace('ESIK = 15.0', f'ESIK = {ESIK}'))
    kos(['python3', 'kare_secimi.py', str(AN), str(N)], AN / 'secim_ozet.txt')
    say(open(AN / 'secim_ozet.txt').read().strip().splitlines()[-1])
    kareler = [r['frame'] for r in csv.DictReader(open(AN / f'secilen_kareler_{N}.csv'))]
    q = chr(39); sel = '+'.join('eq(n' + chr(92) + ',' + k + ')' for k in kareler)
    (W / 'select.txt').write_text('[0:v]select=' + q + sel + q + ',split=2[a][b];[a]scale=1920:1080:flags=lanczos[c1];[b]scale=2560:1440:flags=lanczos[c2]')
    for k in ('frames_1080', 'frames_1440'): (W / k).mkdir(exist_ok=True)
    dk, _ = kos(['ffmpeg', '-v', 'error', '-y', '-threads', '0', '-i', str(V), '-filter_complex_script', 'select.txt',
                 '-map', '[c1]', '-fps_mode', 'passthrough', '-q:v', '2', 'frames_1080/%04d.jpg',
                 '-map', '[c2]', '-fps_mode', 'passthrough', '-q:v', '2', 'frames_1440/%04d.jpg'], L / 'cikarma.log')
    say(f'kareler: 1080p {jpg(W / "frames_1080")}, 1440p {jpg(W / "frames_1440")} ({dk:.1f} dk)')
    if not jpg(W / 'frames_1080') == jpg(W / 'frames_1440') == N: say('HATA kare sayısı'); sys.exit(1)
    for k in ('frames_1080', 'frames_1440'):
        subprocess.call(['rsync', '-a', f'{W / k}/', f'{D / k}/'])
    V.unlink()

# --- SfM
MP = W / SP / 'map.json'
dmp = D / SP / 'map.json'
if dmp.exists() and json.loads(dmp.read_text()).get('return_code') == 0 and 'models' in json.loads(dmp.read_text()):
    subprocess.check_call(['rsync', '-a', f'{D / "sfm"}/', f'{W / "sfm"}/'])
    say('SfM Drive\'dan alındı')
else:
    say('SfM başladı')
    dk, _ = kos(['python3', '-u', 'colab_sfm.py', 'M'], L / 'sfm_M.log')
    say(f'SfM bitti {dk:.1f} dk')
mods = json.load(open(MP))['models']
say('SfM modelleri: ' + json.dumps(mods[:3]))
if mods[0]['registered'] < 0.9 * N: say(f'UYARI kayıtlı kare az: {mods[0]["registered"]}/{N}')

# --- Sürdürme testi (1080p, splatfacto, 300 adım; sonra kontrol noktasından 800. adıma)
TEST = BASE + '_T'
if not (L / 'surdurme_testi.json').exists():
    t = time.time()
    _, r1 = kos([PY, '-u', 'egit_surdur.py', '1080', 'splatfacto', 'T', str(D), '--bitir', '300', '--kayit', '100', '--aralik', '20'], L / 'surdurme_testi.log', E, kritik=False)
    _, r2 = kos([PY, '-u', 'egit_surdur.py', '1080', 'splatfacto', 'T', str(D), '--bitir', '800', '--kayit', '100', '--aralik', '20'], L / 'surdurme_testi.log', E, kritik=False)
    import torch  # noqa: E402  (sistem Python'unda torch var)
    c = sorted((W / 'runs' / TEST).rglob('step-*.ckpt'), key=lambda p: int(re.search(r'(\d+)\.ckpt', p.name).group(1)))
    sonuc = {'rc': [r1, r2], 'ckpt': [p.name for p in c], 'dk': round((time.time() - t) / 60, 1)}
    if r1 == 0 and r2 == 0 and len(c) >= 2:
        a = torch.load(c[0], map_location='cpu', weights_only=False)['pipeline']; b = torch.load(c[-1], map_location='cpu', weights_only=False)['pipeline']
        k = next(x for x in a if x.endswith('gauss_params.means'))
        sonuc.update({'adim': [int(torch.load(c[0], map_location='cpu', weights_only=False)['step']), int(torch.load(c[-1], map_location='cpu', weights_only=False)['step'])],
                      'gauss': [int(a[k].shape[0]), int(b[k].shape[0])]})
    tb = 'Traceback' in (L / 'surdurme_testi.log').read_text()
    sonuc['gecti'] = bool(r1 == 0 and r2 == 0 and not tb and sonuc.get('adim', [0, 0])[1] >= 799 and sonuc.get('gauss', [0, 0])[0] != sonuc.get('gauss', [0, 0])[1])
    (L / 'surdurme_testi.json').write_text(json.dumps(sonuc))
    say('sürdürme testi: ' + json.dumps(sonuc))
    shutil.rmtree(D / 'ckpt' / TEST, ignore_errors=True); shutil.rmtree(W / 'runs' / TEST, ignore_errors=True)
    shutil.rmtree(D / 'runs' / TEST, ignore_errors=True); shutil.rmtree(D / 'ns' / TEST, ignore_errors=True)
    if not sonuc['gecti']: say('UYARI sürdürme çalışmıyor; eğitim yine başlıyor, kesilirse baştan başlar')

# --- Eğitimler
M = W / SP / 'sparse' / mods[0]['model']
sys.path.insert(0, str(W))
for etiket, ek in KOSULAR:
    run = BASE + '_1440_big' + (f'_{etiket}' if etiket else '')
    if (D / 'runs' / run / 'summary.json').exists() and (D / 'runs/unity' / f'koridor_{run[len(BASE) + 1:]}_unity.ply').exists():
        say(f'{run} daha önce bitmiş, atlandı'); continue
    if (D / 'runs' / run).exists():
        subprocess.call(['rsync', '-a', f'{D / "runs" / run}/', f'{W / "runs" / run}/'])
    d = (json.loads((D / 'ckpt' / run / 'durum.json').read_text()) if (D / 'ckpt' / run / 'durum.json').exists() else {})
    say(f'{run} eğitimi ' + (f'sürüyor (son kayıtlı adım {d.get("son_adim")})' if d.get('son_adim') else 'başladı') + ' (1440p, splatfacto-big, 30k)')
    dk, _ = kos([PY, '-u', 'egit_surdur.py', '1440', 'splatfacto-big', etiket, str(D), '--extra', ek], L / f'gs_{etiket or "taban"}.log', E)
    R = W / 'runs' / run
    say(f'{run} bitti ({dk:.1f} dk bu oturumda): ' + (R / 'summary.json').read_text().replace(chr(10), ' '))
    # Unity: ölçek tahmini (kamera yüksekliği ~1,2 m varsayımı: gidiş 1,3–1,4 m, dönüş ~1 m); mezura ile düzeltilecek
    import numpy as np, pycolmap, unity_ply  # noqa: E401,E402
    Mu, o, _, _ = unity_ply.hedef_cerceve(M, 1.0)
    Cm = np.array([i.projection_center() for i in pycolmap.Reconstruction(str(M)).images.values() if i.has_pose])
    h = float(np.median(((Cm - o) @ Mu.T)[:, 1])); olcek = 120 / h
    say(f'kamera yüksekliği {h:.3f} birim; tahmini ölçek {olcek:.1f} cm/birim (1,2 m varsayımı, mezura değil)')
    kos(['python3', 'unity_ply.py', str(R / 'export/splat.ply'), str(next(R.rglob('dataparser_transforms.json'))), str(M), str(olcek),
         str(D / 'runs/unity' / f'koridor_{run[len(BASE) + 1:]}_unity.ply')], L / 'unity.log')
    _, rc = kos([PY, '-u', 'renk_degerlendir.py', run], L / 'renk.log', E, kritik=False)
    if rc == 0:
        say('renk düzeltmeli ' + run + ': ' + json.dumps({k: json.load(open(R / 'renk_duzeltmeli.json'))[k] for k in ('psnr', 'ssim', 'lpips')}))
    subprocess.call(['rsync', '-a', f'{R}/', f'{D / "runs" / run}/'])
    say(f'{run} Unity ply hazır')
subprocess.call(['rsync', '-a', '--exclude', '*.db', '--exclude', '*.db-*', f'{W / "sfm"}/', f'{D / "sfm"}/'])
say('KORİDOR HAT BİTTİ')
