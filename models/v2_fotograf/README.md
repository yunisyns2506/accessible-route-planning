# 3DGS Model Versiyonu 2 (63 Fotoğraf Tabanlı Başarılı Oda Modeli)

## 1. Model Özeti ve Başarı Metrikleri
* **Yöntem:** Nerfstudio - `splatfacto`
* **Girdi:** iPhone 0.5x Ultra Geniş Açılı Lens ile adımlayarak çekilmiş 79 adet fotoğraf (12 MP, 3024x4032, JPG)
* **COLMAP Eşleşmesi:** **63 fotoğraf** tek çatı altında bağlandı (16 fotoğraf dokusuz beyaz dolap nedeniyle elendi).
* **Başlangıç 3B Nokta Bulutu:** **18.499 adet gerçek nirengi noktası**
* **Kamera Modeli:** `OPENCV` (Geniş açı distorsiyon katsayıları optimize edildi)
* **Eğitim:** 30.000 iterasyon (RTX 2060 6GB VRAM için CPU Caching ile)
* **Gaussian Sayısı:** **381.108** (0 NaN/Inf)
* **Dosya Boyutu:** **94.5 MB** (`splat.ply`)
* **Görsel Kalite (PSNR):**
  * Kamera 0 (Masa): **28.35 dB**
  * Kamera 15 (Yatak): **32.82 dB**
  * Kamera 30 (Koridor): **25.45 dB**
  * Kamera 45 (Yan Duvar): **26.48 dB**
  * Kamera 56 (Giriş): **31.53 dB**
  * **Ortalama Test PSNR: 28.92 dB**

---

## 2. Geometrik İyileştirmeler (v1 vs v2)
1. **Derinlik Paralaksı Sağlandı:** Adımlayarak çekilen fotoğraflar sayesinde zemin parkeleri, çalışma masası, yatak ve kapı arasındaki geçiş koridoru gerçek 3B derinlikle oluşmuştur.
2. **Kutu Hacmi Oturumu:** Nokta bulutu standart sapması $\sigma = [3.09, 3.48, 3.07]$ metre ile odanın gerçek dikdörtgen kutu hacmine oturmuştur.
3. **Erişilebilirlik Açıklığı:** Koridordaki net geçiş genişliği (~90 cm) model üzerinde doğrulanabilir hale gelmiştir.

---

## 3. Dosyalar
* `splat.ply` (94.5 MB): SuperSplat ve 3B görüntüleyiciler için eğitilmiş Gaussian Splatting dosyası (Git LFS).
* `renders/`: Modelden render edilmiş iç mekan kamera görünümleri ve gerçek görüntülerle karşılaştırmaları (`photo_render_*.png`, `photo_gt_*.png`).
