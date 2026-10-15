# Hafta 3 — 3DGS Üretim Hattının Kurulması ve Yöntem Karşılaştırması

**Proje:** Engelli Bireyler İçin Akıllı Erişilebilir Rota Planlama
**Aşama:** A1 — Mekân modelleme
**Hazırlayanlar:** Sabri Duruk, Yunis Teymurlu · **Danışman:** Öğr. Gör. Koray AKİ

---

## 1. Amaç

Projenin hedefi, bir binanın iç mekânını fotoğraf/video ile modelleyip tekerlekli
sandalye kullanan bireyler için erişilebilir rota hesaplamaktır. Bu hafta o hattın
ilk halkası olan **3D Gaussian Splatting (3DGS) üretim hattı** kuruldu ve hangi
yöntemin bina ölçeğinde kullanılabileceğini öngörmek için karşılaştırıldı.

Çalışma iki aşamada yürütüldü: önce bir ekip üyesinin odasında hat uçtan uca
çalıştırıldı (3 koşu), ardından D207 dersliğinde tek değişkenli kontrollü
karşılaştırma yapıldı (12 koşu).

Yanıtlanan sorular:

| # | Soru | Bölüm |
| :--- | :--- | :--- |
| 1 | COLMAP'in hangi kareleri eşleştireceği seçimi sonucu nasıl etkiler? | 5.1 |
| 2 | Literatürdeki 3DGS iyileştirmeleri ölçülebilir kazanç sağlıyor mu? | 5.2 |
| 3 | 6 GB VRAM bu iş için nerede yetersiz kalıyor? | 6 |
| 4 | Gaussian temsili, NeRF'e göre üstün mü? | 5.4 |

Haftanın çıktısı, önerilen yapılandırmayla üretilen derslik modelidir:

![Şekil 1 — Üretilen modelin genel görünümü (önerilen yapılandırma, 30.000 iterasyon). Tavan aydınlatması, projeksiyon, tahtalar, kapı, pencere ve sıralar arasındaki geçiş koridoru ayırt edilebilmektedir.](../figures/sekil5_model_genel.jpg)

Semantik eleman tespiti, çizge üretimi ve rota hesabı bu haftanın kapsamı
dışındadır.

---

## 2. Yöntem ve Araçlar

```text
Kare çıkarma   →   COLMAP (SfM)        →   Splatfacto (3DGS)   →   PLY
FFmpeg             kamera pozları +        gsplat CUDA             SuperSplat /
1 kare/s           seyrek nokta bulutu     rasterizasyonu          Unity
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

| Araç | Sürüm | İşlev |
| :--- | :--- | :--- |
| COLMAP | 3.9.1 CUDA | Kamera pozları ve seyrek nokta bulutu |
| Nerfstudio / Splatfacto | 1.0.3 | 3DGS eğitimi, dışa aktarım, `ns-eval` |
| gsplat | 0.1.4 | Gaussian rasterizasyon CUDA çekirdeği |
| tiny-cuda-nn | kaynak (SM 75) | NeRF karşılaştırması için hash kodlaması |
| FFmpeg · OpenCV | 6.1+ · 4.8+ | Kare çıkarma · netlik ölçümü |
| Donanım | RTX 2060 6 GB · Ryzen 5 3500X · 16 GB RAM | — |

---

## 3. Veri

| Özellik | Değer |
| :--- | :--- |
| Kaynak | iPhone 11, 0.5× ultra geniş açı (1× açıda derslik kadraja sığmıyor) |
| Video | 1920×1080, 29,97 FPS, 348,8 s, 10.459 kare |
| Kullanılan kare | FFmpeg `fps=1` → **349 kare** (dikey 1080×1920) |

**Neden 349 kare?** 29,97 FPS'te ardışık iki kare arası, yürüme hızında yalnızca
2–3 cm kamera ötelemesine karşılık gelir; derinlik üçgenlemesi için bu paralaks
yetersizdir. Saniyede bir karede mesafe 0,5–1 metreye çıkar. Ayrıca tam
eşleştirmede karşılaştırma sayısı kare sayısının karesiyle büyür: 349 kare 60.726
çift, 10.459 kare ise 54,7 milyon çift demektir.

**Kare kalitesi.** Laplacian varyansı ile ölçülen netlik medyanı 205; eşik 100'ün
altında kalan **34 kare (%9,7)** bulunmaktadır. Bu karelerde hareket bulanıklığı
ve dokusuz beyaz duvar birlikte görülmektedir — iç mekânlarda dokusuz yüzeyin
rekonstrüksiyonu zorlaştırdığı FreeSplat [05] çalışmasında da bildirilmektedir.

![Şekil 2 — Veri kümesinin iki ucu: solda bol dokulu net kare, sağda hem bulanık hem de kadrajı dokusuz duvarla dolu kare.](../figures/sekil1_kare_kalitesi.jpg)

---

## 4. Deney Düzeni

### 4.1 Oda denemeleri ve çıkarılan dersler

İlk üç koşu hattın çalıştığını gösterdi ama **karşılaştırma üretmedi**: her
koşuda birden fazla değişken aynı anda değişti ve ölçüm düzeni eksikti.

| Oda koşusu | Girdi | Kaydolan | SfM modeli | İz uzunluğu | Sonuç |
| :--- | ---: | ---: | ---: | ---: | :--- |
| R1 video | 309 kare | 229 (%74,1) | 2 | 5,88 | İğne artefaktları, elendi |
| R2 79 foto | 79 | 63 (%79,7) | **3 (parçalandı)** | **3,03** | Geometri oluştu, sahne bölündü |
| R3 512 foto | 512 | 476 (%93,0) | 1 | **7,90** | Tek model, 7 ayar birlikte değişti |

Sınıf çalışmasına geçmeden önce düzeltilenler:

| Eksik | Düzeltme |
| :--- | :--- |
| Koşu başına birden fazla değişken | Tek sabit SfM çıktısı + koşu başına tek değişken |
| Ölçüm eğitim görünümlerinde yapılıyordu | %10 test ayrımı (298 / 33 kare), `ns-eval` ile ölçüm |
| Süre ve VRAM kaydedilmiyordu | Her koşuda otomatik kayıt |
| COLMAP mapper ayarları tutarsızdı | Üç SfM koşusu da aynı komutla |
| Eşleştirme stratejisi hiç sınanmamıştı | Üç strateji ölçüldü |
| 3DGS seçimi ölçülmemiş gerekçeye dayanıyordu | NeRF karşılaştırması eklendi |

### 4.2 Üretim hattında bulunan hata

Nerfstudio `transforms.json` dosyasını daima `colmap/sparse/0` klasöründen
üretir. COLMAP sahneyi parçaladığında en büyük model orada olmak zorunda
değildir: sınıf verisinde **331 görüntülük model `sparse/1`'e, 2 görüntülük
dejenere artık `sparse/0`'a** yazılmıştı. İlk eğitim denemesi farkına varılmadan
2 kare üzerinde koştu ve ancak değerlendirme aşamasında yakalandı. Bu kontrol
üretim hattının zorunlu adımı hâline getirildi (`scripts/fix_transforms.py`).

### 4.3 Deneysel kontrol

Tüm eğitim koşuları **tek ve aynı SfM çıktısını** kullanır: `exhaustive`
eşleştirmeyle üretilen 331 kare, tek COLMAP modeli, 298 eğitim / 33 test
bölünmesi. Her koşuda varsayılana göre yalnızca bir ayar değişir. Ablasyonlar
15.000, doğrulama koşuları 30.000 iterasyonla çalıştırılmıştır.

---

## 5. Sonuçlar

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

![Şekil 3 — Eğitim ilerleyişi (aynı kamera). Sıralar önce bulanık kütleler hâlinde, sonra kenarları oturmuş ve dokusu netleşmiş durumda.](../figures/sekil2_egitim_ilerleyisi.jpg)

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

![Şekil 4 — Önerilen yapılandırmayla üretilen modelden iki ek görünüm.](../figures/sekil6_model_acilar.jpg)

### 5.4 3DGS ve NeRF karşılaştırması

Yöntem seçimini ölçmek için aynı veri ve iterasyon sayısıyla `nerfacto` eğitildi.

| Ölçüt | `splatfacto` (G1) | `nerfacto` (G7) | Fark |
| :--- | ---: | ---: | :--- |
| PSNR | **27,22 dB** | 22,48 dB | 3DGS +4,74 dB |
| SSIM | **0,9091** | 0,7874 | 3DGS lehine |
| LPIPS | **0,1759** | 0,3260 | NeRF ~2 kat kötü |
| Eğitim süresi | **8,9 dk** | 11,8 dk | 3DGS %24 hızlı |
| Tepe VRAM | **2.289 MB** | 4.459 MB | NeRF 1,9 kat |

![Şekil 5 — Aynı test kamerası, üç yöntem. G2 keskin ve hizalı; G4'ün render'ı net olmasına karşın sahne gerçek fotoğrafa göre ötelenmiş; G7 (NeRF) sahneyi kurmuş ama sıra kenarları birbirine karışmış durumda.](../figures/sekil4_render_karsilastirma.jpg)

NeRF serbest 3B bakışta sahne bütünlüğünü (duvar, tavan, pencereler) kurmuştur;
zayıflığı kenar keskinliğindedir. Bu ayrım erişilebilirlik ölçümü açısından
belirleyicidir: geçit genişliği ölçmek keskin yüzey kenarı gerektirir.

Yöntem seçiminin ikinci ve bu ölçümden bağımsız gerekçesi aktarımdır: Unity
görüntüleyicisi (`UnityGaussianSplatting`) ve VR hattı Gaussian temsili
gerektirir; NeRF modeli `.ply` olarak dışa aktarılamaz ve gerçek zamanlı render
edilemez [18], [22].

---

## 6. Bulgular

**1. Örtüşme, kare sayısından daha belirleyicidir.** `sequential` ile
`exhaustive` aynı 349 kareyi aldı; ilki %42,7'sini kaydedip sahneyi dörde böldü.
Aynı örüntü oda denemelerinde de görüldü (R2: iz 3,03, sahne parçalandı — R3:
iz 7,90, tek model). Bina ölçeğinde izlenecek birincil SfM göstergesi **ortalama
iz uzunluğudur**, kaydolan görüntü oranı değil.

**2. Düşük piksel hatası kalite göstergesi değildir.** `sequential` en düşük
yeniden izdüşüm hatasına sahiptir (0,660 px) ama kullanılabilir sonuç üretmeyen
tek koşudur: her parça kendi içinde tutarlı çözülmüş, parçalar birbirine
bağlanamamıştır. Oda denemelerinde R1 de 0,880 px ile sağlıklı görünüp
kullanılabilir geometri üretmemişti.

**3. Kenar yumuşatma ucuz ve ölçülebilir bir kazançtır.** `antialiased` kipi
(Mip-Splatting [02]) üç metrikte de en iyi sonucu verdi; maliyeti %6 ek süre ve
10 MB ek bellektir. Varsayılan olarak açılması önerilir.

> gsplat 0.1.4'ün `antialiased` kipi, Mip-Splatting'in 2B mip filtresi
> bileşenine karşılık gelir; makalenin 3B yumuşatma filtresi bu sürümde yoktur.

**4. Kamera pozu optimizasyonu ölçüm hattı için risklidir.** G4 metriklerde
belirgin biçimde kötüleşti (PSNR 27,22 → 22,52), ancak Şekil 5 render'ın
**bulanık değil kaymış** olduğunu gösteriyor. `SO3xR3` eğitim kameralarının
pozlarını düzeltir, ayrılmış test kameraları bu düzeltmeyi almaz; model
kaydırılmış bir koordinat çerçevesinde öğrenir. Yani düşüş büyük ölçüde hizalama
farkıdır, kalite kaybı değil.

Projeye etkisi: erişilebilirlik ölçümü, Gaussian geometrisinin COLMAP kamera
pozlarıyla **aynı çerçevede** kalmasını gerektirir; geçit ölçüleri ve 2B
tespitlerin 3B kaydı bu pozlar üzerinden yapılacaktır. Bu nedenle ölçüm hattında
varsayılan olarak açılmamalıdır. (Oda denemelerinde R3 bu ayarla eğitilip
"iyileştirme" olarak kaydedilmişti; ölçüm yapılmamıştı.)

**5. Gaussian bütçesini artırmak karşılığını vermiyor.** `splatfacto-big` hem
15.000 hem 30.000 iterasyonda önerilen yapılandırmanın gerisinde kaldı. Model
dosyası boyutu Gaussian sayısıyla doğrusaldır: her Gaussian **248 bayt** yer
kaplar. Bu, Gaussian bütçesini bir kalite parametresi olduğu kadar **dağıtım
kısıtı** hâline getirir — Unity ve VR aşamasında yükleme süresi ve GPU belleği
doğrudan dosya boyutuyla ölçeklenecektir.

**6. Darboğaz GPU belleği değildir.** En ağır splatfacto koşusu 4.889 MB tepe
VRAM kullandı; 6.144 MB'nin en fazla %80'i. Hiçbir splatfacto koşusunda bellek
taşması olmadı, tam çözünürlük bile sorunsuz çalıştı. Oda denemelerinde
sıkışmanın nedeni 12 megapiksellik fotoğraflardı; video karesi 2 megapiksel
olduğundan görüntü başına bellek yükü yaklaşık altı kat düşüktür.

Bina ölçeğindeki gerçek kısıtlar: **(a)** COLMAP eşleştirme süresi — kare
sayısının karesiyle büyür; **(b)** sistem belleği (RAM) — görüntü önbelleği için,
VRAM değil; **(c)** sahne parçalanma riski — kare sayısı ve mekân karmaşıklığı
arttıkça COLMAP'in tek model kuramama olasılığı yükselir.

**7. Gaussian'lar çekim yönüne bağlıdır.** Model, çekim yönlerinden uzak bir
bakış açısından (örneğin tam tepeden) render edildiğinde Gaussian'lar
kenarlarından görülüp iğneye dönüşmektedir; bu çekimden kat planı benzeri bir
üstten görünüm elde edilememiştir. Görsel katmanın ölçüm katmanı yerine
geçemeyeceğinin somut göstergesidir.

**8. 3DGS seçimi ölçümle desteklenmektedir.** NeRF aynı veri ve iterasyonla her
ölçütte geride kaldı (Bölüm 5.4). *Araç Seçimi* raporunda gerekçeye dayanarak
alınan Splatfacto kararı artık ölçüme dayanmaktadır.

---

## 7. Öneriler

### 7.1 Önerilen yapılandırma

| Karar | Seçim | Dayanak |
| :--- | :--- | :--- |
| Sahne temsili | 3DGS (`splatfacto`) | Bulgu 8 + Unity/VR aktarım zorunluluğu |
| Eşleştirme | `exhaustive` (oda/derslik ölçeğinde) | Bulgu 1 |
| Rasterizasyon | `antialiased` | Bulgu 3 |
| Kamera optimizasyonu | **kapalı** | Bulgu 4 |
| Gaussian bütçesi | varsayılan | Bulgu 5 |
| İterasyon | 30.000 | Bölüm 5.3 |

Ölçülen sonuç: **PSNR 28,05 dB · SSIM 0,9142 · LPIPS 0,1525 · 23,4 dk ·
4.141 MB VRAM · 566.064 Gaussian · 134 MiB model dosyası**.

### 7.2 Bina ölçeğine dair

| Konu | Öngörü |
| :--- | :--- |
| Eşleştirme | 3.000 karede ~4,5 milyon çift; tam eşleştirme saatler sürer, uygulanabilir değildir |
| Strateji | Döngü kapanışlı `sequential` veya `vocab_tree` daha büyük veriyle ölçülmelidir; kesişim noktası 349 karenin üzerindedir |
| Bölümlendirme | Tek parça yerine bölüm bazlı eğitim gerekir (VastGaussian [06]) |
| Donanım | 6 GB VRAM yeterlidir; öncelik daha hızlı GPU, daha büyük VRAM değil |
| Model boyutu | Tek derslik 134 MiB; bir kat için toplam boyut ve Unity yükleme bütçesi önceden hesaplanmalıdır |
| Çekim planı | Sabit adım aralığı; aynı noktadan seri çekim yapılmamalı (oda denemelerinde kamera merkezleri arası medyan mesafe 0,0000 ölçüldü: üst üste çakışan kareler maliyet ekleyip paralaks katmıyor) |

### 7.3 Ölçek

Hiçbir koşuda ölçülmüş referans mesafe kaydedilmediği için benzerlik dönüşümü
(X_m = s·R·X + t) uygulanamamıştır. Bu nedenle mevcut modellerden kapı net
açıklığı, geçiş genişliği veya rampa eğimi gibi **metrik değerler
çıkarılamaz**; erişilebilirlik ölçümüne geçmeden önce mekânda en az üç referans
mesafenin ölçülmesi gerekmektedir.

---

## Ek — Kayıtlar

Koşu kayıtları (ayarlar, metrikler, yeniden üretim adımları):

* `experiments/hafta-03_oda-01/` — 3 pilot koşu
* `experiments/hafta-03_sinif-01/` — 3 SfM + 9 eğitim koşusu

Yerel çalışma klasörleri (boyut nedeniyle sürümlenmez):

```text
data/<veri-kümesi>/             ham kareler ve COLMAP çıktıları
runs/<veri-kümesi>/<koşu>/      eğitim çıktıları ve kontrol noktaları
exports/<veri-kümesi>/<koşu>/   dışa aktarılan splat.ply
```

### Kaynaklar

Numaralar *Literatür Araştırması* raporunun 2. bölümündeki kayıtlara aittir.

* **[02]** Yu ve diğerleri — *Mip-Splatting: Alias-free 3D Gaussian Splatting*, CVPR 2024.
* **[03]** Huang ve diğerleri — *2D Gaussian Splatting for Geometrically Accurate Radiance Fields*, SIGGRAPH 2024.
* **[05]** Wang ve diğerleri — *FreeSplat: Generalizable 3D Gaussian Splatting Towards Free-View Synthesis of Indoor Scenes*, NeurIPS 2024.
* **[06]** Lin ve diğerleri — *VastGaussian: Vast 3D Gaussians for Large Scene Reconstruction*, CVPR 2024.
* **[18]** Schieber ve diğerleri — *Semantics-Controlled Gaussian Splatting for Scene Reconstruction and Rendering in Virtual Reality*, IEEE VR 2025.
* **[22]** *Enabling Digital Spaces: Bringing Gaussian Splats Alive in XR*, XR Salento 2025.
