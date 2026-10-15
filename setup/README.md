# Sistem Kurulum Basamakları (Setup Guide)

Bu rehber, projenin 3D Gaussian Splatting (COLMAP + Nerfstudio Splatfacto) eğitim ortamının sıfırdan nasıl kurulacağını adım adım anlatır.

---

## 1. Donanım ve İşletim Sistemi Gereksinimleri

* **İşletim Sistemi:** Windows 10/11 (64-bit)
* **GPU / Hızlandırıcı:** NVIDIA RTX 2060 (6GB VRAM)
* **CUDA Sürümü:** CUDA 11.8

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

Aşağıdaki komutlar hafta 3 pilot koşularında fiilen kullanılan komutlardır.
Hazır çalıştırılabilir hâlleri `scripts/` klasöründedir; eğitimde kullanılan
ayarların doğrulanmış tam listesi ise ilgili koşunun
`experiments/hafta-03_oda-01/*/config.yml` dosyasındadır.

### run-02 — 79 fotoğraf, varsayılan ayarlar (`scripts/process_photos.bat`, `scripts/train_photos_splatfacto.bat`)
```bash
python -m nerfstudio.scripts.process_data images   --data data/oda-01_79foto/raw_images   --output-dir data/oda-01_79foto/processed   --matching-method exhaustive

python -m nerfstudio.scripts.train splatfacto   --data data/oda-01_79foto/processed --output-dir outputs-photos   --pipeline.datamanager.cache-images cpu   --pipeline.model.cull-alpha-thresh 0.1   --max-num-iterations 30000
```

### run-03 — 512 fotoğraf, optimize ayarlar (`scripts/run3_process_colmap.bat`, `scripts/train_run3_splatfacto.bat`)
```bash
python -m nerfstudio.scripts.process_data images   --data data/oda-01_512foto/raw_images   --output-dir data/oda-01_512foto/processed   --camera-type perspective --matching-method exhaustive --num-downscales 3

python -m nerfstudio.scripts.train splatfacto   --data data/oda-01_512foto/processed --output-dir outputs-run3   --experiment-name oda_run3 --max-num-iterations 30000   --pipeline.model.rasterize-mode antialiased   --pipeline.model.use-scale-regularization True --pipeline.model.max-gauss-ratio 5.0   --pipeline.model.densify-grad-thresh 0.0007 --pipeline.model.stop-split-at 15000   --pipeline.model.cull-alpha-thresh 0.006 --pipeline.model.sh-degree 2   --pipeline.model.camera-optimizer.mode SO3xR3   --pipeline.datamanager.cache-images cpu   --pipeline.datamanager.cache-images-type uint8   nerfstudio-data --downscale-factor 4
```

> `--matching-method exhaustive` eşleştirme maliyeti görüntü sayısıyla karesel
> büyür; bina ölçeğinde uygulanabilir değildir. `sequential` ile karşılaştırma
> hafta 4 koşu planındadır (`docs/raporlar/hafta-03_raporu.md`, Bölüm 5).

### PLY olarak dışa aktarma
```bash
python setup/export_ply.py
```

### Değerlendirme
```bash
python setup/render_eval.py
```

> **Uyarı:** `render_eval.py` kameraları eğitim kümesinden (`train_dataset`) alır
> ve 5 sabit indeks kullanır; ürettiği değer **train-view PSNR**'dır. Train/eval
> ayrımlı metrik için nerfstudio'nun `ns-eval` komutuna geçilmesi gerekir.
