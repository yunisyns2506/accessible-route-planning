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
