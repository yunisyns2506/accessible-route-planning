# Sistem ve Donanım Bilgisi (System Info)

Bu doküman, projenin geliştirildiği donanım, işletim sistemi, sürücüler, kütüphane sürümleri ve çözülen sistem seviyesi çakışmaları detaylandırır.

---

## 1. Donanım Özellikleri

### Birincil Geliştirme İstasyonu (Windows - Model Eğitimi):
* **İşletim Sistemi:** Windows 11 Pro 64-bit
* **İşlemci (CPU):** AMD Ryzen / Intel Core (x86_64)
* **Ekran Kartı (GPU):** NVIDIA GeForce RTX 2060
  * **VRAM Kapasitesi:** 6144 MB (6 GB GDDR6)
  * **CUDA Compute Capability:** 7.5 (Turing)
* **Sistem Belleği (RAM):** 16 GB DDR4
* **Depolama:** NVMe M.2 SSD

### İkincil Geliştirme İstasyonu (macOS - Unity & Simülasyon):
* **İşletim Sistemi:** macOS 14+ (Sonoma / Sequoia)
* **Mimari:** Apple Silicon (ARM64 - M1 / M2 / M3 / M4)
* **Grafik API:** Apple Metal (Metal 3)
* **İşlev:** Unity Editor sahne entegrasyonu, tekerlekli sandalye First-Person simülasyonu ve A* rota planlama algoritmalarının yürütülmesi.

---

## 2. Yazılım ve Kütüphane Sürümleri

| Bileşen | Sürüm | Açıklama |
| :--- | :--- | :--- |
| **Python** | 3.10.13 | Conda `nerfstudio` yalıtılmış ortamı |
| **PyTorch** | 2.1.2+cu118 | CUDA 11.8 derlemesi |
| **CUDA Toolkit** | 11.8 (V11.8.89) | NVCC derleyicisi ve CUB kütüphanesi |
| **NVIDIA Driver** | 535+ / 550+ | Game Ready / Studio Driver |
| **Nerfstudio** | 1.0.3 | Ana 3DGS ve Splatfacto çerçevesi |
| **gsplat** | 0.1.4 (Özel Yamalı) | Hızlı CUDA rasterizasyon çekirdeği |
| **COLMAP** | 3.9.1 CUDA | Yapılandırılmış SfM (Structure-from-Motion) |
| **FFmpeg** | 6.1+ / 7.0+ | Video işleme ve kare çıkarımı |
| **Git & Git LFS** | Git 2.44+ / LFS 3.6.0 | Büyük model dosyaları (`.ply`) için |
| **Unity** | 2022.3 LTS (URP) | Simülasyon ve görselleştirme ortamı |

---

## 3. Sistem Seviyesi Çözümler ve Yamalar (Troubleshooting)

1. **Windows RPC - CUB Çakışması (`#undef small`):**
   * Windows SDK `rpcndr.h` dosyasındaki `#define small char` makrosu CUDA 11.8 CUB kütüphanesindeki `dispatch_segmented_sort.cuh` ile çakışıyordu.
   * `gsplat/cuda/csrc` altındaki 20 dosya `#ifdef small \n #undef small \n #endif` ile yamalanıp yerel olarak derlendi.
2. **Türkçe Windows Konsol Kodlaması (CP1254):**
   * Windows Türkçe konsolunda Rich kütüphanesi çökmekteydi.
   * `nerfstudio/utils/rich_utils.py` dosyasına `sys.stdout.reconfigure(encoding="utf-8")` eklenerek UTF-8 zorunlu kılındı.
3. **6 GB VRAM Sınırı ve Bellek Yönetimi:**
   * `--pipeline.datamanager.cache-images cpu` ve `--pipeline.model.cull-alpha-thresh 0.1` ayarlarıyla 6 GB VRAM taşması engellendi.
