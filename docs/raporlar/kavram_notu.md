# Kavram Notu — Raporu Anlamak İçin

Bu not, Hafta 3 raporundaki terimleri sıfırdan açıklar ve hocayla görüşmede
sorulabilecek sorulara hazırlık sağlar. Rapordaki her sayının ne anlama geldiğini
burada bulabilirsin.

---

## BÖLÜM 1 — İşin Mantığı

### Temel fikir

Elimizde bir odanın/dersliğin **fotoğrafları** var. İstediğimiz şey, o mekânın
**3 boyutlu dijital kopyası**. Bunu iki adımda yapıyoruz:

```
1. ADIM            2. ADIM
"Bu fotoğraf   →   "Bu konumlardan
 nereden            bakınca böyle
 çekilmiş?"         görünmeli"
 
 COLMAP            Splatfacto (3DGS)
```

Birinci adım olmadan ikincisi hiç çalışmaz. Raporun yarısı birinci adımla ilgili,
çünkü sorunların çoğu orada çıkıyor.

---

### 1. ADIM: COLMAP ve SfM

**SfM (Structure from Motion)** = "Hareketten yapı çıkarma". Birden fazla
fotoğraftan hem kameraların nerede durduğunu hem de sahnenin kaba 3B şeklini aynı
anda hesaplayan yöntem ailesi. **COLMAP** bunu yapan programın adı.

Nasıl çalışıyor:

| Adım | Ne yapar | Günlük dille |
| :--- | :--- | :--- |
| **Öznitelik çıkarma** (SIFT) | Her karede köşe, desen gibi ayırt edici noktaları bulur | "Bu fotoğrafta tanınabilir ne var?" |
| **Eşleştirme** | Aynı noktayı başka karelerde arar | "Bu köşe öbür fotoğrafta da var mı?" |
| **RANSAC** | Yanlış eşleşmeleri eler | "Bu eşleşme saçma, at" |
| **Üçgenleme** | İki farklı açıdan görülen noktanın 3B konumunu hesaplar | İki gözle derinlik görmek gibi |
| **Bundle adjustment** | Tüm kamera konumlarını ve noktaları birlikte rötuşlar | "Hepsi birbirine uysun" |

**Çıktısı:** her karenin 3B konumu + **seyrek nokta bulutu** (sparse point cloud)
— sahnenin birkaç on bin noktadan oluşan kaba iskeleti.

---

### Paralaks — işin kalbindeki kavram

**Paralaks**, iki farklı konumdan bakınca nesnelerin birbirine göre kaymasıdır.
Derinlik hesabı buna dayanır. İki gözün arasındaki ~6 cm mesafe sayesinde derinlik
görmen gibi.

İki kare arasında **yeterli mesafe yoksa paralaks olmaz, derinlik hesaplanamaz.**

Raporda neden 10.459 kareden sadece 349'unu kullandığımızın cevabı bu: saniyede 30
kare çekilen videoda ardışık iki kare arasında yürürken sadece 2–3 cm ilerliyorsun.
Saniyede 1 kare alınca bu mesafe 0,5–1 metre oluyor.

> **Baseline** = iki kamera konumu arasındaki mesafe. "Yetersiz baseline" = iki
> kare birbirine çok yakın = paralaks yok.

---

### İz uzunluğu (track length) — en önemli gösterge

Bir **iz (track)**, aynı 3B noktanın farklı karelerdeki gözlemlerinin zinciridir.
**Ortalama iz uzunluğu**, bir 3B noktanın ortalama kaç karede göründüğüdür.

| İz uzunluğu | Anlamı |
| :--- | :--- |
| 3 civarı | Her nokta sadece 3 karede görülmüş → **örtüşme zayıf**, sahne dağılabilir |
| 5–8 | Sağlam örtüşme, sahne tek parça çıkar |

Raporda neden bu kadar vurgulandı: R2 koşusunda iz uzunluğu 3,03 çıktı ve COLMAP
sahneyi 3 parçaya böldü. R3'te 7,90 çıktı ve tek parça oldu. **Kaydolan kare
oranına bakmak yanıltıcı; asıl gösterge bu.**

---

### Kaydolan görüntü ve sahne parçalanması

**Kaydolan (registered) görüntü:** COLMAP'in konumunu başarıyla hesaplayabildiği
kare. Hesaplayamadıklarını atar.

**Sahne parçalanması:** COLMAP bazen tüm kareleri tek bir tutarlı modelde
birleştiremez ve **birden fazla ayrı model** üretir. Örneğin dersliğin bir
köşesinden bir model, başka köşesinden bağımsız ikinci bir model — ve bunların
birbiriyle ilişkisini kuramaz.

Eğitimde sadece **en büyük parça** kullanılabilir, gerisi çöpe gider. Raporda
`sequential` yöntemi 4 parça üretti ve videonun %57'si kullanılamadı.

---

### Yeniden izdüşüm hatası (reprojection error)

Hesaplanan 3B noktayı tekrar fotoğrafa izdüşürdüğümüzde, gerçekte görüldüğü
pikselden kaç piksel sapıyor? Düşük olması iyidir **ama yetmez.**

Raporun en önemli derslerinden biri bu: `sequential` yöntemi **en düşük** hatayı
verdi (0,660 px) ama kullanılamayan tek sonuçtu. Sebebi: her parça kendi içinde
çok düzgün çözülmüş, ama parçalar birbirine bağlanamamış. Yani "her mahalle kendi
içinde düzenli ama şehir planı yok".

> **Hocaya anlatırken kullanılacak cümle:** *"Düşük piksel hatası, modelin
> doğru olduğunu göstermez; sadece kendi içinde tutarlı olduğunu gösterir."*

---

### Eşleştirme stratejileri — raporun 1. deneyi

COLMAP hangi kare çiftlerini karşılaştıracağına karar vermeli. Üç yol var:

| Strateji | Ne yapar | Artısı | Eksisi |
| :--- | :--- | :--- | :--- |
| **sequential** | Sadece komşu kareleri (1-2, 2-3, 3-4...) | Çok hızlı | **Döngü kapanışı yok** |
| **exhaustive** | Her kareyi her kareyle | En iyi sonuç | Maliyet kare sayısının **karesiyle** büyür |
| **vocab_tree** | Görsel sözlükle benzer kareleri bulup sadece onları | Teoride ölçeklenir | Küçük veride ek yük getirir |

**Döngü kapanışı (loop closure):** Mekânda dolaşıp başladığın yere döndüğünde,
300. kare ile 5. kare aynı yere bakıyordur. `sequential` bunlara hiç bakmaz çünkü
numaraları uzak. Zincir orada kopar ve sahne parçalanır. **Bu bir ayar sorunu
değil, yöntemin yapısal sınırı.**

**Karesel büyüme neden önemli:**

| Kare sayısı | Karşılaştırma |
| ---: | ---: |
| 349 | 60.726 |
| 1.000 | 499.500 |
| 3.000 | 4.498.500 |

Bina ölçeğinde `exhaustive` kullanılamaz — işin püf noktası bu.

---

### 2. ADIM: 3D Gaussian Splatting (3DGS)

Sahneyi üçgenlerden (mesh) değil, **milyonlarca küçük renkli bulanık lekeden**
oluşturur. Her leke bir **3B Gaussian**'dır ve şu bilgileri taşır:

| Özellik | Sembol | Ne demek |
| :--- | :--- | :--- |
| Konum | μ (mü) | Lekenin uzaydaki yeri |
| Kovaryans | Σ (sigma) | Lekenin şekli: ne kadar yassı, hangi yöne dönük |
| Opaklık | α (alfa) | Ne kadar saydam |
| Renk | SH katsayıları | Bakış açısına göre değişen renk |

**SH (Spherical Harmonics / küresel harmonikler):** Rengin bakış açısına göre
değişmesini sağlayan matematiksel gösterim. Parlak bir masa yüzeyi farklı açıdan
farklı görünür — SH bunu modeller. `sh-degree` ne kadar yüksekse o kadar detaylı
ama o kadar çok bellek.

**Alfa bileştirme (alpha compositing):** Bir pikselin rengi, o pikselin arkasındaki
lekelerin öndekilerden başlayarak üst üste bindirilmesiyle bulunur. Öndeki opak
leke, arkadakini gizler. Buzlu camları üst üste koymak gibi.

**Rasterizasyon:** 3B lekeleri 2B ekran görüntüsüne çevirme işlemi. **gsplat** bunu
GPU'da yapan kütüphane.

---

### Eğitim nasıl oluyor?

```
SfM noktalarından başla
      ↓
Bir kamera seç, o açıdan görüntü üret
      ↓
Gerçek fotoğrafla karşılaştır  ← KAYIP (loss)
      ↓
Lekeleri düzelt: yerini, şeklini, rengini
      ↓
30.000 kez tekrarla
```

| Terim | Anlamı |
| :--- | :--- |
| **İterasyon** | Yukarıdaki döngünün bir turu |
| **Kayıp (loss)** | Üretilen görüntü gerçekten ne kadar farklı. L1 + SSIM karışımı |
| **Yoğunlaştırma (densify)** | Detayın yetmediği yerde lekeyi ikiye bölmek |
| **Budama (cull)** | Çok saydam, işe yaramayan lekeleri silmek |

---

### Denediğimiz ayarlar — raporun 2. deneyi

| Ayar | Ne yapar | Sonuç |
| :--- | :--- | :--- |
| **antialiased** rasterizasyon | Yakınlaşıp uzaklaşırken oluşan kenar bozulmasını düzeltir (Mip-Splatting makalesi) | **En iyi**, maliyeti %6 |
| **Ölçek düzenlemesi** | Lekelerin aşırı uzayıp iğneye dönüşmesini engeller | Fark yaratmadı |
| **Kamera pozu optimizasyonu (SO3xR3)** | COLMAP'in kamera konumlarını eğitim sırasında rötuşlar | Metrikler çöktü, **sahneyi kaydırdı** |
| **splatfacto-big** | Çok daha fazla Gaussian üretir | 2,3 kat büyük dosya, daha kötü sonuç |
| **Tam çözünürlük** | Görüntüleri küçültmeden eğitir | 2,4 kat süre, ölçülebilir kazanç yok |

**SO3xR3 neden tehlikeli:** Bu ayar eğitim kameralarının konumlarını değiştirir.
Model yeni, kaydırılmış bir koordinat sisteminde öğrenir. Test kameraları eski
sistemde kaldığı için görüntüler üst üste oturmaz. Raporun 5. şeklinde
görebilirsin: render **bulanık değil, kaymış**.

Bizim için kritik olan şu: erişilebilirlik ölçümü yapacaksak (kapı genişliği vb.),
modelin geometrisi ile kamera konumları **aynı koordinat sisteminde** kalmalı. Bu
ayar o sistemi bozuyor.

---

### Kalite ölçütleri

| Ölçüt | Ne ölçer | İyi olan |
| :--- | :--- | :--- |
| **PSNR** (dB) | Piksel piksel ne kadar benziyor | Yüksek. 27–28 dB iyi |
| **SSIM** | Yapısal benzerlik (kenarlar, dokular) | Yüksek. 1,0 mükemmel |
| **LPIPS** | İnsan gözüne ne kadar benziyor (sinir ağıyla) | **Düşük** |

**Train/test ayrımı:** Modelin hiç görmediği kareler ayrılır (bizde 331 karenin
33'ü). Metrikler bu karelerde ölçülür. Eğitimde gördüğü karelerle ölçüm yapmak,
öğrenciyi çalıştığı sorularla sınamak gibidir — gerçek başarıyı göstermez.

> Önceki oda raporlarında metrikler eğitim karelerinde ölçülmüştü; bu hafta
> düzelttik.

---

### Diğer terimler

| Terim | Anlamı |
| :--- | :--- |
| **VRAM** | Ekran kartının kendi belleği. Bizde 6 GB (RTX 2060) |
| **PLY** | Gaussian modelinin kaydedildiği dosya biçimi. SuperSplat ve Unity okur |
| **Floater** | Havada asılı kalan, hiçbir yüzeye ait olmayan yanlış leke |
| **NeRF** | 3DGS'ten önceki yöntem. Sahneyi sinir ağıyla temsil eder, yavaştır, Unity'ye aktarılamaz |
| **Metrik ölçek** | Modeldeki "1 birim" gerçekte kaç metre. Fotoğraftan **belirlenemez**, dışarıdan ölçü gerekir |
| **Checkpoint** | Eğitimin kaydedilmiş hâli; modeli sonradan açmayı sağlar |
| **Laplacian varyansı** | Bir karenin ne kadar net olduğunu ölçen sayı. Düşükse kare ya bulanıktır ya da dokusuz bir yüzeye bakıyordur (ikisini ayırmaz) |
| **Ablasyon** | Tek bir ayarı değiştirip etkisini ölçme yöntemi. Raporun 5.2 bölümü bir ablasyon çalışmasıdır |
| **Downscale / çözünürlük düşürme** | Eğitimi küçültülmüş görüntülerle yapmak. Hız ve bellek kazandırır, detay kaybettirir |
| **tiny-cuda-nn** | NeRF'in hızlı çalışması için gereken kütüphane. Kurmadan nerfacto 30 kat yavaş çalışıyordu |
| **transforms.json** | Nerfstudio'nun okuduğu kamera listesi dosyası. COLMAP çıktısından üretilir |
| **sparse/0, sparse/1** | COLMAP'in ürettiği model klasörleri. Birden fazla varsa sahne parçalanmış demektir; **en büyüğü `sparse/0` olmak zorunda değil** (raporun 4.2'sindeki hata buydu) |

---

## BÖLÜM 2 — Hocanın Sorabileceği Sorular

### S1. Büyük bir binayı nasıl çekeceksiniz, parça parça mı?

**Evet, parça parça.** Üç bağımsız sebebi var:

**1. COLMAP maliyeti karesel büyüyor.** Ölçtüğümüz rakamla: 349 kare = 60.726
karşılaştırma = 8 dakika eşleştirme. Bir kat yaklaşık 3.000 kare eder; bu 4,5
milyon karşılaştırma ve saatler demektir. Tek seferde yapılamaz.

**2. Sahne parçalanma riski.** Kare sayısı ve mekân karmaşıklığı arttıkça
COLMAP'in tek tutarlı model kuramama olasılığı yükseliyor. Bunu küçük ölçekte bile
gördük (R2 koşusu 79 fotoğrafta 3 parçaya ayrıldı). Kontrollü bölümlere ayırmak,
bu riski yönetilebilir hâle getirir.

**3. Literatür de bunu söylüyor.** VastGaussian [06] çalışması büyük sahneleri
hücrelere bölüp ayrı eğitip birleştiriyor. Bizim planımız da bu.

**Bölümleme nasıl olacak:** Koridor, derslik, merdiven sahanlığı gibi doğal
birimler. **Kritik kural:** bölümler arasında **ortak görünen alan bırakılmalı** —
iki bölümün aynı kapıyı, aynı koridor köşesini görmesi gerekiyor ki sonradan
ortak koordinat sisteminde hizalanabilsinler. Bunu bırakmazsak parçalar birbirine
bağlanmaz.

---

### S2. Çekimi nasıl yapacaksınız?

Bu haftanın deneylerinden çıkan somut çekim talimatı:

| Kural | Gerekçe |
| :--- | :--- |
| **Video, saniyede 1 kare alınacak şekilde** | 30 FPS'in tamamı gereksiz; paralaks için 0,5–1 m aralık gerekir |
| **Yürüyerek çek, sabit hızda** | Duraklamak aynı noktadan tekrarlı kare üretir: maliyet ekler, bilgi eklemez (ölçtük: medyan kamera mesafesi 0,0000) |
| **Yerinde dönme** | Sadece dönmek paralaks üretmez; öteleme şart |
| **Her yeri iki kez, farklı yönden geç** | Döngü kapanışı için; tek geçiş zinciri kopmaya açık |
| **0.5× geniş açı kullan** | Dar mekânda 1× kadraja sığmıyor; daha fazla örtüşme sağlar |
| **Yavaş hareket et** | Karelerin %9,7'si hareket bulanıklığı yüzünden sorunluydu |
| **Dokusuz beyaz duvara uzun süre bakma** | COLMAP dokusuz yüzeyde eşleşme bulamaz (FreeSplat [05] da bunu bildiriyor) |
| **Bölümler arası ortak alan bırak** | Hizalama için zorunlu |
| **Şeritmetreyle en az 3 mesafe ölç** | Metrik ölçek için tek yol |

---

### S3. Binayı eğitirken hangi yöntemleri kullanacaksınız?

Ölçümlerimizin verdiği yapılandırma:

| Karar | Seçim | Neden |
| :--- | :--- | :--- |
| Sahne temsili | **3DGS (Splatfacto)** | NeRF'e göre +4,74 dB, %24 hızlı, yarı bellek; ayrıca Unity'ye aktarılabilen tek seçenek |
| Rasterizasyon | **antialiased** | Üç metrikte de en iyi, maliyeti %6 |
| Kamera pozu optimizasyonu | **kapalı** | Ölçüm koordinat sistemini kaydırıyor |
| Gaussian bütçesi | **varsayılan** | `splatfacto-big` iki kat maliyete daha kötü sonuç verdi |
| İterasyon | **30.000** | 15.000'den 30.000'e çıkınca +0,67 dB kazanç ölçtük |
| Eşleştirme (oda ölçeği) | **exhaustive** | %94,8 kayıt, tek model |
| Eşleştirme (bina ölçeği) | **henüz ölçülmedi** | `exhaustive` ölçeklenmiyor; `vocab_tree` veya döngü kapanışlı `sequential` denenmeli |

Son satır dürüstçe açık bırakılmalı: 349 karede `vocab_tree`'nin avantajı
çıkmadı, ama bu onun bina ölçeğinde kötü olduğunu **göstermez** — sadece kesişim
noktasının 349 karenin üzerinde olduğunu gösterir. Bir sonraki deney bu.

---

### S4. Mevcut donanım yetiyor mu? Bulut gerekiyor mu?

**VRAM yetiyor, hız yetmiyor.**

En ağır koşumuz 4.889 MB kullandı; 6.144 MB'nin %80'i. Hiçbir koşuda bellek
taşması olmadı, tam çözünürlükte bile. Yani "daha büyük VRAM lazım" demek yanlış
olur.

Asıl darboğazlar:
1. **COLMAP eşleştirme süresi** (karesel büyüyor)
2. **Sistem RAM'i** (görüntü önbelleği için — VRAM değil)
3. **Sahne parçalanma riski**

Colab veya daha güçlü bir GPU'nun faydası **bellek değil hız** olacak. Somut bir
hızlanma oranı ölçmedik, o yüzden sayı vermiyoruz.

> Not: Önceki oda denemelerinde VRAM'e sıkışmamızın sebebi 12 megapiksellik
> fotoğraflardı. Video karesi 2 megapiksel, yani altı kat hafif.

---

### S5. Neden NeRF değil de 3DGS?

İki ayrı gerekçe:

**Ölçülen:** Aynı veri, aynı iterasyonla nerfacto (NeRF) her ölçütte geride kaldı
— PSNR 22,48'e karşı 27,22; LPIPS iki kat kötü; eğitim %24 daha yavaş; bellek 1,9
kat.

**Yapısal:** Unity görüntüleyicisi ve VR hattı Gaussian temsili gerektiriyor. NeRF
modeli `.ply` olarak dışa aktarılamıyor ve gerçek zamanlı render edilemiyor.
Projenin A5 aşaması (VR gösterimi) NeRF ile mümkün değil.

İkincisi birincisinden daha belirleyici: NeRF daha iyi olsa bile kullanamazdık.

---

### S6. Modelden kapı genişliğini ölçebiliyor musunuz?

**Hayır, henüz değil** — ve bu raporun bilinçli olarak öne çıkardığı eksik.

Fotoğraftan üretilen modelin **metrik ölçeği belirsizdir**: modeldeki "1 birim"in
kaç metre olduğu bilinmez. Çözümü dışarıdan ölçü getirmektir — mekânda
şeritmetreyle ölçülmüş birkaç referans mesafe.

Bir mesafe ölçekle_mek_ için, diğerleri **hatayı kontrol etmek** için kullanılır.
Tek mesafeyle ölçek kurmak modelin tamamının doğru olduğunu kanıtlamaz.

Bu yüzden görüşmeden önce (veya hemen sonra) dersliğe girip 3 ölçü almak en
öncelikli iş.

---

### S7. Üstten görünüm / kat planı çıkarabilir misiniz?

**Bu çekimden hayır.** Denedik, çalışmadı — ve nedeni öğretici:

Gaussian lekeleri, çekim yönüne göre yassı diskler hâlinde oluşuyor. Tam tepeden
bakınca bu disklerin kenarlarını görüyoruz ve görüntü iğne yığınına dönüşüyor.
Tavanı kırpıp denedik, yine olmadı.

**Bunun projeye anlamı büyük:** görsel katman, ölçüm katmanının yerine geçemez.
Erişilebilirlik ölçümü için ayrı bir geometri katmanı gerekiyor — COLMAP'in yoğun
eşleştirmesi (MVS) veya yüzey çıkarımı. Tasarım raporumuzdaki "görsel ve fiziksel
katmanın ayrılması" kararı (K01) tam olarak bu yüzden doğru çıktı.

---

### S8. Bu hafta ne öğrendiniz, en önemli üç şey?

1. **Örtüşme, kare sayısından önemli.** İz uzunluğu 3 olunca sahne parçalanıyor,
   8 olunca tek parça çıkıyor. Bina çekim planını bu belirleyecek.
2. **Düşük piksel hatası kaliteyi göstermiyor.** En düşük hatalı koşu, kullanılamayan
   tek koşuydu.
3. **Görsel kalite ile ölçüm ayrı şeyler.** Kamera optimizasyonu görüntüyü
   iyileştirirken ölçüm çerçevesini bozuyor; üstten görünüm hiç alınamıyor.

---

## BÖLÜM 3 — Görüşmede Anlatım Sırası

Hoca "ne yaptınız" diye sorduğunda üç dakikalık akış:

**1. Ne yaptık (30 sn).**
"Derslikte bir video çektik, 349 kare çıkardık ve aynı veri üzerinde 12 koşu
yaparak hangi yöntemin daha iyi olduğunu ölçtük. Amacımız bina ölçeğine geçmeden
önce doğru yöntemi seçmekti."

**2. Nasıl karşılaştırdık (30 sn).**
"Her koşuda tek bir ayarı değiştirdik ve hepsinde aynı COLMAP çıktısını kullandık.
Metrikleri modelin hiç görmediği 33 kare üzerinde ölçtük."

**3. Ne bulduk (1 dk).**
"Eşleştirme stratejisi en kritik karar: ardışık eşleştirme videonun %57'sini
kaybediyor ve sahneyi dörde bölüyor. Tam eşleştirme %94,8 başarıyla tek model
üretiyor ama maliyeti kare sayısının karesiyle büyüdüğü için bina ölçeğinde
kullanılamaz. Eğitim tarafında kenar yumuşatma %6 maliyetle en iyi sonucu verdi;
kamera pozu optimizasyonu ise ölçüm koordinat sistemini kaydırdığı için bizim
işimizde riskli."

**4. Sırada ne var (30 sn).**
"Metrik ölçek için dersliğe girip şeritmetreyle üç referans mesafe alacağız —
bu olmadan kapı genişliği gibi erişilebilirlik ölçüleri üretemeyiz. Ardından bina
ölçeği için döngü kapanışlı eşleştirme stratejisini ölçeceğiz ve Unity aktarımına
geçeceğiz."

### Ezberlenecek sayılar

| Sayı | Ne |
| ---: | :--- |
| 349 | Kullanılan kare (10.459 ham kareden) |
| 331 / %94,8 | Tam eşleştirmede kaydolan kare |
| 149 / %42,7 | Ardışık eşleştirmede kaydolan (4 parçaya bölündü) |
| 28,05 dB | En iyi modelin test PSNR'ı |
| 566.064 | Gaussian sayısı · 134 MiB dosya |
| 4.889 MB | En yüksek VRAM (6.144 MB'nin %80'i) |
| +4,74 dB | 3DGS'in NeRF'e üstünlüğü |
| 4,5 milyon | Bir katta (~3.000 kare) gereken karşılaştırma sayısı |

### Soru gelirse "bilmiyoruz" denecek yerler

Bunları savunmaya çalışma, dürüstçe söyle — raporun güvenilirliği buradan geliyor:

* Bina ölçeğinde hangi eşleştirme stratejisinin kazanacağını **ölçmedik**.
* Metrik ölçek **kurulmadı**, dolayısıyla hiçbir metrik erişilebilirlik ölçüsü yok.
* R1 koşusundaki geometri çökmesinin kök nedeni **ayrıştırılamadı**.
* Unity aktarımı (A2) **yapılmadı**, kare süresi ölçülmedi.
