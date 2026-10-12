# 3DGS ve VR/Simülasyon Destekli Erişilebilir Rota Planlama Sistemi

[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![PyTorch 2.1.2](https://img.shields.io/badge/PyTorch-2.1.2%2Bcu118-red.svg)](https://pytorch.org/)
[![Nerfstudio 1.0.3](https://img.shields.io/badge/Nerfstudio-Splatfacto-orange.svg)](https://docs.nerf.studio/)
[![Unity 2022.3 LTS](https://img.shields.io/badge/Unity-2022.3%20LTS%20URP-black.svg)](https://unity.com/)

Bu proje, **Bursa Uludağ Üniversitesi Bilgisayar Mühendisliği Bölümü Tasarım Dersi** kapsamında geliştirilmekte olan; iç mekanların **3D Gaussian Splatting (3DGS)** ile foto-gerçekçi dijital ikizlerini üreten ve tekerlekli sandalye kullanan bireyler için erişilebilir rota planlayan simülasyon sistemidir.

---

## 👥 Proje Ekibi ve Danışman
* **Sabri Duruk**
* **Yunis Teymurlu**
* **Danışman:** Öğr. Gör. Koray AKİ

---

## 📁 Depo ve Klasör Mimarisi

Somut çalışmalar bağımsız klasörler halinde düzenlenmiştir:

```text
├── models/                                # Üretilen 3D Gaussian Splatting Modelleri
│   ├── v1_video/                          # İlk video denemesi (Sıfır paralaks analizi ve renderlar)
│   │   ├── README.md                      # Deney özeti
│   │   └── renders/                       # Çıkarılan kamera renderları
│   └── v2_fotograf/                       # 63 fotoğraflı nihai oda modeli (28.92 dB PSNR)
│       ├── README.md                      # Model başarı metrikleri
│       ├── splat.ply                      # 94.5 MB'lık 3DGS modeli (Git LFS)
│       └── renders/                       # Modelden alınan kamera renderları
├── setup/                                 # Kurulum Adımları ve Yardımcı Araçlar
│   ├── README.md                          # Windows ve macOS için adım adım kurulum
│   ├── kurulum_notlari.md                 # Çözülen CUB ve encoding sistem yamaları
│   ├── convert_heic.py                    # HEIC -> JPG dönüştürücü
│   ├── export_ply.py                      # PLY dışa aktarıcı
│   └── render_eval.py                     # PSNR değerlendirme scripti
├── src/                                   # Rota ve Graf Algoritmaları
│   └── accessroute/
│       ├── algorithms.py                  # A* ve TS 9111 erişilebilirlik graf algoritması
│       └── api.py                         # Test API'si
├── system-info.md                         # Donanım, CUDA ve Unity sürüm bilgisi
├── dependencies.md                        # Kullanılan kütüphaneler
├── pyproject.toml                         # Paket konfigürasyonu
└── CONTRIBUTING.md                        # Çalışma yönergeleri
```

---

## 📊 Yapılan Çalışmaların Karşılaştırması

| Parametre | Deney 1 (Video) | Deney 2 (63 Fotoğraf - Nihai) |
| :--- | :--- | :--- |
| **Kamera Sayısı** | 229 kare (sıfır öteleme) | **63 fotoğraf (gerçek baseline)** |
| **3B Nirengi Noktası** | 245 nokta (çökük geometri) | **18.499 nokta** |
| **Gaussian Sayısı** | 710.509 adet (iğneler) | **381.108 adet (katı yüzeyler)** |
| **Model Boyutu** | 176 MB | **94.5 MB** |
| **Ortalama PSNR** | ~22 - 24 dB | **28.92 dB** |

---

## 🚀 Hızlı Başlangıç

### Modeli İncelemek İçin:
1. [PlayCanvas SuperSplat](https://playcanvas.com/supersplat/editor) adresini açın.
2. `models/v2_fotograf/splat.ply` dosyasını tarayıcıya sürükleyin.

### Rota Algoritmasını Test Etmek İçin:
```bash
python -m src.accessroute.api
```
