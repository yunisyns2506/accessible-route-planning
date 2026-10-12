# 3DGS Model Versiyonu 3 (512 Fotoğraf Tabanlı Yoğun Oda Modeli)

## 1. Model Özeti ve Başarı Metrikleri
* **Yöntem:** Nerfstudio - `splatfacto`
* **Girdi:** 512 adet iç mekan fotoğrafı (12 MP, EXIF dikey yönlendirmesi düzeltilmiş 3024x4032 JPG)
* **COLMAP Eşleşmesi:** **476 / 512 fotoğraf (%93.0)** tek bir birleşik sahnede eşleşti (`exhaustive_matcher`, 130.816 ikili eşleşme kontrolü).
* **Başlangıç 3B Nokta Bulutu:** **75.678 adet nirengi noktası** (Deney 2'ye kıyasla **4.1 kat** artış)
* **Ortalama İz Uzunluğu (Mean Track Length):** **7.90** görüntü/nokta
* **Ortalama Yeniden İzdüşüm Hatası (Reprojection Error):** **1.07 px**
* **Kamera Modeli:** `OPENCV` (Tekil kamera ve distorsiyon kalibrasyonu)
* **Eğitim:** 30.000 iterasyon (RTX 2060 6GB VRAM ve Host RAM optimizasyonlu)
* **Gaussian Sayısı:** **696.207** (0 NaN/Inf)
* **Dosya Boyutu:** **114 MB** (`splat.ply`)

---

## 2. Deney 2'ye Göre Farklılıklar ve Uygulanan Optimizasyonlar
1. **Veri Seti ve Kapsama Yoğunluğu (79 $\rightarrow$ 512 Fotoğraf):**
   * Önceki denemede 63 kamera ve 18.499 nirengi noktası bulunurken, bu denemede **476 kamera** ve **75.678 gerçek 3B nirengi noktası** elde edilerek odanın kör noktaları ve yüzey detayları çok daha yoğun şekilde tarandı.
2. **EXIF Yönlendirme Ön İşlemesi:**
   * Ham fotoğraflardaki EXIF Orientation (Tag 6 - Saat yönünde 90°) verisi eğitim öncesi fiziksel piksellere uygulanarak COLMAP ve görüntü önbellekleme aşamalarındaki yönelim uyuşmazlıkları giderildi.
3. **Host Pinned Memory ve 6 GB VRAM Bellek Optimizasyonu:**
   * 476 adet yüksek çözünürlüklü görüntünün `float32` formatında RAM'e önbelleklenmesi sırasında oluşan ~17.4 GB CUDA Pinned Memory taşmasını önlemek için `--pipeline.datamanager.cache-images-type uint8` ve `--downscale-factor 4` (756x1008 çözünürlük) kullanıldı.
   * `--pipeline.model.sh-degree 2` seçilerek küresel harmonik katsayılarının bellek tüketimi %40 azaltıldı.
4. **Geometrik ve Kamera Optimizasyonu Parametreleri:**
   * **Scale Regularization (`use-scale-regularization True`, `max-gauss-ratio 5.0`):** Farklı bakış açılarından bakıldığında uzayan "iğne/çubuk" şeklindeki bozuk Gaussian oluşumları engellendi.
   * **Antialiased Rasterization (`rasterize-mode antialiased`):** Kenar yumuşatma aktif edilerek daha pürüzsüz yüzey geçişleri sağlandı.
   * **Kamera Poz Optimizasyonu (`camera-optimizer.mode SO3xR3`):** Eğitim esnasında ufak COLMAP kamera poz sapmaları optimize edildi.
   * **Kontrollü Yoğunlaştırma (`densify-grad-thresh 0.0007`, `stop-split-at 15000`, `cull-alpha-thresh 0.006`):** Gereksiz splat patlaması sınırlandırılarak 696 bin temiz Gaussian elde edildi.

---

## 3. Dosyalar
* `splat.ply` (114 MB): SuperSplat ve 3B görüntüleyiciler için eğitilmiş 3D Gaussian Splatting modeli (Git LFS).
* `renders/`: Modelden alınan örnek kamera renderları ve orijinal görüntülerle karşılaştırmaları (`run3_render_*.png`, `run3_gt_*.png`).
