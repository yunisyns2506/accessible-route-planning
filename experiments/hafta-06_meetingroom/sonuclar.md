# Hafta 6 · Tanks & Temples *Meeting room*: hafta 5 hattıyla 3DGS

**Soru:** Aynı hat (LoMa + sequential/döngü + incremental → splatfacto 30k, 1080p, H2 yok), iyi çekilmiş bir videoda ne kadar net sonuç veriyor?

**Defter:** Drive `Hafta 6 Çalışmaları/Hafta6_MeetingRoom.ipynb` (L4, 04.11.2026). Bütün çıktılar `Hafta 6 Çalışmaları/meetingroom/{video, frames_1080, sfm, runs, logs, figs}` altında. Betikler `scripts/hafta06/` klasöründe ve Drive'da `Hafta 6 Çalışmaları/betikler/` altında.

## Veri
- `Meetingroom.mp4`: 3840×2160, 29,97 fps, H.264, 370 sn, 11.098 kare, 4,27 GB. Herkese açık dosyanın indirme kotası dolu olduğu için Drive API ile kopyalandı.
- 1000 pencere × 11,1 kare (0,37 sn). Pencereler 1 sn'den kısa olduğu için **videonun tamamı** kullanıldı (0–370 sn).
- Kamera hareketi Derslik 4'ten hızlı. Hızlı karelerin (≥ 15 px/kare) oranı %17,9, Derslik 4'te %9,5. Seçilen karelerin %13,8'i eşiğin üstünde kaldı (Derslik 4'te %5,3); bu pencerelerde eşik altında kare yoktu.
- Parlaklık video boyunca 40–130 arasında değişiyor. Otomatik pozlama ya da ışık farkı var.

## Süre, bellek, Colab birimi (L4, 1,54 birim/sa)

| Aşama | Meeting room | Derslik 4 (hafta 5) |
| :--- | :--- | :--- |
| Kurulum (COLMAP 4.2.1 + ONNX derleme, CUDA 12.8; 3DGS ortamı; bir kez) | 23,0 dk | — |
| Video analizi (11.098 kare) | 7,5 dk | — |
| Kare seçimi + 1080p çıkarma | 7,5 dk | — |
| LoMa özellik çıkarma | 15,8 dk · VRAM 13,0 GB · RAM 2,7 GB | 15,0 dk · VRAM 12,4 GB · RAM 2,3 GB |
| Sözlük ağacı | 26,9 dk · RAM 1,6 GB | 26,6 dk · RAM 1,6 GB |
| Eşleştirme (sequential + döngü) | 17,0 dk · VRAM 0,7 GB · RAM 2,1 GB | 15,8 dk · VRAM 0,7 GB · RAM 2,1 GB |
| SfM (incremental mapper) | 51,6 dk · RAM 2,6 GB | 44,2 dk · RAM 2,2 GB |
| 3DGS eğitimi (30k, 1080p) | 31,9 dk · VRAM 9,6 GB · RAM 19,2 GB | 29,4 dk · VRAM 3,0 GB · RAM 19,4 GB |
| Değerlendirme + .ply | 1,1 dk | — |
| **SfM + 3DGS toplamı** | **143,3 dk · 3,68 birim** | **131,0 dk · 3,36 birim** |
| **Tüm aşamalar (kurulum dahil)** | **182,3 dk · 4,68 birim** | — |

## SfM ve 3DGS sonuçları

| | Meeting room | Derslik 4 (hafta 5) |
| :--- | ---: | ---: |
| Modele giren kare | 1000 / 1000 (tek model) | 1000 / 1000 |
| Eşleştirilen / doğrulanan çift | 12.804 / 12.280 (%96) | 12.945 / 11.344 (%88) |
| Döngü çifti (10 kareden uzak) | 7.231 | 6.622 |
| Seyrek 3B nokta | 141.595 | 246.479 |
| Ortalama iz uzunluğu (kare) | **13,04** | 5,75 |
| Ortalama yeniden izdüşüm hatası (px) | 1,34 | 1,32 |
| Eğitim / test kare | 900 / 100 | 900 / 100 |
| PSNR (dB) | **26,68** | 25,23 |
| SSIM | 0,894 | 0,907 |
| LPIPS | 0,192 | 0,200 |
| Gaussian sayısı | 434 k | 409 k |

Referans (NerfBaselines 3DGS, Meeting room): PSNR 25,19, SSIM 0,866, LPIPS 0,141. Test kareleri farklı seçildiği için doğrudan karşılaştırılamaz; yalnız fikir verir.

En düşük test kareleri 0750 (20,9 dB), 0910, 0860 (21,4 dB). Test PSNR'ı ile karenin kamera hareketi arasında r = −0,48. 0750'de çizim gerçek kareden koyu, yani kayıp pozlama farkından geliyor.

## Yoldan uzak açılar (`uzak_gorus.py`, `figs/uzak/`)
R, kameraların ortalama merkezine medyan uzaklığın ¼'ü (sahneye göre ölçekli).

- **Meeting room:** Oda ortasından 4 yöne bakış (en yakın kamera 0,24R) temiz ve net. Sağa kaydırma (0,66–1,0R) net. Yukarı kaldırma (1,0R) hafif yumuşuyor; tavana bakan karede (0750) dağılıyor. Tavan az çekilmiş.
- **Derslik 4, aynı ölçüyle:** Sağa kaydırma 0,67R ve 0,97R'de görüntü tamamen dağılıyor. Yukarı kaldırmada (0,98R) zeminde uçuşan parçalar var. Oda ortası (0,47R) okunur, ama öndeki sıralar ve tablalar bulanık.

**Unity gözlemi (04.11.2026):** Unity'de bu model Derslik 4'ten görsel olarak daha kötü: bulanık, splatlar dağınık. Yukarıdaki üretilmiş görünümler (oda ortası, yana kaydırma) bunu göstermiyordu. Olası sebepler: Unity'de bakılan açılar bu görünümlerden daha uzak ya da alçak; ya da Unity aktarımı (`unity_ply.py`, ölçeksiz Meeting room için ayarlanmamış eşikler, kutu dışı kırpma) bozuyor. Henüz incelenmedi; not olarak tutuluyor.

**İlk yorum (Unity gözleminden önce yazıldı, artık geçerli sayılmaz):** Aynı hat, iyi kapsanan bir çekimde yoldan uzak açılarda da net. Derslik 4'teki dağılmanın büyük kısmı hattan değil, çekimden geliyor: tek geçiş, düşük iz uzunluğu (5,8'e karşı 13,0), geniş ve tekrarlı salon. Kalan zayıflık yukarı/tavan açıları ve pozlama farkı.

## Unity
`runs/unity/meetingroom_unity.ply` (92 MiB, 387.587 Gaussian; salon kutusu dışındaki 36 bin parça atıldı). Hafta 5 `unity_ply.py` ile üretildi: zemin y = 0, Y yukarı, X/Z duvarlara paralel, Unity sol el. **Metre ölçeği yok**, koordinatlar COLMAP biriminde (100 cm/birim verildi). Oda yaklaşık 10,5 × 11,8 birim, tavan 2,9 birim.

## Bilinen kurulum notları
- Colab: Ubuntu 24.04, CUDA 13 sürücüsü, Python 3.13. COLMAP, ONNX Runtime CUDA 12 ile uyumlu olsun diye CUDA 12.8 araç takımıyla derlendi. Derleme Drive'da `Hafta 6 Çalışmaları/kurulum/colmap_4.2.1_u2404_cu128_l4.tgz` olarak duruyor; `kurulum.sh` sonraki oturumda bu arşivi açar.
- `colab_gs.py`'nin `ns/` Drive yedeği, üst klasör yoksa hata veriyor. Defterde 6b hücresi bu yedeği tamamlıyor.
- `uzak_gorus.py`: nerfstudio, `applied_transform`'u `dataparser_transforms.json`'daki dönüşüme katar. Bu yüzden `transforms.json` pozlarına T·A⁻¹ uygulanır. Doğrulama: Derslik 4 0250 karesinde render ile gerçek kare arasında 24,1 dB.
