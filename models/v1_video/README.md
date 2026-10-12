# 3DGS Model Versiyonu 1 (Video Tabanlı Pilot Deneme)

## 1. Model Özeti ve Girdi Verisi
* **Yöntem:** Nerfstudio - `splatfacto`
* **Girdi:** 4 parça cep telefonu videosu (`room-01.mp4`, 1920x1080 @ 60 FPS, toplam 7.720 kare)
* **Kamera Çıkarımı:** 229 kare eşit aralıklarla çıkarıldı.
* **COLMAP Eşleşmesi:** 229 kare tek modelde bağlandı.
* **Eğitim:** 30.000 iterasyon
* **Gaussian Sayısı:** 710.509
* **Dosya Boyutu:** 176 MB

---

## 2. Karşılaşılan Problem: Sıfır Paralaks ve İğne Girdabı (Needle Artifacts)
* **Hata Tipi:** 3B Geometrik Çökme (Degenerate Geometry).
* **Neden:** Kullanıcı odanın merkezinde sabit durarak telefonu yalnızca kendi ekseni etrafında döndürmüştür (Pure Rotation). Kameralar arasında yatay öteleme (baseline) sıfıra yakın olduğu için çoklu bakış geometrisinde (Multi-View Epipolar Geometry) derinlik üçgenlemesi (triangulation) yapılamamıştır.
* **Görsel Sonuç:** 2B açılardan bakıldığında görüntü oluşsa da, serbest 3B uzayda (SuperSplat) model silindirik, boşlukta asılı duran iğnelerden oluşan bir girdap şeklinde çökmüştür.

---

## 3. Dosyalar ve Örnek Renderlar
* `splat.ply` (176 MB): Video tabanlı ilk denemenin 3DGS model dosyası (Git LFS).
* `renders/` altındaki görüntüler, modelin yalnızca çekilen açılardan geçerli olduğunu, serbest açılarda geometrinin bulunmadığını göstermektedir:
  * `renders/test_render_0.png` - Çalışma masası açısı
  * `renders/test_render_50.png` - Koridor açısı
  * `renders/test_render_100.png` - Yatak açısı
  * `renders/test_render_150.png` - Kapı çıkışı açısı

---

## 4. Alınan Karar
Bu model geometrik çökme nedeniyle elenmiş; gerçek adımlama (baseline) ve 0.5x ultra geniş açılı fotoğraflarla **Versiyon 2** ve **Versiyon 3** üretilmiştir.
