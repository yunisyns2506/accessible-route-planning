# Sistem Kurulum Basamakları (Setup Guide)

Bu rehber, projenin 3D Gaussian Splatting (COLMAP + Nerfstudio Splatfacto) eğitim ortamının sıfırdan nasıl kurulacağını adım adım anlatır.

---

## 1. Donanım ve İşletim Sistemi Gereksinimleri

* **İşletim Sistemi:** Windows 10/11 (64-bit)
* **GPU / Hızlandırıcı:** NVIDIA RTX 2060 (6GB VRAM)
* **CUDA Sürümü:** CUDA 11.8
* **Ana Görev:** COLMAP SfM, Nerfstudio Splatfacto 3DGS Eğitimi

---

## 2. Windows Üzerinde 3DGS Ortam Kurulumu (Adım Adım)

### Adım 2.1: Git LFS ve Depo Klonlama
```bash
git lfs install
git clone https://github.com/yunisyns2506/accessible-route-planning.git
cd accessible-route-planning
git lfs pull
```

### Adım 2.2: Conda Ortamı ve PyTorch Kurulumu
```bash
conda create -n nerfstudio python=3.10 -y
conda activate nerfstudio

# PyTorch CUDA 11.8
pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cu118
```

### Adım 2.3: COLMAP ve FFmpeg Kurulumu
1. **COLMAP 3.9+ CUDA:** İndirip `C:\Users\<user>\tools\colmap` klasörüne açın ve Sistem PATH ortam değişkenine ekleyin.
2. **FFmpeg:** `C:\Users\<user>\tools\ffmpeg` yoluna ekleyin.

### Adım 2.4: Nerfstudio ve gsplat Kurulumu
```bash
pip install nerfstudio==1.0.3
pip install pillow-heif trimesh opencv-python
```

> [!WARNING]
> **Windows RPC `rpcndr.h` vs CUDA CUB Hatası Çözümü:**
> Windows SDK'nın `rpcndr.h` dosyasındaki `#define small char` makrosu CUDA 11.8 CUB kütüphanesiyle çakışır. Detaylı çözüm ve yama adımları için [`kurulum_notlari.md`](kurulum_notlari.md) dosyasına bakın.

---

## 3. Model Eğitme ve Dışa Aktarma Komutları

### Veri Seti Ön İşleme (COLMAP):
```bash
python -m nerfstudio.scripts.process_data images --data data/room-01-photos/raw_images --output-dir data/room-01-photos/processed --matching-method exhaustive
```

### Splatfacto 3DGS Eğitimi (RTX 2060 6GB Optimize):
```bash
python -m nerfstudio.scripts.train splatfacto --data data/room-01-photos/processed --output-dir outputs-photos --pipeline.datamanager.cache-images cpu --pipeline.model.cull-alpha-thresh 0.1 --max-num-iterations 30000
```

### PLY Olarak Dışa Aktarma:
```bash
python setup/export_ply.py
```
