# Bağımlılıklar ve Lisanslar (Dependencies)

Bu dosya, projenin tüm modüllerinde kullanılan açık kaynak yazılımları, kütüphaneleri ve lisans bilgilerini listeler.

---

## 1. Python ve Derin Öğrenme Bağımlılıkları

```text
torch==2.1.2+cu118
torchvision==0.16.2+cu118
nerfstudio==1.0.3
gsplat==0.1.4
pillow-heif>=0.14.0
opencv-python>=4.8.0
trimesh>=4.0.0
numpy>=1.24.0,<2.0.0
scipy>=1.11.0
matplotlib>=3.7.0
rich>=13.4.0
pyyaml>=6.0
```

---

## 2. Dış Sistem Araçları

* **COLMAP 3.9.1 (CUDA Destekli):**
  * *İşlev:* Fotoğraflardan SIFT öznitelik çıkarımı, eşleştirme ve seyrek 3B nokta bulutu (SfM) üretimi.
  * *Lisans:* BSD-3-Clause
* **FFmpeg:**
  * *İşlev:* Video dosyalarından kare çıkarma ve ses/görüntü kodlama.
  * *Lisans:* LGPL / GPL
* **Git LFS (Large File Storage):**
  * *İşlev:* 94.5 MB ve üzeri 3D Gaussian Splatting (`.ply`) dosyalarının GitHub üzerinde sürümlenmesi.

---

## 3. Görselleştirme ve Simülasyon Bağımlılıkları

* **Unity Editor:** `6000.1.17f1` (URP)
* **UnityGaussianSplatting:**
  * *Geliştirici:* Aras Pranckevicius (`aras-p`)
  * *Depo:* [https://github.com/aras-p/UnityGaussianSplatting](https://github.com/aras-p/UnityGaussianSplatting)
  * *İşlev:* 3D Gaussian Splatting modellerini (`.ply`) Unity içinde gerçek zamanlı GPU rasterizasyonu ile render eder.
  * *Lisans:* MIT
