# Hafta 6 · Derslik 4 koridoru (06.11 çekimi, işleme 07.11.2026)

Amaç: asansörden K3 kapısına giden yolun modeli. Video `derslik4_koridor.mov` (0,5×, 4K 30 fps, HEVC, 2,81 dk).

## Ayarlar ve sınıf hattından farklar

| Ayar | Koridor | Sınıf (06.11) |
| :--- | :--- | :--- |
| Kare aralığı | 0,40 sn (422 kare) | 0,80 sn (1500 kare) |
| Kare seçimi | eşit pencere, hareket < 15 px/kare olan en net kare | aynı |
| Test kareleri | her 10. kare (42) | aynı (150) |
| SfM | LoMa + sequential/döngü + incremental | aynı |
| 3DGS | 1440p splatfacto-big 30k; sonra aynı + H2 (bilateral grid) | 1080p splatfacto 30k (+ H2 ayrı) |
| Kesinti koruması | kontrol noktası 1000 adımda bir, Drive'a 10 dk'da bir; sürdürme testli | yok |

Koridorda ileri yürürken bakış hızlı değiştiği için kareler sınıftan sık alındı. Seçilen karelerin %10,7'si hız eşiğinin üstünde, %20,6'sı keskinlik medyanının yarısının altında (sınıfta %6,5 ve %13,7).

## Süre ve kaynak (Colab L4, 1,54 birim/sa)

| Aşama | Süre |
| :--- | ---: |
| Kurulum (COLMAP hazır derleme + 3DGS ortamı) | 27,8 dk |
| Video analizi + kare çıkarma (1080p ve 1440p) | 3,4 dk |
| SfM (çıkarma 7,5 + sözlük ağacı 21 + eşleştirme ve mapper 20) | 49,0 dk |
| Sürdürme testi (1080p, 300 + 500 adım) | ~1 dk |
| 1440p big eğitimi | 78,0 dk (RAM 14,9 GB, VRAM 7,6 GB) |
| 1440p big + H2 eğitimi | 112,8 dk (RAM 15,1 GB, VRAM 6,8 GB) |

## Sonuçlar

SfM: 422 / 422 kare kayıtlı, 87.602 nokta, ortalama iz uzunluğu 6,87, yeniden izdüşüm hatası 1,38 px.

| Model | PSNR (ham) | PSNR (renk düzeltmeli) | SSIM (r.d.) | LPIPS (r.d.) | Gaussian |
| :--- | ---: | ---: | ---: | ---: | ---: |
| 1440p big | 27,12 dB | 27,49 dB | 0,891 | 0,310 | 1,43 M |
| 1440p big + H2 | 22,02 dB | 26,09 dB | 0,893 | 0,300 | 1,37 M |

H2'de ham PSNR düşük; bilateral grid test karesinde nötr renk verdiği için ham değer yanıltıcı, renk düzeltmeli değerler karşılaştırılır. H2 LPIPS ve SSIM'i az iyileştirdi, renk düzeltmeli PSNR'ı 1,4 dB düşürdü. Görsel karşılaştırma yapılmadı.

## Sorunlar

1. **torch.load (07.11 16:25 TR):** Sürdürme testi geçti ama denetim adımı Colab'ın sistem torch'unda `weights_only` varsayılanı yüzünden çöktü; eğitim başlamadı. `weights_only=False` ile düzeltilip hat yeniden başlatıldı; biten aşamalar atlandı. L4 ~30 dk boşta kaldı.
2. **Ölçek tahmini:** 187,6 cm/birim, kamera yüksekliği 1,2 m varsayımıyla (gidiş 1,3–1,4 m, dönüş ~1 m). Mezura (M1 koridor genişliği, M4 asansör–K3) ile düzeltilecek.

## Çıktılar (Drive `Hafta 6 Çalışmaları/derslik4_koridor/`)

- Unity: `runs/unity/koridor_1440_big_unity.ply`, `runs/unity/koridor_1440_big_H2_unity.ply` (187,6 cm/birim, tahmini)
- Koşular: `runs/loma_sequential_loop_incremental_1440_big[_H2]/`, kontrol noktaları `ckpt/`
- Betikler: `scripts/hafta06/hat_koridor.py`, `egit_surdur.py` (Drive `betikler_koridor/`)

## Koridor ve sınıfın birleştirilmesi (08.11.2026)

Eğitim yapılmadı; iki modelin 3DGS sonuçları tek çerçeveye taşındı. Betikler: `scripts/hafta06/hizala_koridor.py`, `kapi_ac.py`. Yöntem:

1. **Ortak kareler (SIFT, L4):** 1500 sınıf karesi ve koridorun 130–300 arası 86 karesi. Kaba aramada ortak görüşlü kareler bulundu, 68 sınıf + 86 koridor karesiyle küçük ortak SfM kuruldu (67 + 74 kare kayıtlı).
2. **Dönüşüm:** Kamera merkezlerinden RANSAC + Umeyama. Artık hata: sınıf 0,0069 birim (~1,5 cm), koridor 0,0076 birim (~1,6 cm); yönelim farkı ~0,1°. Koridor ölçeği sınıfa bağlandı (çarpan 1,039).
3. **Yatay düzeltme:** Sınıf modelinin y=0 düzlemi platforma oturmuş ve 1,45° eğikti. İki model aynı dönüşümle yatay yapıldı, koridor zemini y=0. Denetim (hizalamada kullanılmadı): zemin kotu sınıfta x=-9..6 boyunca −0,07..−0,01 m, koridorun +z kolunda −0,03..+0,01 m.
4. **Kapı K3:** Sınıf çekiminde kapalı, koridor çekiminde açıktı. Kapı +z duvarında, x = −6,91..−5,31 m (1,60 m, koyu kanat rengiyle), üstü 2,12 m. Kutu (x −7,06..−5,16, z 6,16..7,54, y −0,2..2,27) içi koridor modelinden alındı; sınıfta kapı duvarının arkası atıldı, koridorun sınıf içindeki kısmı atıldı. Görsel: `kapi_kontrol.png`, üstten hiza: `hizalama_ust.png`.

Maliyet: L4 ~1 saat (~1,6 birim). Sorunlar: `colmap` için eksik `libboost_graph/regex` kütüphaneleri; 4.2.1'de `--Mapper.image_list_path` adı; kapı duvarının otomatik seçiminin L şeklindeki koridorda yanılması (+z olarak sabitlendi). Unity'de görsel denetim henüz yapılmadı; ölçek sınıfın tahmini 210 cm/birimine bağlı, mezura ile güncellenecek.

Unity çıktıları (Drive): `derslik4_cekim2/runs/unity/derslik4_cekim2_H2_kapi_acik_unity.ply`, `derslik4_cekim2_1440big_H2_kapi_acik_unity.ply`; `derslik4_koridor/runs/unity/koridor_1440_big_H2_kapi_acik_unity.ply`, `koridor_1440_big_kapi_acik_unity.ply`.
