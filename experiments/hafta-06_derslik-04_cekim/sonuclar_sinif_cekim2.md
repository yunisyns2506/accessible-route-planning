# Hafta 6 · Derslik 4 tekrar çekim: sınıf videosu, 2. çekim (06.11.2026)

**Defter:** Drive `Hafta 6 Çalışmaları/Hafta6_Derslik4_Sinif.ipynb` (L4). Çıktılar `Hafta 6 Çalışmaları/derslik4_cekim2/`. Hat betiği `betikler/hat_cekim2.py`.

## Veri ve ayarlar

| | Hafta 5 | 05.11 çekimi | Bu çekim |
| :--- | ---: | ---: | ---: |
| Lens, odak (COLMAP) | 0,5×, 874 px | 1×, 1597 px | 0,5× (13mm), 874 px |
| Video | 4K, 30 fps, 10 dk 19 sn | 4K, 59,94 fps, 20 dk 55 sn | 4K, 30 fps, 19 dk 53 sn |
| Kare sayısı, aralık | 1000, 0,62 sn | 1500, 0,84 sn | 1500, 0,80 sn |
| Hareket eşiği | 15 px/kare | 7,5 px/kare | 15 px/kare |
| Rota | hafta 5 yolu | sıra aralarında 90° yana | son rota (düz + ters yön + 45° çapraz) |
| Hat | LoMa + sequential/döngü + incremental, splatfacto 30k, 1080p | aynı | aynı |

**İki parça:** Çekim iki videoya bölündü (17 dk 15 sn + 2 dk 42 sn). Birleşme noktasından önceki ve sonraki 12 sn'lik kareler incelendi; iki parça aynı noktada, görüntü sakin. Part 1'in sonundan ve part 2'nin başından 2'şer sn kırpıldı, yeniden kodlama yapılmadı. SfM'de birleşme noktasında poz sıçraması yok.

## Süre, bellek, Colab birimi (L4, 1,54 birim/sa)

| Aşama | Süre | Bellek |
| :--- | ---: | :--- |
| Kurulum (COLMAP yine kaynaktan derlendi) | 28 dk | — |
| Yükleme beklemesi | ~30 dk | — |
| Kopyalama, birleştirme, inceleme | ~9 dk | — |
| Video analizi (35.799 kare) | 16,0 dk | — |
| Kare çıkarma | 8,3 dk | — |
| LoMa özellik çıkarma | 23,2 dk | VRAM 12,4 GB, RAM 2,3 GB |
| Sözlük ağacı | 26,6 dk | RAM 1,6 GB |
| Eşleştirme | 24,0 dk | VRAM 0,7 GB, RAM 2,2 GB |
| SfM (incremental) | 203,7 dk | RAM ~2,5 GB |
| 3DGS eğitimi | 30,3 dk | VRAM 3,7 GB, RAM 25,8 GB |
| **Toplam oturum** | **~7 sa, ~10,8 birim** | |

## Sonuçlar

| | Hafta 5 | 05.11 çekimi | Bu çekim |
| :--- | ---: | ---: | ---: |
| Modele giren kare | 1000 / 1000 | 1486 / 1500 | 1500 / 1500 |
| Doğrulanan / eşleştirilen çift | 11.344 / 12.945 (%88) | 12.225 / 20.023 (%61) | 16.678 / 20.029 (%83) |
| Seyrek 3B nokta | 246.479 | 301.737 | 351.709 |
| Ortalama iz uzunluğu (kare) | 5,75 | 4,63 | 5,35 |
| Yeniden izdüşüm hatası (px) | 1,32 | 1,18 | 1,30 |
| Elenen kamera | 0 | 106 | 0 |
| Eğitim / test kare | 900 / 100 | 1244 / 136 | 1350 / 150 |
| PSNR (dB) | 25,23 | 20,18 | **25,53** |
| SSIM | 0,907 | 0,841 | **0,881** |
| LPIPS (düşük iyi) | 0,200 | 0,365 | **0,303** |
| Gaussian | 409 k | 537 k | 414 k |

Test kareleri aynı değil; karşılaştırma yaklaşıktır.

Test karelerinde bölümlere göre:

| Kare | Video (dk) | PSNR (dB) | SSIM | LPIPS |
| :--- | ---: | ---: | ---: | ---: |
| 1–150 | 0,0 | 24,25 | 0,897 | 0,303 |
| 151–300 | 2,0 | 25,27 | 0,882 | 0,265 |
| 301–450 | 4,0 | 24,83 | 0,872 | 0,319 |
| 451–600 | 6,0 | 24,68 | 0,870 | 0,293 |
| 601–750 | 8,0 | 25,27 | 0,897 | 0,273 |
| 751–900 | 9,9 | 24,63 | 0,866 | 0,309 |
| 901–1050 | 11,9 | 24,54 | 0,864 | 0,336 |
| 1051–1200 | 13,9 | 27,55 | 0,880 | 0,366 |
| 1201–1350 | 15,9 | 27,83 | 0,905 | 0,269 |
| 1351–1500 | 17,9 | 26,42 | 0,875 | 0,297 |

## Yorum

- **05.11'deki bozulma bu çekimde yok.** Sıra araları dahil her bölümde kare başına 1168–1478 3B nokta var (05.11 bozuk bölüm: 226). 45° çapraz geçiş SfM'i bozmadı.
- **Hafta 5'e göre:** PSNR 0,30 dB yüksek; SSIM ve LPIPS daha kötü. Yani genel renk ve konum uyumu aynı düzeyde, ince ayrıntı (yapısal benzerlik, algısal fark) daha zayıf.
- **Olası sebep (doğrulanmadı):** Bu çekim çok daha fazla bakış açısı içeriyor (alçak, çapraz, tavan, zemin), ama Gaussian sayısı aynı düzeyde (414 k) ve iterasyon aynı (30k). Aynı bütçe daha geniş görüşe paylaşılıyor olabilir.
- **Hafta 5 Unity modeli bunun dengi değil:** Hafta 5'te Unity'ye verilen `derslik4_1440big_unity.ply` 1440p ve splatfacto-big ile 1,05 M Gaussian'dı. Bu çekimin Unity dosyası 1080p ve 388 k Gaussian; Unity'de doğrudan karşılaştırmada daha az keskin görünebilir.

## H2: pozlama düzeltmeli eğitim (bilateral grid)

Unity'de beyaz yüzeylerde sorun görülünce aynı pozlar ve karelerle yalnız `--pipeline.model.use-bilateral-grid True` eklenerek yeniden eğitildi (1080p, 30k). SfM tekrarlanmadı.

| | Taban | H2 |
| :--- | ---: | ---: |
| Ham PSNR (dB) | 25,53 | 24,09 |
| Ham SSIM | 0,881 | 0,877 |
| Ham LPIPS | 0,303 | 0,298 |
| Renk düzeltmeli PSNR (dB) | 26,10 | 25,84 |
| Renk düzeltmeli SSIM | 0,882 | 0,882 |
| Renk düzeltmeli LPIPS | 0,301 | 0,293 |
| Gaussian | 414 k | 393 k |
| Unity dosyası (süzgeç sonrası) | 387.741, 96 MB | 367.135, 91 MB |
| Eğitim süresi | 30,3 dk | 103,2 dk |
| En yüksek VRAM / RAM | 3,7 / 25,8 GB | 4,4 / 49,8 GB |
| Oturum | — | ~2 sa, ~3,1 birim |

- **Ölçümler neredeyse aynı.** Ham PSNR'daki düşüş beklenen bir şey: model her kareye ayrı pozlama öğreniyor, test karesinde bu düzeltme yok. Renk düzeltmeli ölçümde H2 PSNR'da 0,26 dB geride, LPIPS'te 0,008 önde.
- **Beyaz duvarlarda görsel fark belirgin.** Duvarı en çok görünen 4 test karesinin panosunda (`logs/h2_pano_gercek_taban_h2.jpg`, gerçek / taban / H2) tabandaki leke ve dalgalanma H2'de büyük ölçüde kayboluyor. Bu ölçümlerde yeterince görünmüyor; karar Unity görünümüne göre verilmeli.
- **Bellek:** 49,8 GB RAM, L4'ün 52 GB sınırına yakın. Daha fazla kare veya 1440p ile RAM yetmeyebilir.
- Süre 3,4 katına çıktı. Hafta 5'te de yaklaşık bu oran vardı (29 → ~80 dk).

## Kaynak karelerde bulanıklık (hafta 5 ile)

H2 de Unity'de hafta 5'ten kötü görününce kaynak karelerin bulanık olup olmadığı ölçüldü. Her iki çekimin tüm 1080p eğitim kareleri (aynı çıkarma yöntemi: lanczos, `-q:v 2`). Betik `scripts/hafta06/bulaniklik.py`, örnekler `bulaniklik_karsilastirma.jpg`.

| Ölçüt (medyan) | Hafta 5 | Bu çekim | İyi yön |
| :--- | ---: | ---: | :--- |
| Laplace varyansı | 117 | 160 | yüksek |
| Bulanıklık etkisi (0–1) | 0,416 | 0,347 | düşük |
| Kenar gücü, 99. yüzdelik | 326 | 349 | yüksek |
| Sandalye kenarı, 95. yüzdelik | 252 | 308 | yüksek |
| En bulanık %10'un eşiği (bulanıklık etkisi) | 0,534 | 0,375 | düşük |
| En bulanık %10'un eşiği (Laplace) | 37 | 69 | yüksek |

- **Bu çekimin kaynak kareleri daha keskin.** Dört ölçütün dördünde de önde; en kötü kareler arasındaki fark daha büyük. Hafta 5'in en bulanık kareleri görsel olarak da hareket bulanıklığı içeriyor, bu çekiminkiler net. Yani modelin daha az keskin görünmesinin sebebi bulanık kaynak değil.
- **Keskin kare, kötü LPIPS:** Bu çekimin test karelerinde bulanıklık etkisi ile LPIPS arasında r = −0,78. En keskin üçte birin LPIPS'i 0,354, en bulanık üçte birin 0,267. Sebep olarak model ayrıntıyı karşılayamıyor olabilir. Ama ayrıntılı sahne hem keskin ölçülür hem zor öğrenilir, bu ilişki tek başına kanıt değil. Hafta 5 kaydında kare başına değer olmadığı için aynı ilişki orada ölçülemedi.
- **Sınır:** Ölçütler sahne içeriğinden de etkilenir, iki rota aynı görüntüleri içermiyor. Yine de fark tüm ölçütlerde aynı yönde.
- **Maliyet:** L4'te ~13 dk, ~0,3 birim; Drive izni başarısız olan önceki deneme ~10 dk, ~0,3 birim.

## Sorunlar

1. **Video adı:** Dosyalar "çekim2" olarak yüklendi, hat "cekim2" arıyordu; Drive kontrolünde görüldü, eşleştirme düzeltildi. ~27 dk gecikme.
2. **Hazır COLMAP paketi açılmadı:** Kaynaktan derlendi (27 dk), paket yeniden yedeklendi. Sebep incelenmedi.
3. **Şüpheli pozlar:** 1000 ve 481–483 numaralı karelerde yörüngede 2,3–7 birimlik sıçrama (medyan adım 0,2). Kare 1000'in test PSNR'ı 12,9 dB. Süzgeç yakalamadı (kameralar oda içinde kalıyor). Test karelerinden 1470 (13,3 dB) ve 50 (13,7 dB) de çok düşük; sebepleri incelenmedi.
4. **Tahmini ölçek hatası:** Kamera yüksekliği varsayımı (1,3 m) 263,5 cm/birim verdi ve tavan 5,4 m çıktı. Hafta 5 salon boyutlarına (21 × 16 m, tavan 4,1 m) göre 210 cm/birim ile yeniden üretildi: 20,9 × 15,2 m, tavan 4,27 m. Mezura ölçüleriyle düzeltilecek.
5. **1440p big + H2 eğitimi tamamlanamadı (07.11):** İlk deneme 23:45 UTC'de önbellekleme sırasında bellek bekçisine takıldı (1594 MiB kaldı); görüntü ve maske `pin_memory` kapatılıp `MALLOC_ARENA_MAX=2` eklenince önbellek aşıldı. İkinci deneme 23:51 UTC'de başladı, 01:00 UTC'de %46'daydı (13.850/30.000 adım, 306 ms/adım, 26 GB boş RAM). 02:29 UTC kontrolünde sanal makine yeniydi (açılış 02:25:56 UTC), `/content/work` yoktu. Sanal makinenin kapanma anı ve sebebi bilinmiyor; 01:00–02:26 UTC arasında. Oturum 23:24 UTC'de açılmıştı, yeni makine ~3 sa sonra geldi; bu yalnız bir ipucu, süre sınırı doğrulanmadı.
   - **Kayıp:** Metrik, ply ve kontrol noktası yok. Betik koşuyu Drive'a yalnız sonda kopyalıyordu, günlükler de Drive'a eğitim başlangıcından sonra yansımadı. Harcanan yaklaşık 2,5–4,7 birim (+ yeni makine ~0,1).
   - **Tekrar için gerekli:** Kontrol noktalarını belirli aralıkla Drive'a kopyalamak, kesilince oradan sürdürmek, günlükleri düzenli yazmak. Kapasite mi poz mu sorusu bu nedenle hâlâ açık.
   - **07.11 tekrarı (`hat_sinif_1440.py` + `egit_surdur.py`, kontrol noktası 10 dk'da bir Drive'a):** kesintisiz bitti. Eğitim 153 dk, VRAM 11,3 GB, RAM 28,9 GB, 1,11 M Gaussian. Ham 22,22 / 0,870 / 0,340; renk düzeltmeli **25,63 / 0,880 / 0,321** (aynı ölçümde 1080p H2: 25,84 / 0,882 / 0,293). Panoda (`sinif_1440_karsilastirma.jpg`) iki model neredeyse aynı: ön plandaki sandalyeler ve tel sepetler ikisinde de bulanık. Sonuç: çözünürlük ve kapasite artışı netlik getirmedi; sınır girdide (hareket bulanıklığı, 0,5× lens, video sıkıştırması) ya da pozlarda. Not: 1440p ölçümü 1440p karelerde yapıldığı için LPIPS doğrudan karşılaştırılamaz. Unity: `runs/unity/derslik4_cekim2_1440big_H2_unity.ply` (226 MB, 210 cm/birim tahmini).

## Çıktılar

- Unity: `derslik4_cekim2/runs/unity/derslik4_cekim2_unity.ply` (96 MB, 387.741 Gaussian, 210 cm/birim, tahmini)
- Unity, H2: `derslik4_cekim2/runs/unity/derslik4_cekim2_H2_unity.ply` (91 MB, 367.135 Gaussian, 210 cm/birim, tahmini)
- Eğitilmiş model ve splat: `derslik4_cekim2/runs/loma_sequential_loop_incremental/`, H2: `..._H2/`
- SfM ve veritabanı: `derslik4_cekim2/sfm/loma/sequential_loop/`
