# 3DGS ve VR/Simülasyon Destekli Erişilebilir Rota Planlama Sistemi

[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![PyTorch 2.1.2](https://img.shields.io/badge/PyTorch-2.1.2%2Bcu118-red.svg)](https://pytorch.org/)
[![Nerfstudio 1.0.3](https://img.shields.io/badge/Nerfstudio-Splatfacto-orange.svg)](https://docs.nerf.studio/)

Bu proje, **Bursa Uludağ Üniversitesi Bilgisayar Mühendisliği Bölümü Tasarım Dersi** kapsamında geliştirilmekte olan; iç mekanların **3D Gaussian Splatting (3DGS)** ile foto-gerçekçi dijital ikizlerini üreten ve tekerlekli sandalye kullanan bireyler için erişilebilir rota planlayan simülasyon sistemidir.

---

## Proje Ekibi ve Danışman
* **Sabri Duruk**
* **Yunis Teymurlu**
* **Danışman:** Öğr. Gör. Koray AKİ

---

## Depo ve Klasör Mimarisi

Somut çalışmalar bağımsız klasörler halinde düzenlenmiştir:

```text
├── models/                                # Üretilen 3D Gaussian Splatting Modelleri
│   ├── v1_video/                          # Deney 1: İlk video denemesi (Sıfır paralaks analizi ve renderlar)
│   │   ├── README.md                      # Deney özeti
│   │   ├── splat.ply                      # 176 MB'lık 3DGS modeli (Git LFS)
│   │   └── renders/                       # Çıkarılan kamera renderları
│   ├── v2_fotograf/                       # Deney 2: 63 fotoğraflı oda modeli (28.92 dB PSNR)
│   │   ├── README.md                      # Model başarı metrikleri
│   │   ├── splat.ply                      # 94.5 MB'lık 3DGS modeli (Git LFS)
│   │   └── renders/                       # Modelden alınan kamera renderları
│   └── v3_512_fotograf/                   # Deney 3: 512 fotoğraflı yoğun oda modeli (Scale-Reg + SO3xR3)
│       ├── README.md                      # Optimizasyon ve metrik detayları
│       ├── splat.ply                      # 114 MB'lık 3DGS modeli (Git LFS)
│       └── renders/                       # Modelden alınan kamera renderları
├── setup/                                 # Kurulum Adımları ve Yardımcı Araçlar
│   ├── README.md                          # Adım adım kurulum kılavuzu
│   ├── kurulum_notlari.md                 # Çözülen CUB ve encoding sistem yamaları
│   ├── convert_heic.py                    # HEIC -> JPG dönüştürücü
│   ├── export_ply.py                      # PLY dışa aktarıcı
│   └── render_eval.py                     # PSNR değerlendirme scripti
├── system-info.md                         # Donanım ve CUDA sürüm bilgisi
└── dependencies.md                        # Kullanılan kütüphaneler
```

---

## Yapılan Çalışmaların Karşılaştırması

| Parametre | Deney 1 (Video) | Deney 2 (79 Fotoğraf) | Deney 3 (512 Fotoğraf - Yoğun) |
| :--- | :--- | :--- | :--- |
| **Eşleşen Kamera Sayısı** | 229 kare (sıfır öteleme) | 63 / 79 fotoğraf | **476 / 512 fotoğraf (%93)** |
| **3B Nirengi Noktası** | 245 nokta (çökük geometri) | 18.499 nokta | **75.678 nokta (4.1x artış)** |
| **Gaussian Sayısı** | 710.509 adet (iğneler) | 381.108 adet | **696.207 adet (Scale-Reg + Antialiased)** |
| **SH Derecesi & Optimizasyon** | SH 3 / Varsayılan | SH 3 / Varsayılan | **SH 2 / SO3xR3 Kamera Opt. / uint8 Cache** |
| **Model Boyutu** | 176 MB | 94.5 MB | **114 MB** |

---

## Hızlı Başlangıç

### Modelleri İncelemek İçin:
1. [PlayCanvas SuperSplat](https://playcanvas.com/supersplat/editor) adresini açın.
2. İncelemek istediğiniz modelin `.ply` dosyasını (`models/v1_video/splat.ply`, `models/v2_fotograf/splat.ply` veya `models/v3_512_fotograf/splat.ply`) tarayıcıya sürükleyin.


