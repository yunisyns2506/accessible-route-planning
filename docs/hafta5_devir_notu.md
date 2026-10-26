# Hafta 5 devir notu: Rektörlük derslik 4 (3DGS + ölçek + Unity)

Bu not, kalan işleri devralacak kişi içindir. Ne yapıldı, sonuçlar nerede, ne kaldı.

## 1. Veri ve akış (özet)
- **Girdi:** 4K yatay video (`Derslik_4.MOV`, Drive `3dgs videoları/Merkezi Derslik_Derslik4/IMG_0299.MOV`), 18.560 kare.
- **Kare seçimi:** 1000 kare; 0,6 sn pencerede hızlı dönüş dışı en keskin kare (`scripts/hafta05/kare_secimi.py`,
  liste `experiments/hafta-05_derslik-04/video_analiz/secilen_kareler_1000.csv`).
- **Test kareleri:** her 10. kare (0010, 0020, …, 1000; 100 kare). SfM'e girer (poz hesabı için), 3DGS eğitimine girmez;
  metrikler yalnız bu karelerde ölçülür.
- **SfM:** COLMAP 4.2.1 (Colab L4, kaynaktan derlendi). En iyi: LoMa özellikleri + sequential eşleştirme + döngü
  tespiti + incremental mapper (`scripts/hafta05/colab_sfm.py`).
- **3DGS:** nerfstudio 1.1.5 splatfacto / splatfacto-big, gsplat 1.4, 30.000 iterasyon (`scripts/hafta05/colab_gs.py`).
- **Ölçek ve hizalama:** 3 gerçek ölçüyle ölçek 207,2 cm/model birimi; zemin y = 0, Y yukarı, metre
  (`scripts/hafta05/olcek_ucgenle.py`, `scripts/hafta05/unity_ply.py`).
- **Unity:** aras-p UnityGaussianSplatting; çarpışma kutuları + FPS kontrol betikleri.

## 2. Sonuçlar (sayılar)

### SfM + 3DGS (1080p, 100 test karesi)
| SfM | Kayıtlı kare | PSNR (dB) | SSIM | LPIPS |
|---|---:|---:|---:|---:|
| LoMa + sequential + döngü + incremental | 1000 / 1000 | 25,23 | 0,907 | 0,200 |
| LoMa + sequential + döngü + hierarchical (leaf 250) | 999 / 1000 | 24,35 | 0,893 | 0,215 |
| SIFT + exhaustive + incremental | 981 / 1000 | 24,86 | 0,902 | 0,207 |

### Çözünürlük (LoMa incremental)
| Model | PSNR (dB) | SSIM | LPIPS | Gaussian |
|---|---:|---:|---:|---:|
| 1080p splatfacto | 25,23 | 0,907 | 0,200 | 409 k |
| 1440p splatfacto-big | 25,63 | 0,912 | 0,210 | 1,25 M |
| 4K splatfacto-big | 25,38 | 0,930 | 0,242 | 1,30 M |

### Dokusuz (beyaz) duvar iyileştirmesi (1080p; "düz" = renk düzeltmeli metrik)
| Koşu | PSNR ham / düz (dB) | LPIPS düz | Görsel |
|---|---:|---:|---|
| Taban | 25,23 / 25,68 | 0,198 | duvarda gri lekeler |
| H: pozlama düzeltme + kamera pozu ince ayarı | 20,24 / 21,48 | 0,226 | temiz ama kaymış |
| **H2: yalnız pozlama düzeltme (bilateral grid)** | 23,16 / 25,33 | **0,191** | **temiz, hizalı (önerilen)** |
| DN-Splatter (monoküler derinlik) | 23,19 / 23,60 | 0,246 | lekeli, bozuk |
| H2 1440p splatfacto-big | 21,43 / 25,29 | 0,210 | 1,16 M Gaussian; duvar temizliği 1080p H2 ile aynı yönde olmalı (Unity'de bakılacak) |

Not: 1440p'de H2'nin renk düzeltmeli PSNR'ı (25,29 dB) ham 1440p tabanın (25,63 dB) biraz altında, LPIPS
aynı (0,210). Yani 1440p'de pozlama düzeltmesinin sayısal getirisi yok; tercih Unity'deki görsel karşılaştırmaya
(beyaz duvar lekeleri) göre yapılmalı. Ham PSNR'ın düşük çıkması beklenen (pozlama her eğitim karesine ayrı öğreniliyor).

Ayrıntı ve görsel: `experiments/hafta-05_derslik-04/iyilestirme/sonuclar.md`, `…/karsilastirma_taban_H_H2_DN.jpg`.
Literatür taraması: `reports/Dokusuz yüzeylerde 3DGS iyileştirme.md`.

### Ölçek ve doğrulama
Kalibrasyon (en küçük kareler, 3 ölçü): **207,2 cm/birim**. M1 masa 120 → 125 cm (+%4), K1 kürsü 70 → 82 cm (+%17),
D1 kapı 155 → 144 cm (−%7). Doğrulama: B1 platform 43,5 → 40,6 cm (−2,9 cm). Bağımsız denetim: masa yüksekliği
0,74 m, kapı 2,05–2,09 m, kamera yüksekliği 1,28 m (gerçekçi). Ayrıntı: `experiments/hafta-05_derslik-04/olcum/kalibrasyon/olcek_sonuc.md`.

### Analizler
- Hatalı kamera bölgeleri: `experiments/hafta-05_derslik-04/analiz/adim1_kamera/` (+ `_hier`).
- Duvar kayması (zemin eğimi, tavan ızgarası): `…/analiz/adim2_*`.
- Eksik geometri: `…/analiz/adim3_eksik_*`.

## 3. Unity dosyaları (Drive: `hafta5_derslik4/unity/`)
| Dosya | Model |
|---|---|
| `derslik4_1440_big_H2_unity.ply` | 1440p big + pozlama düzeltme (duvarlar için ilk bakılacak) |
| `derslik4_H2_unity.ply` | 1080p + pozlama düzeltme |
| `derslik4_1440big_unity.ply` | 1440p big taban |
| `derslik4_H_unity.ply` | 1080p H (karşılaştırma için) |
| `unity_betikler.zip` | `DerslikCarpisma.cs` (çarpışma kutuları), `FPSKontrol.cs` (WASD/fare/zıplama/uçma) |
| `UNITY_MAC.md` | kurulum ve içe aktarma adımları |

Tüm ply'ler metre, Y yukarı, zemin y = 0; GameObject dönüşümü sıfır bırakılır. Yazı aynalı görünürse Scale Z = −1.

## 4. Kalan işler
| İş | Durum / ne gerekiyor |
|---|---|
| Sistem mimarisi (girdi → çıktı diyagramı) | Yapılmadı. Bölüm 1'deki akış diyagrama dökülecek. |
| Test karelerinin SfM ve 3DGS'te kullanımı | Yapılmadı (metin). Bölüm 1'deki "Test kareleri" maddesi genişletilecek. |
| Eğitime giremeyen kare sayıları | Veri hazır (tablo Bölüm 2): LoMa 0, hierarchical 1, SIFT 19 kare; 3DGS'te kopuk kamera 0; 900 eğitim / 100 test. Yazılacak. |
| Çalıştırılabilir COLMAP yapılandırması | `colab_sfm.py` içindeki ayarlar (LoMa, sequential + döngü: vocab tree 8192 kelime, period 10, 50 görüntü) tek yapılandırma dosyasına çıkarılacak. |
| Gerçek ölçülerle doğrulama | B1 yapıldı. D2 (kapı kanadı 72,5 cm) ve S2 (sıra tablası 30 cm) köşeleri işaretlenip `olcek_ucgenle.py` ile hesaplanacak. Hoca 5 doğrulama istemişti, 3 ölçü var: sınırlama olarak yazılmalı. |
| Kapı genişliği güvenilirliği | Ölçüm var (modelde dış kasa 144 cm, ölçülen 155 cm "kasa içi", kişi emin değil). Tanım belirsizliği + ölçek belirsizliği (±%7) ile bölüm yazılacak. |
| Duvar kayması | Zemin ve tavan yapıldı. Duvarlar seyrek modelde güvenilmez; dense (COLMAP MVS) ya da sınırlama olarak yazılacak. |
| VR testi | PC'ye bağlı bir VR gözlükle yapılmalı; Mac'te yapılamaz. 1,25 M Gaussian, gözlüğün kendi işlemcisiyle (bağımsız) çalıştırmak için ağır; gerekirse daha düşük kalite ayarı ya da daha az Gaussian'lı model. |
| Hafta 5 raporu | Yukarıdakilerin hepsi. |

## 5. Kod ve veri nerede
- **GitHub:** `yunisyns2506/accessible-route-planning`, dal `test/3dgs-pilot-runs`. Betikler `scripts/hafta05/`,
  sonuçlar ve analizler `experiments/hafta-05_derslik-04/`, bu not `docs/`.
- **Drive (`hafta5_derslik4/`):** büyük dosyalar Git'te değil, burada. `sfm/` (COLMAP modelleri), `runs/` (eğitim
  çıktıları, orijinal .ply'ler, checkpoint'ler), `unity/` (Unity'ye hazır .ply'ler), `betikler/`, `kurulum/`.

## 6. Colab ipuçları
- Betikler Drive `hafta5_derslik4/betikler/`; COLMAP derlemesi `hafta5_derslik4/kurulum/colmap_4.2.1_l4.tgz`.
- Arka plan işi `subprocess.Popen(..., start_new_session=True)` ile, hücrede bekleme döngüsü olmalı (yoksa Colab boşta sayıp kapatır).
- nerfstudio'da `pin_memory` RAM'i ikiye katlıyor; `full_images_datamanager.py`'de kapatıldı.
- Kamera pozu ince ayarı (`camera-optimizer SO3xR3`) test metriğini bozuyor; kullanmayın.
