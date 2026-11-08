"""Koridor test karelerinde gerçek / 1440p big / 1440p big + H2 yan yana (Colab terminalinden, sınıf eğitimi sürerken).
Veri yükleyici kurulmaz (sınıf eğitiminin RAM'ine dokunmamak için): Gaussian'lar son kontrol noktasından okunur,
kamera transforms.json + dataparser_transforms.json'dan kurulur, gsplat ile çizilir. Gerçek kare nerfstudio ile aynı
biçimde bozulmadan arındırılır (OPENCV, getOptimalNewCameraMatrix alpha 0). H2'nin bilateral grid'i yalnız eğitimde
uygulandığından render hamdır (değerlendirmedeki gibi).
Çıktı: derslik4_koridor/logs/render/<kare>.jpg (her biri 3 × 960 px)
Kullanım: /content/ns/bin/python render_koridor.py
"""
import glob
import json
import os
import re
from pathlib import Path

os.environ.setdefault('CUDA_HOME', '/usr/local/cuda-12.8')
os.environ['PATH'] = '/usr/local/cuda-12.8/bin:' + os.environ['PATH']
os.environ.setdefault('TORCH_CUDA_ARCH_LIST', '8.9')
import cv2  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from gsplat import rasterization  # noqa: E402

K_ = Path('/content/work_koridor')
OUT = Path(glob.glob('/content/drive/MyDrive/Hafta*/derslik4_koridor')[0]) / 'logs' / 'render'
OUT.mkdir(parents=True, exist_ok=True)
RUNS = ['loma_sequential_loop_incremental_1440_big', 'loma_sequential_loop_incremental_1440_big_H2']
BG = torch.tensor([0.1490, 0.1647, 0.2157])


def yukle(run):
    ck = sorted(K_.glob(f'runs/{run}/**/step-*.ckpt'), key=lambda p: int(re.search(r'(\d+)\.ckpt', p.name).group(1)))[-1]
    st = torch.load(ck, map_location='cpu', weights_only=False)['pipeline']
    g = {k.split('gauss_params.')[1]: v for k, v in st.items() if 'gauss_params.' in k}
    dp = json.load(open(sorted(K_.glob(f'runs/{run}/**/dataparser_transforms.json'))[-1]))
    print(run, ck.name, g['means'].shape[0], flush=True)
    return {k: v.cuda() for k, v in g.items()}, dp


def ciz(g, c2w, K, w, h):
    R = c2w[:3, :3] @ np.diag([1, -1, -1]); t = c2w[:3, 3]
    vm = np.eye(4); vm[:3, :3] = R.T; vm[:3, 3] = -R.T @ t
    col = torch.cat([g['features_dc'][:, None, :], g['features_rest']], 1)
    out, _, _ = rasterization(g['means'], g['quats'] / g['quats'].norm(dim=-1, keepdim=True), torch.exp(g['scales']),
                              torch.sigmoid(g['opacities']).squeeze(-1), col,
                              torch.tensor(vm, dtype=torch.float32, device='cuda')[None],
                              torch.tensor(K, dtype=torch.float32, device='cuda')[None], w, h,
                              sh_degree=3, backgrounds=BG.cuda()[None])
    return (out[0].clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)


tf = json.load(open(K_ / 'ns' / RUNS[0] / 'transforms.json'))
fr = {Path(f['file_path']).name: f for f in tf['frames']}
test = [n for n in tf['test_filenames']]
A = np.vstack([np.array(tf.get('applied_transform', [[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, -1, 0]])), [0, 0, 0, 1]])
Km = np.array([[tf['fl_x'], 0, tf['cx']], [0, tf['fl_y'], tf['cy']], [0, 0, 1]])
dist = np.array([tf.get('k1', 0), tf.get('k2', 0), tf.get('p1', 0), tf.get('p2', 0), 0.0])
W, H = tf['w'], tf['h']
newK, (rx, ry, rw, rh) = cv2.getOptimalNewCameraMatrix(Km, dist, (W, H), 0)
newK = newK.copy(); newK[0, 2] -= rx; newK[1, 2] -= ry
modeller = [yukle(r) for r in RUNS]
with torch.no_grad():
    for fp in test:
        nm = Path(fp).name
        gt = cv2.cvtColor(cv2.imread(str(K_ / 'frames_1440' / nm)), cv2.COLOR_BGR2RGB)
        gt = cv2.undistort(gt, Km, dist, None, newK + np.array([[0, 0, rx], [0, 0, ry], [0, 0, 0]]))[ry:ry + rh, rx:rx + rw]
        sat = [gt]
        for g, dp in modeller:
            c2w = np.array(fr[nm]['transform_matrix'])
            # dataparser_transforms 'transform' COLMAP koordinatlarından; transforms.json pozlarına applied_transform zaten uygulanmış
            T = np.vstack([np.array(dp['transform']), [0, 0, 0, 1]]) @ np.linalg.inv(A)
            c2w = T @ c2w; c2w[:3, 3] *= dp['scale']
            sat.append(ciz(g, c2w, newK, rw, rh))
        sat = [cv2.resize(s, (960, round(960 * rh / rw)), interpolation=cv2.INTER_AREA) for s in sat]
        cv2.imwrite(str(OUT / nm), cv2.cvtColor(np.hstack(sat), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
        print(nm, flush=True)
print('RENDER BİTTİ', flush=True)
