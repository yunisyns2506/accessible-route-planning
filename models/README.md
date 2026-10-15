# Üretilen 3DGS Modelleri

Dosyalar Git LFS ile saklanır; klonladıktan sonra `git lfs pull` gerekir.
İncelemek için [SuperSplat](https://playcanvas.com/supersplat/editor)'e sürükleyin.

Koşu kayıtları: [`experiments/hafta-03_oda-01/`](../experiments/hafta-03_oda-01/)

| Model | Girdi | COLMAP | SfM noktası | Gaussian | Boyut |
| :--- | :--- | :--- | ---: | ---: | ---: |
| `oda-01_v1_video` | 309 video karesi | 229 (%74,1) | 30.752 | 710.509 | 168 MiB |
| `oda-01_v2_fotograf` | 79 fotoğraf | 63 (%79,7) | 18.499 | 381.108 | 90,1 MiB |
| `oda-01_v3_512fotograf` | 512 fotoğraf | 476 (%93,0) | 75.678 | 696.207 | 114 MiB |

Üçü de `splatfacto`, 30.000 iterasyon, RTX 2060 6 GB.

## v1 — video tabanlı (elendi)

Serbest 3B bakışta boşlukta asılı iğne yapılarından oluşan girdap görünümü;
çekim açısı dışında kullanılabilir geometri yok. SfM istatistikleri sağlıklı
(iz uzunluğu 5,88, yeniden izdüşüm hatası 0,880 px) olduğundan kök neden
ayrıştırılamadı; aday nedenler video karelerindeki hareket bulanıklığı ve
ardışık karelerin düşük bilgi artışıdır.

## v2 — 79 fotoğraf

İğne artefaktları kayboldu, zemin ve koridor geçişi gerçek derinlikle oluştu.
COLMAP sahneyi tek modelde birleştiremedi (63 / 34 / 2 görüntülük üç model);
ortalama iz uzunluğu 3,03 ile düşük. Eğitim görünümlerinde ölçülen PSNR
ortalaması 28,92 dB — ayrılmış test bölümü olmadığından genelleme kanıtı
sayılmaz.

## v3 — 512 fotoğraf, optimize ayarlar

476 görüntü tek birleşik modelde çözüldü, iz uzunluğu 7,90'a yükseldi.
Varsayılandan sapan ayarlar: `sh-degree 2`, `rasterize-mode antialiased`,
`use-scale-regularization` (ratio 5.0), `camera-optimizer SO3xR3`,
`cull-alpha-thresh 0.006`, `downscale-factor 4`.

Veri yoğunluğu ve yedi ayar birlikte değiştiği için kazancın kaynağı
ayrıştırılamaz. Sınıf ölçeğindeki tek değişkenli karşılaştırma:
[`docs/raporlar/hafta-03_raporu.md`](../docs/raporlar/hafta-03_raporu.md)

> Hiçbir koşuda metrik ölçek belirlenmedi; bu modellerden kapı açıklığı veya
> koridor genişliği gibi metrik ifade çıkarılamaz.


---

# Sınıf Modelleri (sinif-01)

D207 dersliğinde yapılan yöntem karşılaştırmasının çıktıları. Hepsi aynı COLMAP
çıktısını (331 kare, `exhaustive` eşleştirme) ve aynı 298 / 33 eğitim-test
bölünmesini kullanır; her koşuda yalnızca bir ayar değişir.

Ölçümler ayrılmış 33 test karesinde `ns-eval` ile alınmıştır. Ayrıntı:
[`docs/raporlar/hafta-03_raporu.md`](../docs/raporlar/hafta-03_raporu.md)

| Model | Değişen ayar | İterasyon | PSNR | SSIM | LPIPS | Gaussian | Boyut |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| `sinif-01_G1_varsayilan` | — (varsayılan) | 15.000 | 27,22 | 0,9091 | 0,1759 | 551.246 | 130 MB |
| `sinif-01_G2_antialiased` | `antialiased` | 15.000 | 27,38 | 0,9111 | 0,1697 | 565.603 | 134 MB |
| **`sinif-01_G2_antialiased_30k`** | `antialiased` | **30.000** | **28,05** | **0,9142** | **0,1525** | 566.064 | 134 MB |
| `sinif-01_G3_scalereg` | ölçek düzenlemesi | 15.000 | 27,14 | 0,9084 | 0,1838 | 534.193 | 127 MB |
| `sinif-01_G4_camopt` | kamera pozu opt. (SO3xR3) | 15.000 | 22,52 | 0,7794 | 0,2119 | 540.495 | 128 MB |
| `sinif-01_G5_big` | `splatfacto-big` | 15.000 | 26,55 | 0,9031 | 0,1757 | 1.289.932 | 306 MB |
| `sinif-01_G6_tamcozunurluk` | tam çözünürlük (1080×1920) | 15.000 | 26,87\* | 0,9053\* | 0,2705\* | 673.386 | 160 MB |

\* G6 metrikleri 1080×1920'de, diğerleri 540×960'ta hesaplandığından diğer
satırlarla karşılaştırılamaz.

**Önerilen model:** `sinif-01_G2_antialiased_30k` — üç metrikte de en iyi sonucu
veren yapılandırmanın 30.000 iterasyonlu hâli.

**İnceleme önerisi:** `G2_antialiased_30k` ile `G4_camopt` modellerini arka arkaya
açarsanız kamera pozu optimizasyonunun sahneyi kaydırdığı görülür — render net
olmasına karşın geometri gerçek konumundan ötelenmiştir.

> Hiçbir modelde metrik ölçek kurulmamıştır; bu dosyalardan kapı açıklığı veya
> geçiş genişliği gibi metrik değerler çıkarılamaz.
