# Deney Ortamı (Hafta 4 — sinif-01 COLMAP karşılaştırması)

Tüm SfM, 3DGS ve dense koşuları aynı makinede, sırayla (GPU'da aynı anda tek iş)
çalıştırılmıştır. Arka planda tarayıcı, Steam, Spotify, WhatsApp ve NVIDIA
Overlay açıktı; durum üç blok boyunca aynı tutuldu (boşta ~425 MiB VRAM).

| Bileşen | Değer |
| :--- | :--- |
| İşletim sistemi | Windows 11 Pro 64-bit, güç planı "Yüksek performans", uyku kapalı |
| GPU | NVIDIA GeForce RTX 2060, 6 GB, CC 7.5, sürücü 617.42 |
| CPU / RAM | Ryzen 5 3500X (6 çekirdek) / 16 GB DDR4 |
| COLMAP | 4.2.1 CUDA (commit bd1fcf6), `tools\colmap-4.2.1` |
| ONNX Runtime | 1.30.0 (COLMAP ile gelir), CUDA sağlayıcısı |
| CUDA 12 kütüphaneleri | cuBLAS 12.9.2, cudart 12.9.79, cuFFT 11.4.1, cuRAND 10.3.10, NVRTC 12.9.86 |
| cuDNN | 9.10.2 (9.27 Turing'de çalışmadı) |
| Modeller | `aliked-n16rot`, `aliked-lightglue`, `loma_detector`, `loma_descriptor_dedode_g`, `loma_matcher_B`; SIFT ve ALIKED sözlük ağaçları (SHA256 doğrulandı) |
| Python / PyTorch | 3.10.13 / 2.1.2+cu118 (conda `nerfstudio`) |
| Nerfstudio / gsplat | 1.0.3 / 0.1.4 (yerel yamalı) |
| Ölçüm | psutil 7.2.2 (süreç ağacı RSS), `nvidia-smi` (GPU geneli, taban değer ayrıca kayıtlı) |
