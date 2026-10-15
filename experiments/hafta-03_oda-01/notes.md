# oda-01 — Koşu Kayıtları (Hafta 3 pilot)

Yorum ve bulgular: [`docs/raporlar/hafta-03_raporu.md`](../../docs/raporlar/hafta-03_raporu.md)
Ölçümler: [`metrics.csv`](metrics.csv) · Ortam: [`environment.md`](environment.md)
Tam ayar listeleri: `run-*/config.yml` · Model özetleri: `run-*/model-manifest.json`

Üçü de `splatfacto`, 30.000 iterasyon, `cache-images cpu`, RTX 2060 6 GB.

---

## run-01_video

**Girdi:** cep telefonu videosu (1920×1080), FFmpeg ile 309 kare.
**COLMAP:** 229 / 309 kaydoldu (%74,1), 2 model üretildi, en büyüğü kullanıldı.
30.752 nokta, iz uzunluğu 5,88, yeniden izdüşüm hatası 0,880 px.
**Ayarlar:** varsayılan (SH 3, `classic`, kamera opt. kapalı, `cull-alpha 0.1`).
**Sonuç:** 710.509 Gaussian, 168 MiB.

Serbest 3B bakışta boşlukta asılı iğne yapıları; çekim açısı dışında geometri
yok. SfM istatistikleri sağlıklı göründüğünden kök neden ayrıştırılamadı — aday
nedenler video karelerindeki hareket bulanıklığı, ardışık karelerin düşük bilgi
artışı ve dejenere bir SfM çözümüdür. Koşu elendi.

## run-02_63foto

**Girdi:** iPhone 0.5× ultra geniş açı, 79 fotoğraf (12 MP), HEIC → JPG.
**COLMAP:** sahne **üç modele parçalandı** (63 / 34 / 2 görüntü); eğitim en
büyüğü üzerinde. 18.499 nokta, iz uzunluğu **3,03** (düşük), hata 0,806 px.
**Ayarlar:** run-01 ile aynı.
**Sonuç:** 381.108 Gaussian, 90,1 MiB.

İğne artefaktları kayboldu; zemin, masa ve koridor geçişi gerçek derinlikle
oluştu. Eğitim görünümlerinde beş kamerada ölçülen PSNR ortalaması 28,92 dB —
ayrılmış test bölümü olmadığından genelleme kanıtı sayılmaz.

**Karşılaştırılabilirlik uyarısı:** bu koşunun COLMAP mapper ayarları diğer
ikisinden farklıdır (`init_min_tri_angle` 4 / 16; `abs_pose_min_num_inliers`
15 / 30; `max_reg_trials` 5 / 3; `tri_ignore_two_view_tracks` false / true).
Ayarın kaynağı kayıtlı değildir.

## run-03_512foto

**Girdi:** 512 fotoğraf (12 MP), EXIF yönlendirmesi piksellere uygulandı.
**COLMAP:** 476 / 512 (%93,0) tek birleşik modelde, 130.816 ikili kontrol.
75.678 nokta (4,1 kat artış), iz uzunluğu **7,90**, hata 1,078 px.
**Sonuç:** 696.207 Gaussian, 114 MiB.

**Varsayılandan sapan ayarlar:**

| Ayar | Değer | Varsayılan | Gerekçe |
| :--- | :--- | :--- | :--- |
| `sh_degree` | 2 | 3 | Küresel harmonik bellek tüketimi |
| `rasterize_mode` | antialiased | classic | Örnekleme hatası |
| `use_scale_regularization` / `max_gauss_ratio` | True / 5.0 | False / 10.0 | İğne Gaussian'ları baskılama |
| `camera_optimizer.mode` | SO3xR3 | off | COLMAP poz sapmaları |
| `densify_grad_thresh` | 0.0007 | 0.0008 | Yoğunlaştırma eşiği |
| `cull_alpha_thresh` | 0.006 | 0.1 | Daha az agresif budama |
| dataparser `downscale_factor` | 4 (756×1008) | — | 476 görüntüyü belleğe sığdırma |

`cache_images cpu` / `cache_images_type uint8` üç koşuda da aynıdır.

Veri yoğunluğu ve yedi ayar birlikte değiştiği için kazancın kaynağı
ayrıştırılamaz. Kamera merkezleri arasındaki medyan en yakın komşu mesafesi
0,0000 (SfM birimi): veri kümesinde neredeyse üst üste çakışan kareler var.

---

Hiçbir koşuda metrik ölçek belirlenmedi; bu modellerden metrik ifade
çıkarılamaz. Tek değişkenli karşılaştırma sınıf ölçeğinde yapılmıştır:
[`hafta-03_sinif-01/`](../hafta-03_sinif-01/)
