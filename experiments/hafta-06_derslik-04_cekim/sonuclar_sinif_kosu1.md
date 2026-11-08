# Hafta 6 · Derslik 4 tekrar çekim: sınıf videosu, 1. koşu (05.11.2026)

**Defter:** Drive `Hafta 6 Çalışmaları/Hafta6_Derslik4_Sinif.ipynb` (L4). Çıktılar `Hafta 6 Çalışmaları/derslik4/`.

## Veri ve ayarlar

| | Hafta 5 | Bu koşu |
| :--- | ---: | ---: |
| Lens, görüş açısı (yatay) | 0,5×, 95° | 1×, 62° (SfM'in kestirdiği) |
| Video | 4K, 30 fps, 10 dk 19 sn | 4K, 59,94 fps, 20 dk 55 sn |
| Kare sayısı | 1000 | 1500 |
| Hareket eşiği | 15 px/kare | 7,5 px/kare (aynı piksel hızı) |
| Pencere | eşit süre | eşit süre |
| Hat | LoMa + sequential/döngü + incremental, splatfacto 30k, 1080p | aynı |

Kare sayısı 1000 yerine 1500 alındı: ardışık kare kayması 1000 karede medyan %9,4 / p90 %42,6 idi (hafta 5: %2,6 / %6,7).

## Süre, bellek, Colab birimi (L4, 1,54 birim/sa)

| Aşama | Süre | Bellek |
| :--- | ---: | :--- |
| Kurulum (COLMAP kaynaktan derlendi, `libGLEW` eksikti) | 23 dk | — |
| Video analizi (75.215 kare) | 41,4 dk | RAM 0,7 GB |
| Kare çıkarma | 15,2 dk | RAM 0,8 GB |
| LoMa özellik çıkarma | 23,3 dk | VRAM 12,4 GB, RAM 2,6 GB |
| Sözlük ağacı | 34,8 dk | RAM 1,6 GB |
| Eşleştirme | 28,3 dk | VRAM 0,7 GB, RAM 2,1 GB |
| SfM (incremental) | 195,3 dk | RAM 2,0 GB |
| 3DGS, 1. koşu (geçersiz) | 34,3 dk | VRAM 14,1 GB, RAM 24,4 GB |
| 3DGS, 2. koşu | 29,8 dk | VRAM 3,6 GB, RAM 24,4 GB |
| **Toplam oturum** | **~7 sa, ~10,8 birim** | |

## Sonuçlar

| | Hafta 5 | Bu koşu |
| :--- | ---: | ---: |
| Modele giren kare | 1000 / 1000 | 1486 / 1500 |
| Doğrulanan / eşleştirilen çift | 11.344 / 12.945 (%88) | 12.225 / 20.023 (%61) |
| Seyrek 3B nokta | 246.479 | 301.737 |
| Ortalama iz uzunluğu (kare) | 5,75 | 4,63 |
| Yeniden izdüşüm hatası (px) | 1,32 | 1,18 |
| Elenen kamera | 0 | 106 |
| Eğitim / test kare | 900 / 100 | 1244 / 136 |
| PSNR (dB) | 25,23 | **20,18** |
| SSIM | 0,907 | 0,841 |
| LPIPS | 0,200 | 0,365 |
| Gaussian | 409 k | 537 k |

Test PSNR'ı bölümlere göre:

| Kare | Video (dk) | Kayma medyan / p90 | 3B nokta/kare (medyan) | Elenen kamera | PSNR ort. (dB) |
| :--- | :--- | ---: | ---: | ---: | ---: |
| 1–386 | 0–5,4 | %6,6 / %22,2 | 1363 | 0 | 18,97 |
| 387–731 | 5,4–10,2 | %17,1 / %42,2 | 226 | 106 | 16,02 |
| 732–1100 | 10,2–15,3 | %3,5 / %16,0 | 866 | 0 | 21,04 |
| 1101–1500 | 15,3–20,9 | %4,2 / %18,1 | 1292 | 0 | 22,73 |

## Sorunlar

1. **387–731 arasında SfM pozları bozuk.** Bazı kameralar oda dışına düşüyor (normal uzaklık ~3 birim, en uzak 1261 birim). Örnek kareler net; bu karelerde yakından, birbirinin aynı sandalyeler görünüyor ve kareler arası kayma yüksek. Sebep olarak tekrar eden doku + az örtüşme düşünülüyor; ayrı bir deneyle doğrulanmadı.
2. **Kamera süzgecinde açık (1. koşu, PSNR 12,14, geçersiz).** 7 bozuk kamera ikili-üçlü küme hâlinde olduğu için "en yakın 3 kamera" kuralından geçti. Nerfstudio sahneyi bunlara göre ölçekledi (0,0015). `colab_gs.py`'ye merkez uzaklığı kuralı eklendi (medyanın 10 katı).
3. **Düşük PSNR yalnız bozuk bölgede değil.** Bozuk bölge dışındaki bölümler de hafta 5'in altında. Olası sebep, kalan hatalı pozların modelin bütününü bozması; doğrulanmadı.

## Önerilen sonraki adım

Kareleri eşit süre yerine görüntü değişimine göre seçmek (N = 1500, hareket payı 0,75). Hesap: 5,4–10,2. dk 345 yerine 542 kare, kayma %17/%43 yerine %11/%23, kayması %50'yi aşan çift 24 yerine 0. Bedeli SfM + 3DGS'in baştan koşması.
