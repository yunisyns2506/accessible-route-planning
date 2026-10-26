# Dokusuz yüzey iyileştirme koşuları (LoMa incremental, 1080p, 30k iterasyon)

Hepsi aynı 1000 kare, aynı COLMAP pozları ve aynı 100 test karesiyle (her 10. kare) değerlendirildi.
"Renk düzeltmeli": her test karesinde render ile gerçek kare arasına 3x3 + sabit renk dönüşümü uydurulduktan
sonraki metrik (pozlama farkını ayırır, geometri/keskinlik farkını ayırmaz). Betik: `renk_degerlendir.py`.

| Koşu | Ayar | PSNR ham (dB) | PSNR düzeltmeli (dB) | SSIM ham | SSIM düzeltmeli | LPIPS ham | LPIPS düzeltmeli | Gaussian | Eğitim (dk) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Taban | splatfacto | 25,23 | 25,68 | 0,902 | 0,903 | 0,200 | 0,198 | 409 k | 29 |
| H | + pozlama düzeltme (bilateral grid) + kamera pozu ince ayarı | 20,24 | 21,48 | 0,817 | 0,825 | 0,236 | 0,226 | 373 k | 79 |
| H2 | + yalnız pozlama düzeltme | 23,16 | 25,33 | 0,893 | 0,901 | 0,204 | **0,191** | — | ~80 |
| DN | DN-Splatter, Depth Anything V2 metrik derinlik (Pearson, λ 0,2) | 23,19 | 23,60 | 0,872 | 0,872 | 0,250 | 0,246 | ~460 k | 228 |

## 1440p splatfacto-big
| Koşu | PSNR ham (dB) | PSNR düzeltmeli (dB) | SSIM düz | LPIPS düz | Gaussian | Eğitim (dk) |
|---|---:|---:|---:|---:|---:|---:|
| Taban 1440p big | 25,63 | — | 0,912 (ham) | 0,210 (ham) | 1,25 M | 79 |
| H2 1440p big (pozlama düzeltme) | 21,43 | 25,29 | 0,903 | 0,210 | 1,16 M | 131 |

1440p'de pozlama düzeltmesinin sayısal getirisi yok (düzeltmeli PSNR tabanın ham değerinin 0,3 dB altında,
LPIPS aynı). Seçim Unity'de duvar görünümüne göre yapılmalı. Unity ply'leri Drive `hafta5_derslik4/unity/`.

## Görsel karşılaştırma
`karsilastirma_taban_H_H2_DN.jpg` (test kareleri 0250, 0500 ve duvar yakın kırpımı): tabanda beyaz duvar ve
perde çevresinde gri lekeler/bulutlar var; H ve H2'de bunlar neredeyse tamamen kayboluyor, duvar düz ve temiz.
H'de görüntü test karesine göre kaymış (poz ince ayarı), H2 hizalı. DN'de duvar dokulu/lekeli, portrede belirgin
bozulma var. Görsel olarak en iyi: **H2**.

## Gözlemler
- **H:** duvarlardaki gri bulutlar görsel olarak büyük ölçüde gitti, ama kamera pozu ince ayarı eğitim pozlarını
  kaydırdığı için test kareleriyle hizalanmıyor; PSNR'daki büyük düşüş bu kaymadan. Test kareleri için de poz
  ince ayarı yapılmadan bu ayar sayısal karşılaştırmada kullanılamaz.
- **H2:** kayma yok. Ham PSNR'ın düşük olması beklenen: bilateral grid pozlamayı eğitim karelerine ayrı ayrı
  öğrenir, test karesinde nötr renk verir. Renk düzeltmeli PSNR tabanla aynı düzeyde (−0,35 dB), LPIPS daha iyi
  (0,198 → 0,191; algısal olarak gerçek kareye daha yakın). Yani pozlama düzeltmesi geometriyi bozmadan renk
  tutarlılığını artırıyor; duvar bulanıklığına etkisi Unity'de görsel karşılaştırmayla değerlendirilmeli.
- **DN:** coolermap ayrıştırıcısı derinlikten normal üretimini COLMAP verisinde desteklemediği için yalnız
  derinlik kaybıyla koşuldu. Monoküler derinliğin COLMAP noktalarına göre medyan göreli sapması %9.
  Sonuç: görüntü metriklerinde tabandan belirgin kötü (renk düzeltmeli PSNR −2,1 dB, LPIPS 0,198 → 0,246).
  Olası nedenler: monoküler derinlikteki %9'luk tutarsızlığın (kareler arası ölçek farkı) renkle çelişmesi,
  derinlik ağırlığının (0,2) bu veri için yüksek kalması, normal kaybının kullanılamaması. Makalelerde
  DN-Splatter'ın PSNR'ı tabana yakın tutup geometriyi iyileştirdiği bildiriliyor; burada geometri (duvar
  düzlüğü, uçuşan parçalar) Unity'de ayrıca bakılarak değerlendirilmeli. Eğitim 3,8 saat sürdü (taban 0,5 saat).
  .ply: Drive `hafta5_derslik4/runs/loma_DN/export/splat.ply` (113 MB).

## Kurulum notları (DN)
- dn-splatter nerfstudio 1.1.3 / gsplat 1.0.0 ister → ayrı ortam (`/content/dn`, Python 3.10).
- PyMCubes 0.1.2 numpy 2 ile derlenmiyor → `--override` ile PyMCubes>=0.1.4 ve numpy<2.
- uv'de PyTorch dizini öncelikli olduğu için `--index-strategy unsafe-best-match` gerekli.
- dn-splatter'ın SSIM kaybı 8 bit kare önbelleğini kabul etmiyor → önce float32 önbellek denendi; 25 GB kare +
  derinlikler 52 GB RAM'i doldurdu, eğitim adım başına 10 sn'ye düştü (tahmini 3 gün). Çözüm: 8 bit önbellek ve
  nerfstudio datamanager'da kare GPU'ya alınırken float'a çevrilmesi (yama, `dn_kuyruk.sh`). dn-splatter kendi
  datamanager'ında aynı fonksiyonları yeniden tanımladığı için yama oraya da uygulandı (6. deneme). Eğitim
  23:56 TR'de başladı; RAM ~25 GB kullanımda.

## SIFT (exhaustive + incremental)
Hafta_5 çalışma zamanı 26.10 ~23:10–23:40 TR arasında koptu; son Drive yedeği 23:10 TR (1,18 GB veritabanı).
Kalan eşleştirme, SfM ve 1080p 3DGS, DN'den sonra aynı makinede yedekten sürdürüldü (`sift_devam.sh`).
- Eşleştirme: 499.500 / 499.500 çift, 26.10 05:40 TR (bu makinede 111 dk; toplam ~7 saat).
- SfM (incremental): 1 model, **981 / 1000 kare** kayıtlı (LoMa incremental: 1000 / 1000), 06:43 TR.
- 1080p 3DGS (splatfacto, 30k, LoMa ile aynı ayar), 07:14 TR:

| SfM | Kayıtlı kare | Test karesi | PSNR (dB) | SSIM | LPIPS | Gaussian | Eğitim (dk) |
|---|---:|---:|---:|---:|---:|---:|---:|
| LoMa + sequential + döngü + incremental | 1000 / 1000 | 100 | **25,23** | **0,907** | **0,200** | 409 k | 29 |
| SIFT + exhaustive + incremental | 981 / 1000 | 99 | 24,86 | 0,902 | 0,207 | 404 k | 29 |

SIFT exhaustive, ~7 saatlik eşleştirmeye (LoMa sequential + döngü: dakikalar) rağmen 19 kareyi kaydedemedi ve
3DGS'te LoMa'nın 0,37 dB gerisinde kaldı. Bina ölçeği için LoMa + sequential + döngü tercihi doğrulandı.
(Not: SIFT'te 1 test karesi kayıtsız olduğu için ortalama 99 kare üzerinden.)
- Test bölünmesi: kareler (k − 10) mod 1000 olarak yeniden adlandırıldı; eğitimden önce test listesinin
  tabanla aynı olduğu doğrulandı.
