# Bağımlılıklar ve Lisanslar

**Durum** sütunu, bileşenin fiilen çalıştırıldığını mı yoksa sonraki aşamalar
için planlandığını mı gösterir. Listede bulunmak kurulu olduğu anlamına gelmez.

Kurulum yalnızca eğitim istasyonunda yapılmıştır (donanım:
[`system-info.md`](system-info.md)).

---

## Kurulu ve çalıştırılmış

Hafta 3 ve hafta 4 koşularında fiilen kullanılan sürümler. COLMAP 4.2.1 kurulumu:
[`setup/colmap4_kurulum.md`](../setup/colmap4_kurulum.md)

| Bileşen | Sürüm | İşlev | Lisans |
| :--- | :--- | :--- | :--- |
| Python | 3.10.13 | conda `nerfstudio` ortamı | PSF |
| PyTorch | 2.1.2+cu118 | Tensör hesaplama | BSD tarzı |
| Nerfstudio | 1.0.3 | Veri hazırlama, Splatfacto, `ns-eval` | Apache-2.0 |
| gsplat | 0.1.4 | Gaussian rasterizasyon çekirdeği (yerel yamalı) | Apache-2.0 |
| tiny-cuda-nn | kaynak (SM 75) | NeRF hash kodlaması | BSD-3-Clause |
| COLMAP | 3.9.1 CUDA | SIFT, eşleştirme, SfM (hafta 3) | BSD-3-Clause |
| COLMAP | 4.2.1 CUDA | SIFT / ALIKED / LoMa, LightGlue, global ve hierarchical SfM (hafta 4) | BSD-3-Clause |
| ONNX Runtime | 1.30.0 (COLMAP 4.2.1 ile gelir) | ALIKED, LightGlue, LoMa çıkarımı | MIT |
| CUDA 12 çalışma kütüphaneleri | cuBLAS 12.9, cudart 12.9, cuFFT 11.4 | ONNX Runtime CUDA sağlayıcısı (ayrı klasör) | NVIDIA EULA |
| cuDNN | 9.10.2 | ONNX Runtime evrişimleri (9.27 Turing'de çalışmadı) | NVIDIA SLA |
| ALIKED / LightGlue ONNX | COLMAP 3.13.0 sürüm dosyaları | Öğrenme tabanlı çıkarıcı / eşleştirici | BSD-3-Clause / Apache-2.0 |
| LoMa ONNX | COLMAP 4.2.1 varsayılan modelleri | Öğrenme tabanlı çıkarıcı + eşleştirici | kaynak deposuna bakınız |
| psutil | 7.2.2 | Koşu sırasında tepe RAM ölçümü | BSD-3-Clause |
| pycolmap | 4.2.1 (ayrı klasör, `tools\pycolmap-4.2.1`) | LoMa için 256 boyutlu sözlük ağacı denemesi | BSD-3-Clause |
| FFmpeg | 6.1+ | Videodan kare çıkarma | LGPL / GPL |
| OpenCV | 4.8+ | Kare netliği ölçümü, görsel üretimi | Apache-2.0 |
| pillow-heif | 0.14+ | HEIC → JPG (oda-01 fotoğrafları) | LGPL |
| python-docx | 1.2.0 | Raporun `.docx`'e çevrilmesi | MIT |
| CUDA Toolkit | 11.8 | NVCC derleyicisi | NVIDIA EULA |
| MSVC Build Tools | 14.44.35207 | gsplat ve tiny-cuda-nn derlemesi | Microsoft |
| Git LFS | 3.6.0 | `.ply` dosyalarının sürümlenmesi | MIT |

Derleme sırasında çözülen sürüm çakışmaları:
[`setup/kurulum_notlari.md`](../setup/kurulum_notlari.md)

---

## Planlanan (henüz kurulmadı)

| Bileşen | Aşama | İşlev | Lisans |
| :--- | :--- | :--- | :--- |
| Unity Editor | A2 | Simülasyon ortamı (`6000.1.17f1 URP` adayı) | Unity Companion |
| UnityGaussianSplatting | A2 | `.ply` modellerin Unity'de render edilmesi | MIT |
| Open3D | A3 | Nokta bulutu, düzlem ve mesafe hesapları | MIT |
| MMDetection | A4 | Mask R-CNN / RTMDet-Ins çatısı | Apache-2.0 |
| SAM 2 | A4 | Etiketlemede maske hazırlama | Apache-2.0 |
| CVAT | A4 | Etiketleme platformu | MIT |
| NetworkX | A4 | Erişilebilirlik çizgesi, Dijkstra ve A* | BSD-3-Clause |
| pytest | A4 | Dönüşüm ve rota testleri | MIT |
| XR Interaction Toolkit | A5 | VR etkileşimi | Unity Companion |

---

## Değerlendirilip kullanılmayanlar

2DGS, SuGaR, FreeSplat, tam Mip-Splatting ve `instant-ngp` denenmedi; gerekçeler
[`hafta-03_raporu.md`](../docs/raporlar/hafta-03_raporu.md)
geçerlilik sınırları bölümündedir.
