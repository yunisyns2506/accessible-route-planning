# Hafta 3 — 3DGS Üretim Hattının Kurulması ve Yöntem Karşılaştırması

**Proje:** Engelli Bireyler İçin Akıllı Erişilebilir Rota Planlama
**Aşama:** A1 — Mekân modelleme
**Hazırlayanlar:** Sabri Duruk, Yunis Teymurlu · **Danışman:** Öğr. Gör. Koray AKİ

---

## 1. Amaç ve Yapılan İş

Projenin hedefi, bir binanın iç mekânını fotoğraf/video ile modelleyip tekerlekli
sandalye kullanan bireyler için erişilebilir rota hesaplamaktır. Bu hafta o hattın
ilk halkası olan **3D Gaussian Splatting (3DGS) üretim hattı** kuruldu ve hangi
yöntemin bina ölçeğinde kullanılabileceğini öngörmek için karşılaştırıldı.

Aynı derslik videosu **iki ayrı hatta** işlendi:

| Hat | Ortam | Kapsam | Bölüm |
| :--- | :--- | :--- | :--- |
| **A — Yerel** | RTX 2060 6 GB iş istasyonu | 3 SfM + 9 eğitim koşusu, tek değişkenli kontrollü karşılaştırma | 5 |
| **B — Bulut ve hazır hizmet** | Google Colab (NVIDIA L4) ve Luma AI | 2 eğitim koşusu + 1 hazır hizmet, Unity aktarımı | 6 |

Bu ayrım raporun tamamında korunmuştur: A hattı kontrollü bir ablasyon çalışması,
B hattı ise ortam ve hizmet karşılaştırmasıdır. İki hattın sayısal sonuçları
**birbiriyle karşılaştırılamaz** — kare seti, çözünürlük, test bölmesi ve eşleştirme
stratejisi farklıdır. Ortak bulgular 7. bölümde, her maddenin hangi hattan geldiği
belirtilerek toplanmıştır.

Öncesinde bir ekip üyesinin odasında 3 pilot koşu yapılarak hattın uçtan uca
çalıştığı doğrulanmıştır (Bölüm 4.3).

Haftanın çıktısı, A hattında önerilen yapılandırmayla üretilen derslik modelidir:

![Şekil 1 — Üretilen modelin genel görünümü (A hattı, önerilen yapılandırma, 30.000 iterasyon). Tavan aydınlatması, projeksiyon, tahtalar, kapı, pencere ve sıralar arasındaki geçiş koridoru ayırt edilebilmektedir.](../figures/sekil5_model_genel.jpg)

Semantik eleman tespiti, çizge üretimi ve rota hesabı bu haftanın kapsamı
dışındadır.

---

## 2. Yöntem ve Araçlar

```text
Kare çıkarma   →   COLMAP (SfM)        →   Splatfacto (3DGS)   →   PLY
FFmpeg             kamera pozları +        gsplat CUDA             SuperSplat /
                   seyrek nokta bulutu     rasterizasyonu          Unity
```

**COLMAP**, fotoğraflardan kamera konumlarını geri hesaplar: SIFT öznitelikleri
çıkarılır, görüntü çiftleri eşleştirilir, RANSAC aykırı eşleşmeleri ayıklar,
üçgenleme ile 3B noktalar üretilir ve bundle adjustment kamera ile nokta
parametrelerini birlikte iyileştirir:

&nbsp;&nbsp;&nbsp;&nbsp;min Σ ρ( ‖ u(i,j) − π(K(i), R(i), t(i), X(j)) ‖² )

**Splatfacto**, sahneyi konum μ, kovaryans Σ = R S Sᵀ Rᵀ, opaklık α ve bakışa
bağlı renk taşıyan anizotropik 3B Gauss kümesiyle temsil eder. Piksel rengi alfa
bileştirme ile üretilir:

&nbsp;&nbsp;&nbsp;&nbsp;C = Σᵢ T(i)·α(i)·c(i),&nbsp;&nbsp; T(i) = Π (1 − α(j)), j < i

Eğitim SfM noktalarından başlatılır; kayıp L = (1 − λ)·L1 + λ·(1 − SSIM),
λ = 0,2. Yetersiz açıklanan bölgelerde Gaussian bölünür, gereksizler budanır.

| Araç | Sürüm / ortam | İşlev |
| :--- | :--- | :--- |
| COLMAP | 3.9.1 CUDA (yerel) · CPU (bulut) | Kamera pozları ve seyrek nokta bulutu |
| Nerfstudio / Splatfacto | 1.0.3 | 3DGS eğitimi, dışa aktarım, `ns-eval` |
| gsplat | 0.1.4 | Gaussian rasterizasyon CUDA çekirdeği |
| tiny-cuda-nn | kaynak (SM 75) | NeRF karşılaştırması için hash kodlaması |
| FFmpeg · OpenCV | 6.1+ · 4.8+ | Kare çıkarma · netlik ölçümü |
| Unity + UnityGaussianSplatting | URP | Modellerin oyun motorunda görüntülenmesi |
| Luma AI | hazır bulut hizmeti | Kapalı kutu 3DGS üretimi |
| Donanım (A) | RTX 2060 6 GB · Ryzen 5 3500X · 16 GB RAM | Yerel eğitim |
| Donanım (B) | Google Colab, NVIDIA L4 | Bulut eğitim |

**Ortalama iz uzunluğu**, bir 3B noktanın kaç görüntüde gözlendiğini verir ve bu
çalışmada çoklu görünüm örtüşmesinin birincil göstergesi olarak kullanılmıştır.

---

## 3. Veri

Her iki hat da aynı ham videoyu kullanır; kare örneklemesi farklıdır.

| Özellik | Değer |
| :--- | :--- |
| Kaynak | iPhone 11, 0.5× ultra geniş açı (1× açıda derslik kadraja sığmıyor) |
| Video | 1920×1080, 29,97 FPS, 348,8 s, 10.459 kare |
| **A hattı örneklemesi** | `fps=1` → **349 kare**, dikey 1080×1920 |
| **B hattı örneklemesi** | `fps=3` → **1.047 kare**, uzun kenar 1.600 px'e küçültülmüş |

**Neden tüm kareler kullanılmıyor?** 29,97 FPS'te ardışık iki kare arası, yürüme
hızında yalnızca 2–3 cm kamera ötelemesine karşılık gelir; derinlik üçgenlemesi
için bu paralaks yetersizdir. Saniyede bir karede mesafe 0,5–1 metreye çıkar.
Ayrıca tam eşleştirmede karşılaştırma sayısı kare sayısının karesiyle büyür: 349
kare 60.726 çift, 10.459 kare ise 54,7 milyon çift demektir.

B hattında kareler üç kat sık alınmış, her üç adaydan Laplacian varyansı en yüksek
olan tutulmuştur. COLMAP bu ortamda CPU'da çalıştığı için görüntüler küçültülmüştür.

**Kare kalitesi (A hattı).** Laplacian varyansı ile ölçülen netlik medyanı 205;
eşik 100'ün altında kalan **34 kare (%9,7)** bulunmaktadır. Bu karelerde hareket
bulanıklığı ve dokusuz beyaz duvar birlikte görülmektedir — iç mekânlarda dokusuz
yüzeyin rekonstrüksiyonu zorlaştırdığı FreeSplat [05] çalışmasında da
bildirilmektedir. B hattında çözünürlük farklı olduğundan netlik değerleri
(en az 9, ortalama 81) A hattıyla karşılaştırılamaz.

![Şekil 2 — Veri kümesinin iki ucu: solda bol dokulu net kare, sağda hem bulanık hem de kadrajı dokusuz duvarla dolu kare.](../figures/sekil1_kare_kalitesi.jpg)

Laplacian varyansı bulanıklık ile dokusuzluğu ayırmaz; her ikisi de düşük değer
üretir. Bu nedenle ölçüt eleme değil, işaretleme amacıyla kullanılmıştır.

![Şekil 3 — Çekim güzergâhı. Her piramit bir kamera konumudur; sıraların çevresi dolaşılmış, duvar boyunca ilerlenmiştir.](../figures/sekil3_kamera_yolu.jpg)

---

## 4. Deney Düzeni

### 4.1 A hattı — kontrollü karşılaştırma

Yerel eğitim koşularının tamamı **tek ve aynı SfM çıktısını** kullanır:
`exhaustive` eşleştirmeyle üretilen 331 kare, tek COLMAP modeli, 298 eğitim / 33
test bölünmesi. Her koşuda varsayılana göre **yalnızca bir ayar** değişir.
Ablasyonlar 15.000, doğrulama koşuları 30.000 iterasyonla çalıştırılmıştır.
Metrikler `ns-eval` ile ayrılmış test karelerinde ölçülmüştür.

### 4.2 B hattı — ortam ve hizmet karşılaştırması

Bu koşular A hattıyla aynı kontrol altında **değildir**; amaç ortam ve hizmet
karşılaştırmasıdır.

| Koşu | Ortam | SfM | Eğitim |
| :--- | :--- | :--- | :--- |
| **C1** | Colab, NVIDIA L4 | 1.047 kare, `sequential`, CPU; ana model 823 kare | `splatfacto`, 30.000 iterasyon |
| **C2** | Colab, NVIDIA L4 | C1 ile aynı SfM çıktısı | `splatfacto-big` + ölçek düzenlemesi, 30.000 iterasyon |
| **L1** | Luma AI | hizmet içinde, görünmez | hizmet içinde, görünmez |

C2'nin `splatfacto-big` olduğu, iki eşik değerinin bu yapılandırmanın
varsayılanlarıyla eşleşmesinden doğrulanmıştır.

### 4.3 Oda denemeleri ve çıkarılan dersler

İlk üç koşu hattın çalıştığını gösterdi ama **karşılaştırma üretmedi**: her koşuda
birden fazla değişken aynı anda değişti ve ölçüm düzeni eksikti.

| Oda koşusu | Girdi | Kaydolan | SfM modeli | İz uzunluğu | Sonuç |
| :--- | ---: | ---: | ---: | ---: | :--- |
| R1 video | 309 kare | 229 (%74,1) | 2 | 5,88 | İğne artefaktları, elendi |
| R2 79 foto | 79 | 63 (%79,7) | **3 (parçalandı)** | **3,03** | Geometri oluştu, sahne bölündü |
| R3 512 foto | 512 | 476 (%93,0) | 1 | **7,90** | Tek model, 7 ayar birlikte değişti |

Derslik çalışmasına geçmeden önce düzeltilenler:

| Eksik | Düzeltme |
| :--- | :--- |
| Koşu başına birden fazla değişken | Tek sabit SfM çıktısı + koşu başına tek değişken |
| Ölçüm eğitim görünümlerinde yapılıyordu | %10 test ayrımı, `ns-eval` ile ölçüm |
| Süre ve VRAM kaydedilmiyordu | Her koşuda otomatik kayıt |
| COLMAP mapper ayarları tutarsızdı | Üç SfM koşusu da aynı komutla |
| Eşleştirme stratejisi hiç sınanmamıştı | Üç strateji ölçüldü |
| 3DGS seçimi ölçülmemiş gerekçeye dayanıyordu | NeRF karşılaştırması eklendi |

### 4.4 Her iki ortamda görülen üretim hattı hatası

Nerfstudio `transforms.json` dosyasını daima `colmap/sparse/0` klasöründen üretir.
COLMAP sahneyi parçaladığında en büyük model orada olmak zorunda değildir:

* **A hattında** 331 görüntülük model `sparse/1`'e, 2 görüntülük dejenere artık
  `sparse/0`'a yazılmıştı. İlk eğitim denemesi farkına varılmadan 2 kare üzerinde
  koştu ve ancak değerlendirme aşamasında yakalandı.
* **B hattında** aynı hata bağımsız olarak görüldü: COLMAP beş model üretti, 823
  görüntülük ana model `sparse/1`'de, 2 görüntülük artık `sparse/0`'da idi ve ilk
  `transforms.json` yalnızca 2 poz içeriyordu.

Her iki ortamda bağımsız olarak ortaya çıkması, bunun tesadüf değil **hattın
yapısal bir tuzağı** olduğunu gösterir. Eğitimden önce kare sayısının doğrulanması
zorunlu adım hâline getirilmiştir (`scripts/fix_transforms.py`; B hattında
`--skip-colmap --colmap-model-path colmap/sparse/1`).

---

## 5. A Hattı — Yerel Koşuların Sonuçları

### 5.1 Eşleştirme stratejisi

Üç koşu da aynı 349 kareyi girdi alır; yalnızca COLMAP'in hangi kare çiftlerini
karşılaştıracağı değişir.

| | `sequential` | `exhaustive` | `vocab_tree` |
| :--- | ---: | ---: | ---: |
| Çalışma biçimi | komşu kareler | tüm çiftler (60.726) | sözlükle seçilen çiftler |
| **Eşleştirme süresi** | **1,14 dk** | 8,17 dk | 10,81 dk |
| Toplam süre | 6,57 dk | 13,86 dk | 16,07 dk |
| **Kaydolan görüntü** | 149 (%42,7) | **331 (%94,8)** | **331 (%94,8)** |
| Üretilen SfM modeli | **4 parça** | 1 | 1 |
| 3B nirengi noktası | 26.296 | 65.185 | 66.725 |
| Ortalama iz uzunluğu | 4,59 | 4,88 | 4,94 |
| Yeniden izdüşüm hatası | **0,660 px** | 0,718 px | 0,697 px |

`sequential` yalnızca kare numarası yakın olan çiftleri eşleştirir. Dersliğin
çevresi dolaşılıp başlangıca dönüldüğünde 300. kare ile 5. kare aynı bölgeyi
görmesine rağmen hiç karşılaştırılmaz; zincirin koptuğu yerde sahne parçalanır.
Bu, stratejinin yapısal sınırıdır, parametreyle giderilemez.

`vocab_tree` bu ölçekte avantaj sağlamadı: `exhaustive` ile aynı kayıt oranını
üretti, ancak eşleştirmesi daha uzun sürdü. Sözlük kurma ve sorgulama maliyeti,
349 karede 60.726 çifti doğrudan karşılaştırmaktan pahalıya gelmektedir.

**Seçim:** Tüm yerel eğitim koşuları `exhaustive` çıktısı üzerinde yapılmıştır.

### 5.2 Eğitim ayarları (15.000 iterasyon)

| Koşu | Değişen ayar | PSNR | SSIM | LPIPS | Süre | VRAM | Gaussian |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| G1 | — (varsayılan) | 27,22 | 0,9091 | 0,1759 | 8,9 dk | 2.289 MB | 551.246 |
| **G2** | `antialiased` [02] | **27,38** | **0,9111** | **0,1697** | 9,5 dk | 2.299 MB | 565.603 |
| G3 | ölçek düzenlemesi [03] | 27,14 | 0,9084 | 0,1838 | 11,2 dk | 2.470 MB | 534.193 |
| G4 | kamera pozu opt. (SO3xR3) | 22,52 | 0,7794 | 0,2119 | 14,0 dk | 2.673 MB | 540.495 |
| G5 | `splatfacto-big` | 26,55 | 0,9031 | 0,1757 | 17,8 dk | 4.285 MB | 1.289.932 |
| G6 | tam çözünürlük (1080×1920) | 26,87* | 0,9053* | 0,2705* | 21,6 dk | 4.749 MB | 673.386 |

PSNR/SSIM'de yüksek, LPIPS'te düşük değer iyidir.
\* G6 metrikleri 1080×1920'de, diğerleri 540×960'ta hesaplandığı için diğer
satırlarla karşılaştırılamaz; G6 yalnızca tam çözünürlüğün bu donanımda
çalıştığını gösterir.

![Şekil 4 — Eğitim ilerleyişi (aynı kamera). Sıralar önce bulanık kütleler hâlinde, sonra kenarları oturmuş ve dokusu netleşmiş durumda.](../figures/sekil2_egitim_ilerleyisi.jpg)

### 5.3 Doğrulama: 30.000 iterasyon

Ablasyonlar süre bütçesi nedeniyle 15.000 iterasyonla yapıldı; Splatfacto'nun
varsayılanı ise 30.000'dir. Önerilen yapılandırma (G2) ve yoğun model (G5) bu
bütçeyle tekrarlandı.

| Koşu | PSNR | SSIM | LPIPS | Süre | VRAM | Gaussian |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| G2 — 15k | 27,38 | 0,9111 | 0,1697 | 9,5 dk | 2.299 MB | 565.603 |
| **G2 — 30k** | **28,05** | **0,9142** | 0,1525 | 23,4 dk | 4.141 MB | 566.064 |
| G5 — 15k | 26,55 | 0,9031 | 0,1757 | 17,8 dk | 4.285 MB | 1.289.932 |
| G5 — 30k | 27,50 | 0,9082 | **0,1503** | 40,4 dk | 4.889 MB | 1.303.990 |

* **İterasyonu ikiye katlamak karşılığını veriyor:** G2'de PSNR +0,67 dB,
  LPIPS 0,1697 → 0,1525. Nihai modeller 30.000 ile üretilmelidir.
* **Yoğun model, yeterince eğitildiğinde bile öne geçmiyor:** G5-30k, G2-30k'nın
  PSNR ve SSIM'de gerisindedir; yalnızca LPIPS'te ihmal edilebilir farkla
  öndedir. Buna karşılık %73 daha uzun sürer, 2,3 kat Gaussian ve 2,3 kat dosya
  boyutu üretir.

![Şekil 5 — Önerilen yapılandırmayla üretilen modelden iki ek görünüm.](../figures/sekil6_model_acilar.jpg)

### 5.4 3DGS ve NeRF karşılaştırması

Yöntem seçimini ölçmek için aynı veri ve iterasyon sayısıyla `nerfacto` eğitildi.

| Ölçüt | `splatfacto` (G1) | `nerfacto` (G7) | Fark |
| :--- | ---: | ---: | :--- |
| PSNR | **27,22 dB** | 22,48 dB | 3DGS +4,74 dB |
| SSIM | **0,9091** | 0,7874 | 3DGS lehine |
| LPIPS | **0,1759** | 0,3260 | NeRF ~2 kat kötü |
| Eğitim süresi | **8,9 dk** | 11,8 dk | 3DGS %24 hızlı |
| Tepe VRAM | **2.289 MB** | 4.459 MB | NeRF 1,9 kat |

![Şekil 6 — Aynı test kamerası, üç yöntem. G2 keskin ve hizalı; G4'ün render'ı net olmasına karşın sahne gerçek fotoğrafa göre ötelenmiş; G7 (NeRF) sahneyi kurmuş ama sıra kenarları birbirine karışmış durumda.](../figures/sekil4_render_karsilastirma.jpg)

NeRF serbest 3B bakışta sahne bütünlüğünü (duvar, tavan, pencereler) kurmuştur;
zayıflığı kenar keskinliğindedir. Yöntem seçiminin ikinci ve bu ölçümden bağımsız
gerekçesi aktarımdır: Unity görüntüleyicisi ve VR hattı Gaussian temsili
gerektirir; NeRF modeli `.ply` olarak dışa aktarılamaz ve gerçek zamanlı render
edilemez [18], [22].

> `nerfacto` ölçümü `tiny-cuda-nn` kurulduktan sonra alınmıştır. Kütüphane
> kurulmadan adım süresi 1.470 ms, kurulduktan sonra 48 ms ölçülmüştür
> (yaklaşık 30 kat).

---

## 6. B Hattı — Bulut ve Hazır Hizmet Sonuçları

### 6.1 SfM: bulut ortamında sahne parçalanması

Bulut koşusu `sequential` eşleştirmeyle ve üç kat sık örneklenmiş 1.047 kareyle
yapıldı. Karelerin %94,8'i (993) bir modele yerleşti, ancak sahne **beş parçaya
bölündü** ve en büyük model karelerin yalnızca **%78,6'sını (823)** kapsadı.

| Bulut SfM modeli | Kayıtlı kare | 3B nokta | Yeniden izdüşüm hatası |
| :--- | ---: | ---: | ---: |
| **Model 1 (ana)** | **823** | 250.782 | 0,57 px |
| Model 2 | 64 | 28.173 | 0,57 px |
| Model 4 | 57 | 7.240 | 0,67 px |
| Model 3 | 47 | 3.345 | 0,70 px |
| Model 0 (artık) | 2 | 2.862 | 0,21 px |

![Şekil 7 — Bulut hattında COLMAP modellerinin video zamanına göre kapsamı. Ana model videonun ilk 3:48'ini kesintisiz kapsar; zincir yaklaşık 4:07, 4:34 ve 5:09'da kopmuştur.](../figures/sekil7_bulut_colmap_kapsam.png)

Kopma noktalarındaki kareler incelendiğinde **sandalye ve sıra altına çok yakın
çekimler** (4:07–4:10) ile **neredeyse boş beyaz duvar görünümleri** (4:35, 5:11)
dikkat çekmektedir. Kareleri sık almak kayıt oranını artırdı, parçalanmayı
önlemedi.

COLMAP bu ortamda CUDA desteği olmadan çalıştığı için SfM uzun sürdü: özellik
çıkarma 7,2 dk, eşleştirme ~40 dk, haritalama ~50 dk (toplam ~1,5 saat).

Eğitim koşuları ana model (823 kare) üzerinde yapılmıştır.

### 6.2 Eğitim ve hazır hizmet

| Ölçüt | C1 `splatfacto` | C2 `splatfacto-big` + ölçek düz. | L1 Luma AI |
| :--- | ---: | ---: | ---: |
| Eğitimdeki kare | 823 | 823 | bilinmiyor |
| `cull_alpha_thresh` | 0,1 | 0,005 | — |
| `densify_grad_thresh` | 0,0008 | 0,0005 | — |
| Gaussian | 634.243 | 1.258.471 | 1.068.282 |
| Model dosyası | 157 MB | 312 MB | ölçülmedi |
| PSNR | 27,16 dB | 26,78 dB | ölçülemez |
| SSIM | 0,8923 | 0,8924 | — |
| LPIPS | 0,2842 | 0,2810 | — |
| Unity'de gezinme | zor, yoğun floater | zor, yoğun floater | kolay, temiz |

Bulut ölçümleri 900×1600 çözünürlükte ve Nerfstudio'nun varsayılan test
bölmesiyle alınmıştır; **Bölüm 5'teki değerlerle karşılaştırılamaz.**

C2 ölçümde kazanç getirmedi (PSNR −0,38 dB, SSIM aynı, LPIPS −0,003) ama Gaussian
sayısını ve dosya boyutunu yaklaşık iki katına çıkardı. C2'de üç ayar birlikte
değiştiği için etki ayrıştırılamaz; sonuç A hattındaki tek değişkenli sonuçlarla
(G3, G5) tutarlıdır.

### 6.3 Unity'de görsel karşılaştırma

![Şekil 8 — Unity'de aynı derslik: (a) Luma AI, iç bakış; (b) C1, en iyi iç bakış; (c) C1, sahne dışından; (d) C2, iç bakış. Modellerin koordinat sistemleri farklı olduğundan görüntüler aynı kamera noktasından alınamamıştır.](../figures/sekil8_unity_karsilastirma.jpg)

Bulut modelleri iç bakışta tahta, çerçeveli resim, kürsü ve sıraları okunur
biçimde gösterir; ancak kenarlarda ve kamera önünde yoğun, iğne biçimli
Gaussian'lar vardır ve temiz bir kare yalnızca çekim konumlarına yakın dar
açılardan bulunabilir. Sahne dışından bakıldığında model yoğun bir küme ve
çevresinde uzun çizgiler olarak görünür (Şekil 8c).

Luma AI modeli iç bakışta pencere ve jaluzileri, sıra düzenini, tavan
aydınlatmasını, projeksiyonu ve duvar prizlerini temiz biçimde gösterir; gezinme
rahattır. **Gaussian sayısı kalite ölçüsü değildir:** Luma 1,07 milyon Gaussian
ile temiz, C2 1,26 milyon Gaussian ile dağınıktır.

Luma'nın neden daha temiz olduğu **bilinmemektedir**; hizmet kapalıdır, ayarları
ve ara çıktıları görünmez. Olası nedenler: videonun tamamının tek modelde
kullanılması (bulut hattında karelerin %21'i ana modelin dışında kaldı), dışa
aktarmada temizlik ve farklı eğitim ayarları.

> Unity'de splat'ların görünmesi için URP renderer'a **Gaussian Splat URP Feature**
> eklenmesi gerekmiştir; eklenmeden asset doğru olsa bile sahne boş kalmaktadır.

**Karşılaştırma uyarısı:** C1/C2 ile A hattı modelleri arasındaki görsel fark
yalnızca ortamdan kaynaklanmıyor olabilir. C1/C2 `sequential` eşleştirmeyle ve
parçalanmış bir SfM çıktısıyla (823/1.047 kare) eğitilmiştir; A hattı modelleri
`exhaustive` ile tek bütün model üzerinde eğitilmiştir. Bulgu 1 ışığında, Unity'de
gözlenen floater yoğunluğunun büyük bölümü bu SfM farkıyla açıklanabilir.

---

## 7. Bulgular

Her maddenin hangi hattan geldiği parantez içinde belirtilmiştir.

**1. Örtüşme, kare sayısından daha belirleyicidir.** (A ve B) `sequential` ile
`exhaustive` aynı 349 kareyi aldı; ilki %42,7'sini kaydedip sahneyi dörde böldü.
Aynı örüntü oda denemelerinde (R2: iz 3,03, parçalandı — R3: iz 7,90, tek model)
ve bulut hattında da görüldü: 1.047 karelik `sequential` koşusu sahneyi beşe
böldü. **Kareleri üç kat sık almak parçalanmayı önlemedi.** Bina ölçeğinde
izlenecek birincil SfM göstergesi ortalama iz uzunluğudur, kaydolan görüntü oranı
değil.

**2. Düşük piksel hatası kalite göstergesi değildir.** (A ve B) `sequential` en
düşük yeniden izdüşüm hatasına sahiptir (0,660 px) ama kullanılabilir sonuç
üretmeyen tek koşudur. Bulut hattındaki parçalı modelde de hata 0,57 px'tir —
yani beşe bölünmüş bir sahne, sayısal olarak "daha iyi" görünmektedir. Oda
denemelerinde R1 de 0,880 px ile sağlıklı görünüp kullanılabilir geometri
üretmemişti.

**3. Kenar yumuşatma ucuz ve ölçülebilir bir kazançtır.** (A) `antialiased` kipi
(Mip-Splatting [02]) üç metrikte de en iyi sonucu verdi; maliyeti %6 ek süre ve
10 MB ek bellektir.

> gsplat 0.1.4'ün `antialiased` kipi, Mip-Splatting'in 2B mip filtresi
> bileşenine karşılık gelir; makalenin 3B yumuşatma filtresi bu sürümde yoktur.

**4. Kamera pozu optimizasyonu ölçüm hattı için risklidir.** (A) G4 metriklerde
belirgin biçimde kötüleşti (PSNR 27,22 → 22,52), ancak Şekil 6 render'ın
**bulanık değil kaymış** olduğunu gösteriyor. `SO3xR3` eğitim kameralarının
pozlarını düzeltir, ayrılmış test kameraları bu düzeltmeyi almaz; model
kaydırılmış bir koordinat çerçevesinde öğrenir. Düşüş büyük ölçüde hizalama
farkıdır, kalite kaybı değil.

Projeye etkisi: erişilebilirlik ölçümü, Gaussian geometrisinin COLMAP kamera
pozlarıyla **aynı çerçevede** kalmasını gerektirir; geçit ölçüleri ve 2B
tespitlerin 3B kaydı bu pozlar üzerinden yapılacaktır. Bu nedenle ölçüm hattında
varsayılan olarak açılmamalıdır. (Oda denemelerinde R3 bu ayarla eğitilip
"iyileştirme" olarak kaydedilmişti; ölçüm yapılmamıştı.)

**5. Gaussian bütçesini artırmak karşılığını vermiyor.** (A ve B)
`splatfacto-big` A hattında hem 15.000 hem 30.000 iterasyonda önerilen
yapılandırmanın gerisinde kaldı; B hattında da (C2) kazanç gözlenmedi. Model
dosyası boyutu Gaussian sayısıyla doğrusaldır: her Gaussian **248 bayt** yer
kaplar — aynı oran bulut modellerinde de ölçüldü (157 MB / 634.243 ve
312 MB / 1.258.471). Bu, Gaussian bütçesini bir kalite parametresi olduğu kadar
**dağıtım kısıtı** hâline getirir; Unity ve VR aşamasında yükleme süresi ve GPU
belleği doğrudan dosya boyutuyla ölçeklenecektir.

**6. Darboğaz GPU belleği değil, SfM süresidir.** (A ve B) A hattında en ağır
koşu 4.889 MB tepe VRAM kullandı; 6.144 MB'nin en fazla %80'i, hiçbir koşuda
bellek taşması olmadı. Buna karşılık B hattında CUDA'sız COLMAP ile 1.047 karenin
SfM aşaması ~1,5 saat sürdü. Bina ölçeğindeki gerçek kısıtlar: **(a)** COLMAP
eşleştirme süresi — kare sayısının karesiyle büyür ve CUDA desteği olmadan
katlanır; **(b)** sistem belleği (RAM) — görüntü önbelleği için, VRAM değil;
**(c)** sahne parçalanma riski.

**7. İterasyon sayısı 30.000 olmalıdır.** (A) 15.000'den 30.000'e çıkmak önerilen
yapılandırmada PSNR'ı 0,67 dB, LPIPS'i 0,1697'den 0,1525'e iyileştirdi.

**8. 3DGS seçimi ölçümle desteklenmektedir.** (A) NeRF aynı veri ve iterasyonla
her ölçütte geride kaldı. *Araç Seçimi* raporunda gerekçeye dayanarak alınan
Splatfacto kararı artık ölçüme dayanmaktadır.

**9. Gaussian'lar çekim yönüne bağlıdır.** (A ve B) Model, çekim yönlerinden uzak
bir bakış açısından (tam tepeden ya da sahne dışından) render edildiğinde
Gaussian'lar kenarlarından görülüp iğneye dönüşmektedir; olgu bulut modellerinde
çok daha belirgindir (Şekil 8c). Bu çekimden kat planı benzeri bir üstten görünüm
elde edilememiştir. Görsel katman, ölçüm katmanının yerine geçemez.

**10. Hazır hizmet görsel kalitede öndedir, ancak ölçüm hattına uygun değildir.**
(B) Luma AI aynı videodan en temiz ve en rahat gezilebilen modeli üretti. Ancak
ayarları, ara çıktıları ve eğitim kareleri görünmediği için sonucu ölçülemez,
tekrarlanamaz ve COLMAP çerçevesiyle ilişkisi bilinmez. Görsel sunum katmanı için
yedek seçenek olarak değerlendirilebilir.

---

## 8. Öneriler

### 8.1 Önerilen yapılandırma

| Karar | Seçim | Dayanak |
| :--- | :--- | :--- |
| Sahne temsili | 3DGS (`splatfacto`) | Bulgu 8 + Unity/VR aktarım zorunluluğu |
| Eşleştirme | `exhaustive` (oda/derslik ölçeğinde) | Bulgu 1 |
| Rasterizasyon | `antialiased` | Bulgu 3 |
| Kamera optimizasyonu | **kapalı** | Bulgu 4 |
| Gaussian bütçesi | varsayılan | Bulgu 5 |
| İterasyon | 30.000 | Bulgu 7 |
| SfM ortamı | CUDA destekli COLMAP | Bulgu 6 |

Ölçülen sonuç: **PSNR 28,05 dB · SSIM 0,9142 · LPIPS 0,1525 · 23,4 dk ·
4.141 MB VRAM · 566.064 Gaussian · 134 MiB model dosyası**.

### 8.2 Bina ölçeğine dair

| Konu | Öngörü |
| :--- | :--- |
| Eşleştirme | 3.000 karede ~4,5 milyon çift; tam eşleştirme saatler sürer, uygulanabilir değildir |
| Strateji | Döngü kapanışlı `sequential` veya `vocab_tree` daha büyük veriyle ölçülmelidir |
| Bölümlendirme | Tek parça yerine bölüm bazlı eğitim gerekir (VastGaussian [06]) |
| Donanım | 6 GB VRAM yeterlidir; öncelik daha hızlı GPU ve **CUDA destekli COLMAP** |
| Bulut ortamı | COLMAP CUDA destekli kurulmalı ya da SfM yerelde çalıştırılıp sonuç buluta taşınmalı; oturum kopmalarına karşı ara çıktılar düzenli yedeklenmeli |
| Model boyutu | Tek derslik 134–312 MiB; bir kat için toplam boyut ve Unity yükleme bütçesi önceden hesaplanmalıdır |
| Çekim planı | Sabit adım aralığı; ani yakın çekimlerden ve boş duvara uzun süre bakmaktan kaçınılmalı; başlangıç noktasına dönülerek döngü kapatılmalı |
| Hazır hizmet | Görsel sunum için yedek seçenek; ölçüm hattında kullanılmamalı |

### 8.3 Ölçek

Hiçbir koşuda ölçülmüş referans mesafe kaydedilmediği için benzerlik dönüşümü
(X_m = s·R·X + t) uygulanamamıştır. Bu nedenle mevcut modellerden kapı net
açıklığı, geçiş genişliği veya rampa eğimi gibi **metrik değerler
çıkarılamaz**; erişilebilirlik ölçümüne geçmeden önce mekânda en az üç referans
mesafenin ölçülmesi gerekmektedir.

---

## Ek — Kayıtlar

**A hattı** koşu kayıtları (ayarlar, metrikler, yeniden üretim adımları):

* `experiments/hafta-03_oda-01/` — 3 pilot koşu
* `experiments/hafta-03_sinif-01/` — 3 SfM + 9 eğitim koşusu
* `models/` — üretilen `.ply` modelleri (Git LFS)

**B hattı** çıktıları (COLMAP modelleri, eğitim kayıtları, değerlendirme
dosyaları, PLY): Google Drive `oda3_yedek/`

Betikler `scripts/` altındadır: `sfm_run.py`, `colmap_stats.py`,
`fix_transforms.py`, `train_run.py`, `run_queue.sh`, `run_queue_30k.sh`,
`eval_run.py`, `render_compare.py`, `render_overview.py`, `export_all_ply.sh`,
`make_figures.py`, `md_to_docx.py`, `install_tcnn.bat`.

Ham kareler ve eğitim çıktıları boyut nedeniyle sürümlenmez.

### Kaynaklar

Numaralar *Literatür Araştırması* raporunun 2. bölümündeki kayıtlara aittir.

* **[02]** Yu ve diğerleri — *Mip-Splatting: Alias-free 3D Gaussian Splatting*, CVPR 2024.
* **[03]** Huang ve diğerleri — *2D Gaussian Splatting for Geometrically Accurate Radiance Fields*, SIGGRAPH 2024.
* **[05]** Wang ve diğerleri — *FreeSplat: Generalizable 3D Gaussian Splatting Towards Free-View Synthesis of Indoor Scenes*, NeurIPS 2024.
* **[06]** Lin ve diğerleri — *VastGaussian: Vast 3D Gaussians for Large Scene Reconstruction*, CVPR 2024.
* **[18]** Schieber ve diğerleri — *Semantics-Controlled Gaussian Splatting for Scene Reconstruction and Rendering in Virtual Reality*, IEEE VR 2025.
* **[22]** *Enabling Digital Spaces: Bringing Gaussian Splats Alive in XR*, XR Salento 2025.
* Nerfstudio — Splatfacto belgesi (docs.nerf.studio): `splatfacto-big` ve PhysGaussian'dan alınan ölçek düzenlemesi.
