# Hafta 4 — COLMAP Yöntemlerinin Karşılaştırılması ve Bina Ölçeği İçin Öneriler

**Proje:** Engelli Bireyler İçin Akıllı Erişilebilir Rota Planlama · **Aşama:** A1 — Mekân modelleme

**Hazırlayanlar:** Sabri Duruk, Yunis Teymurlu · **Danışman:** Öğr. Gör. Koray AKİ

---

## 1. Amaç

Bu hafta COLMAP'in yöntem ailesi aynı veri ve aynı donanımda karşılaştırıldı:

* **Özellik çıkarma ve eşleştirme:** SIFT, ALIKED + LightGlue, LoMa
* **Eşleştirme stratejisi:** exhaustive, sequential, sequential + döngü tespiti, vocab_tree
* **Seyrek rekonstrüksiyon (SfM):** incremental, global, hierarchical
* **Yoğun rekonstrüksiyon:** PatchMatch Stereo, stereo fusion, Poisson ve Delaunay yüzey

Her SfM çıktısının son modele etkisi 3DGS ile ölçüldü. Proje ileride çok katlı
bir binayı modelleyeceği için her sonuç şu soruya bağlandı: *bu yöntem binlerce
karelik bir çekimde işe yarar mı, ne kadar sürer, nerede bozulur?*

---

## 2. Yöntemler

```text
Kareler → Özellik çıkarma → Eşleştirme      → SfM                 → 3DGS (görsel model)
          SIFT / ALIKED /    strateji +       incremental /           Dense (ölçülebilir yüzey)
          LoMa               RANSAC doğrulama global / hierarchical
```

**Özellik çıkarma** her karede tanınabilir noktalar ve bu noktaları tarif eden
tanımlayıcılar üretir.

| Yöntem | Çalışma biçimi |
| :--- | :--- |
| SIFT | El tasarımı. Farklı ölçeklerde Gauss farkının uç noktaları anahtar nokta olur; çevredeki gradyan yönleri 128 boyutlu tanımlayıcıya dönüşür. |
| ALIKED | Öğrenme tabanlı hafif evrişimli ağ; deforme edilebilir örnekleme ile perspektif değişimine uyum sağlar (128 boyut). Eşleştirici: LightGlue, iki karedeki noktaları dikkat katmanlarıyla birlikte değerlendiren sinir ağı. |
| LoMa | COLMAP 4.2'de eklenen öğrenme tabanlı paket: dedektör ağı + DeDoDe-G tanımlayıcısı (DINOv2 omurgalı, 256 boyut) + kendi eşleştirici ağı. |

**Eşleştirme**, hangi kare çiftlerinin karşılaştırılacağını seçer. Her çift
RANSAC ile geometrik olarak doğrulanır.

| Strateji | Hangi çiftler? | Çift sayısının büyümesi |
| :--- | :--- | :--- |
| exhaustive | Tüm çiftler | Karesel: N(N−1)/2 |
| sequential | Çekim sırasındaki yakın kareler | Doğrusal |
| sequential + loop | sequential + her 10 karede "burayı daha önce gördüm mü?" araması (sözlük ağacıyla döngü kapatma) | Doğrusal |
| vocab_tree | Her kare için görsel olarak en benzer 100 kare | Doğrusal |
| spatial | GPS'e göre yakın kareler | Uygulanamadı: video karelerinde konum bilgisi yok |

**SfM**, kameraları ve 3B noktaları uzaya yerleştirir.

| Yöntem | Çalışma biçimi | Güçlü / zayıf yanı |
| :--- | :--- | :--- |
| incremental | Kareler tek tek eklenir; her adımda tüm model yeniden iyileştirilir (bundle adjustment). | En sağlam; büyük veride yavaş |
| global (GLOMAP) | Tüm kameraların önce yönleri, sonra konumları aynı anda çözülür. | Çok hızlı; yanlış bir eşleşme tüm çözüme yayılabilir |
| hierarchical | Sahne parçalara bölünür, parçalar paralel kurulup birleştirilir. | Büyük sahneler için; birleşim yerleri kopabilir |

> Varsayılan hierarchical ayarı 500 karenin altında sahneyi bölmez; 349 karede
> incremental ile aynı sonucu verdiği ölçülerek doğrulandı. Yöntemin gerçekten
> çalışması için parça boyutu 100 kareye indirildi (leaf=100).

**Dense** aşaması SfM pozlarını kullanarak her pikselin derinliğini bulur
(PatchMatch), derinlikleri yoğun bir nokta bulutunda birleştirir (fusion) ve
yüzey üretir (Poisson / Delaunay). 3DGS görüntü üretir ama ölçülebilir bir yüzey
değildir; kapı, koridor, eğim ölçümleri dense çıktısı üzerinden yapılacaktır.

---

## 3. Deney Düzeni

| Sabit tutulan | Değer |
| :--- | :--- |
| Veri | D207 dersliği, 349 kare (1080×1920) |
| Donanım | RTX 2060 6 GB · Ryzen 5 3500X · 16 GB RAM · Windows 11 |
| Yazılım | COLMAP 4.2.1 (CUDA), tüm ayarlar varsayılan, sabit rastgele tohum |
| 3DGS | Splatfacto, varsayılan ayarlar, 30.000 iterasyon |
| Test kareleri | Her 10. kare (34 kare), hiçbir eğitime girmez |
| Ölçüm | Her aşamada süre, tepe RAM ve tepe VRAM |

* Her kombinasyon **bir kez** koşuldu; özellik çıkarma ve eşleştirme bir kez
  yapılıp sonraki aşamalarda paylaşıldı. Aynı sonucu verecek işlem tekrarlanmadı.
* 3DGS üç çıkarıcıda aynı 6 kombinasyonda eğitildi: {exhaustive, sequential,
  sequential + loop} × {incremental, global}.
* **Bina ölçeği vekili (vocab_tree k=7):** 349 karede 100 aday verinin %29'udur
  ve neredeyse exhaustive gibi davranır. 5.000 karelik bir binada 100 aday ~%2'ye
  denk gelir. Bu oranı burada üretmek için vocab_tree 7 adayla da koşuldu.

**Doğruluk ölçütü — "doğru pozlanan kare".** Kayıt oranı ve yeniden izdüşüm
hatası, modelin doğru olup olmadığını göstermez (bölüm 4.2). Bu nedenle her
modelin kameraları bir **referans geometriye** hizalandı ve kamerası referansla
örtüşen kareler sayıldı (sahne ölçeğinin %5'i içinde). Sonuç tek bir sayıdır:
**349 karenin yüzde kaçı hem modele girdi hem doğru yerde?**

Referans: LoMa + exhaustive + incremental. 349 karenin tamamını kapsar ve tamamen
farklı özellik kullanan SIFT + exhaustive + incremental ile bağımsız olarak
kameraların %99,7'sinde örtüşür. İki ayrı hattın aynı geometride buluşması, referansın doğru
olduğunu destekler.

---

## 4. Sonuçlar

### 4.1 SfM doğruluğu

![Şekil 1 — Doğru pozlanan kare oranı (349 karenin %'si). Koyu = sahnenin büyük kısmı doğru kuruldu. N/A: koşulamadı (bölüm 6).](../figures/hafta-04/sekil_h4_2_sfm_matrisi.png)

* **SIFT:** exhaustive ve vocab_tree, incremental ile 349 karenin %94–95'ini doğru
  kuruyor. sequential tek başına sahnenin üçte birinde kalıyor; global ile tek
  parçaya birleşen model %44'te.
* **ALIKED + LightGlue:** incremental ve global'de kayıt oranı %96–100 olmasına
  rağmen doğru pozlanan kare çoğunlukla %18–60. En iyileri sequential + loop +
  incremental ve vocab_tree + hierarchical (%84).
* **LoMa:** exhaustive ve sequential, incremental ve hierarchical ile %97–100;
  global ile %62–84.
* **Global** her çıkarıcıda incremental'ın gerisinde. **Hierarchical (leaf=100)**
  SIFT'te parçalanıyor, LoMa'da %97'ye ulaşıyor.

### 4.2 Temel kombinasyonlarda SfM ölçütleri

| Çıkarıcı + kombinasyon | Modele giren kare | Doğru pozlanan kare (%) | Kopuk kamera | Seyrek nokta | İz uzunluğu | Yeniden izdüşüm hatası (px) | Toplam süre (dk) | 3DGS PSNR (dB) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SIFT exhaustive + incremental | 331 | 94,6 | 0 | 70.199 | 5,03 | 0,70 | 43,3 | 28,26 |
| SIFT sequential + incremental | 148 | 32,7 | 0 | 24.958 | 4,54 | 0,61 | 6,6 | 27,06 (a) |
| SIFT sequential + global | 338 | 43,6 | 21 | 41.423 | 4,58 | 0,62 | 5,1 | 19,44 |
| ALIKED exhaustive + incremental | 346 | 43,8 | 3 | 92.915 | 4,97 | 0,98 | 133,1 | 18,99 |
| ALIKED sequential + loop + incremental | 343 | 84,5 | 0 | 74.156 | 5,08 | 0,94 | 25,8 | 25,11 |
| LoMa exhaustive + incremental | 349 | 100 (referans) | 0 | 94.256 | 5,48 | 1,26 | 223,9 | 27,81 |
| LoMa sequential + incremental | 346 | 98,9 | 1 | 75.918 | 4,84 | 1,12 | 119,8 | 27,64 |

(a) Yalnızca modelin kapsadığı 14 test karesinde. Odanın yarısından fazlası modelde yok.
Tüm 39 SfM koşusunun aynı ölçütleri `sfm_runs.csv` dosyasındadır.

SIFT sequential + incremental, kurduğu bölgede iyi ama sahneyi 8 parçaya bölüyor.
SIFT sequential + global aynı eşleşmelerden tek parça model kuruyor; kayıt oranı
en yüksek, yeniden izdüşüm hatası en düşük, ancak 349 karenin yalnız %44'ü doğru
yerde. ALIKED exhaustive de 346 kareyi modele alıyor ama yalnız %44'ü doğru.
Öğrenme tabanlı yöntemlerin izdüşüm hatası SIFT'ten yüksektir (0,9–1,3 px) ama bu
geometri kalitesini belirlemiyor: LoMa en yüksek hatayla en doğru modeli kurdu.
**Kayıt oranı ve izdüşüm hatası tek başına yanıltıcıdır.**

### 4.3 Yanlış geometri nasıl görünüyor?

![Şekil 2 — Üstten görünüş: modeller referansa hizalandı. Gri: seyrek noktalar (zemin ve tavan çıkarıldı), renkli: kamera konumları (çekim sırası). Doğru modelde üç sıra dizisi ve kamera yolu referansla örtüşüyor. ALIKED'de oda kendi üstüne katlanmış, sıralar üst üste binmiş; SIFT sequential + global'de çekimin bir bölümü yanlış yere eklenmiş ve kopuk kameralar var.](../figures/hafta-04/sekil_h4_6_kamera_yerlesimi.png)

**Neden?** ALIKED + LightGlue, SIFT'in 3 katı çift doğruladı (31.065'e 10.850).
Bunların 999'u SIFT'in hiç bağlamadığı, zaman olarak çok uzak ama ≥100 eşleşmeli
"güçlü" çiftlerdir. Örneğin 196 sn arayla çekilmiş iki kare 497 eşleşme ile
bağlandı. Dersliğin tekrar eden yapısı (aynı sıralar, aynı pencereler) yanlış
eşleşmeleri geometrik doğrulamadan geçirdi. SIFT + sequential + global'de ise
kopuk sequential zinciri, global çözücü tarafından yanlış yerden birleştirildi.

### 4.4 3DGS kalitesi

**3DGS test PSNR (dB)** — görülmemiş test karelerinde; yüksek değer iyidir.

| SfM kombinasyonu | SIFT | ALIKED + LightGlue | LoMa |
| :--- | ---: | ---: | ---: |
| exhaustive + incremental | **28,26** | 18,99 | **27,81** |
| exhaustive + global | 28,15 | 15,23 | 23,77 |
| sequential + incremental | 27,06 (a) | 17,88 | **27,64** |
| sequential + global | 19,44 | 17,07 | 17,96 |
| sequential + loop + incremental | 22,41 | 25,11 | N/A (b) |
| sequential + loop + global | 23,37 | 19,89 | N/A (b) |

(a) Yalnızca modelin kapsadığı 14 test karesinde. (b) LoMa için sözlük ağacı kurulamadı (bölüm 6). SSIM ve LPIPS aynı sıralamayı verir; tüm değerler `gs_summary.csv` dosyasındadır.
Eğitim süresi 16–21 dk, tepe VRAM 1,7–2,8 GB'dir.

![Şekil 3 — Aynı test karesi, farklı SfM çıktılarıyla eğitilen 3DGS. Doğru geometride sıralar ve pencere keskin; yanlış geometride nesneler dağılıyor.](../figures/hafta-04/sekil_h4_4_render_karsilastirma.jpg)

![Şekil 4 — Doğru pozlanan kare oranı ile 3DGS kalitesi; her panel bir çıkarıcı, her nokta 3DGS eğitilen bir SfM kombinasyonu (exh: exhaustive, seq: sequential, inc: incremental, glob: global). SfM'in geometrik doğruluğu arttıkça 3DGS kalitesi de artıyor.](../figures/hafta-04/sekil_h4_1_dogruluk_psnr.png)

### 4.5 Kopuk kameralar

Global mapper bazı kareleri sahneden çok uzağa yerleştiriyor (bir örnekte kameraların
medyan uzaklığının yaklaşık 200.000 katı). 3DGS sahneyi en uzak kameraya göre ölçeklediği için tek bir kopuk
kamera bütün modeli bozuyor. Bu kameralar eğitimden önce otomatik olarak
ayıklandı (en yakın 3 kameraya uzaklığı medyanın 10 katını aşan kamera); bölüm
4.4'teki tüm sonuçlar ayıklanmış veriyle alınmıştır.

![Şekil 5 — SIFT exhaustive + global: kopuk 6 kamera eğitimde kalınca model çöküyor, ayıklanınca referansla aynı kaliteye çıkıyor.](../figures/hafta-04/sekil_h4_7_kopuk_kamera_etkisi.jpg)

### 4.6 Zayıf dokulu yüzeyler

Boş duvar, tahta, tavan ve zemin gibi dokusuz yüzeyler binada sık görülür.
Yeni çekim yapılmadan aynı 349 kare iki gruba ayrıldı: alanının en az %60'ı
dokusuz olan **45 zayıf dokulu kare** ve geri kalan 304 normal kare (dokusuz
alan: 32×32 piksellik bloklarda parlaklık standart sapması 4 gri düzeyin
altında). Her çıkarıcının mevcut çıktıları bu iki grupta ölçüldü.

| Ölçüt | SIFT | ALIKED + LightGlue | LoMa |
| :--- | ---: | ---: | ---: |
| Kare başına anahtar nokta, normal kare | 8.154 | 2.011 | 2.048 |
| Kare başına anahtar nokta, zayıf dokulu kare | 3.513 | 1.379 | 2.048 |
| Zayıf dokulu karede anahtar noktaların dokusuz bölgeye düşen oranı (%) | 4,2 | 9,7 | 27,3 |
| Komşu karelerle doğrulanmış eşleşme, zayıf dokulu kare | 170 | 504 | 627 |
| Aynı değer, normal karenin yüzdesi olarak (%) | 26 | 56 | 69 |
| Modele giren zayıf dokulu kare (%) | 82,2 | 97,8 | 100 |
| Kare başına 3B noktaya dönüşen gözlem, zayıf dokulu kare | 296 | 729 | 1.056 |
| Bunlardan dokusuz bölgede olan, kare başına | 4,5 | 21,8 | 149,5 |

Eşleşme sayıları sequential eşleştirmeden, modele giriş ve 3B gözlemler
exhaustive + incremental modelinden alınmıştır (her çıkarıcı için aynı strateji).

![Şekil 6 — Alanının %83'ü dokusuz olan bir kare (frame_0343). Beyaz: anahtar noktalar; renkli: 3B noktaya dönüşenler. SIFT ve ALIKED askılık ve sandalye gibi dokulu nesnelere yoğunlaşıyor; LoMa duvar yüzeyinde de nokta bulup kullanabiliyor.](../figures/hafta-04/sekil_h4_8_zayif_doku.jpg)

**Sonuç:** Zayıf dokulu karelerde SIFT eşleşmelerinin dörtte üçünü kaybediyor
ve bu karelerin %18'ini modele alamıyor; SIFT'in kaydedemediği 18 karenin 8'i
zayıf dokulu karelerdir. ALIKED + LightGlue bu karelerde SIFT'ten belirgin
biçimde daha iyi (eşleşmelerin %56'sını koruyor, %98'ini modele alıyor), yani
dokusuz yüzeyde öğrenme tabanlı yöntemin avantajı bu veride doğrulandı. Ancak
aynı yöntem tekrar eden yapıda yanlış eşleşme ürettiği için (bölüm 4.3) genel
geometride SIFT'in gerisinde kaldı. LoMa her iki durumda da en iyisi: zayıf
dokulu karelerin tamamını modele aldı ve duvar yüzeyinde de 3B nokta üretti.
Dokusuz kareler render edilmesi kolay olduğu için 3DGS PSNR bu karşılaştırmada
ayırt edici değildir ve kullanılmamıştır.

### 4.7 Dense rekonstrüksiyon

| Kaynak SfM | Toplam süre (dk) | Yoğun nokta (milyon) | Poisson yüzey (milyon üçgen) | Delaunay yüzey (bin üçgen) | Tepe RAM (GB) | Tepe VRAM (GB) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| SIFT exhaustive + incremental | 92,7 | 1,65 | 8,45 | 482 | 4,0 | 0,8 |
| LoMa exhaustive + incremental | 98,3 | 1,89 | 9,87 | 540 | 4,2 | 0,8 |

Kareler 1000 piksele küçültülmüştür. Sürenin %95'i PatchMatch'tir ve kare sayısıyla
doğrusal büyür (~15 sn/kare). ALIKED dense'i de koşuldu, ancak kaynak geometrisi
hatalı olduğu için tabloya alınmadı.

![Şekil 7 — SIFT dense nokta bulutunun üstten görünüşü (zemin ve tavan çıkarıldı). Sıra dizilimi, kürsü ve duvarlar okunabiliyor; 3DGS'ten elde edilemeyen kat planı görünümü dense ile elde edildi.](../figures/hafta-04/sekil_h4_5_dense_ust_gorunus.jpg)

### 4.8 Süre ve sistem gereksinimi

**Özellik çıkarma ve eşleştirme süresi (dakika, 349 kare)**

| Aşama | SIFT | ALIKED + LightGlue | LoMa |
| :--- | ---: | ---: | ---: |
| Özellik çıkarma | 0,3 | 6,5 | 107,1 |
| Eşleştirme: exhaustive | 37,4 | 114,2 | 103,8 |
| Eşleştirme: sequential | 2,5 | 6,4 | 5,5 |
| Eşleştirme: sequential + loop | 5,4 | 9,8 | N/A (b) |
| Eşleştirme: vocab_tree | 22,3 | 42,2 | N/A (b) |
| Eşleştirme: vocab_tree k=7 | 3,7 | 3,2 | N/A (b) |

**SfM ve uçtan uca süre (dakika, 349 kare).** Toplam = özellik çıkarma + eşleştirme + SfM.

| Eşleştirme + SfM | SIFT: SfM (dk) | SIFT: toplam (dk) | ALIKED: SfM (dk) | ALIKED: toplam (dk) | LoMa: SfM (dk) | LoMa: toplam (dk) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| exhaustive + incremental | 5,7 | 43,3 | 12,3 | 133,1 | 13,0 | 223,9 |
| exhaustive + global | 2,5 | 40,2 | 1,4 | 122,2 | 1,0 | 211,9 |
| exhaustive + hierarchical (leaf=100) | 4,3 | 41,9 | 6,6 | 127,4 | 6,9 | 217,8 |
| sequential + incremental | 3,8 | 6,6 | 15,0 | 28,0 | **7,1** | **119,8** |
| sequential + global | 2,3 | 5,1 | 1,7 | 14,7 | 1,4 | 114,0 |
| sequential + hierarchical (leaf=100) | 2,4 | 5,2 | 6,9 | 19,8 | 3,6 | 116,3 |
| sequential + loop + incremental | 4,8 | 10,5 | 9,5 | 25,8 | N/A (b) | N/A (b) |
| sequential + loop + global | 2,2 | 7,9 | 1,5 | 17,9 | N/A (b) | N/A (b) |
| sequential + loop + hierarchical (leaf=100) | 9,6 | 15,3 | 5,1 | 21,4 | N/A (b) | N/A (b) |
| vocab_tree + incremental | 5,3 | 27,9 | 10,0 | 58,8 | N/A (b) | N/A (b) |
| vocab_tree + global | 1,9 | 24,5 | 1,3 | 50,0 | N/A (b) | N/A (b) |
| vocab_tree + hierarchical (leaf=100) | 3,7 | 26,3 | 6,7 | 55,5 | N/A (b) | N/A (b) |
| vocab_tree k=7 + incremental | 2,6 | 6,6 | 5,7 | 15,5 | N/A (b) | N/A (b) |
| vocab_tree k=7 + global | 1,8 | 5,7 | 2,0 | 11,8 | N/A (b) | N/A (b) |
| vocab_tree k=7 + hierarchical (leaf=100) | 1,8 | 5,8 | 4,0 | 13,8 | N/A (b) | N/A (b) |

Önerilen LoMa + sequential + incremental toplam 119,8 dk sürdü: 107,1 dk özellik çıkarma, 5,5 dk eşleştirme, 7,1 dk SfM. LoMa'da süreyi çıkarma belirliyor; SIFT ve ALIKED'de ise exhaustive eşleştirme. Global SfM, incremental'dan 2–13 kat hızlı ama doğruluğu düşük (bölüm 4.1). (b) LoMa için sözlük ağacı kurulamadı.

**Kaynak kullanımı (ölçülen tepe değerler; 1 GB = 1.024 MiB)**

| | SIFT | ALIKED + LightGlue | LoMa |
| :--- | ---: | ---: | ---: |
| Kare başına çıkarma (sn) | 0,05 | 1,1 | 18,4 |
| Çift başına eşleştirme (ms) | 37 | 113 | 103 |
| VRAM, çıkarma (GB) | 2,1 | 5,6 | 5,7 |
| RAM, çıkarma (GB) | 0,2 | 5,2 | 8,6 |
| RAM, SfM (GB) | 1,3 | 1,2 | 1,5 |
| Önerilen asgari donanım | 4 GB VRAM, 8 GB RAM | 6 GB VRAM, 16 GB RAM | 8 GB VRAM (6 GB sınırda), 16 GB RAM |

3DGS eğitimi tüm koşularda 2,8 GB VRAM ve 1,9 GB RAM altında kaldı; dense en fazla
0,8 GB VRAM ve 4,2 GB RAM kullandı. Darboğaz bellek değil, **öğrenme tabanlı çıkarma ve
exhaustive eşleştirme süresidir**.

### 4.9 Bina ölçeğine kestirim

Ölçülen birim maliyetlerle yalnızca **çıkarma + eşleştirme** süresi. Exhaustive
için N(N−1)/2 çift, diğerleri için kare başına ölçülen sabit çift sayısı
kullanıldı. SfM süresi kestirilmedi (doğrusal büyümez). (b) LoMa için sözlük ağacı kurulamadı.

| Strateji | SIFT, 1.000 kare (saat) | SIFT, 5.000 kare (saat) | ALIKED, 1.000 kare (saat) | ALIKED, 5.000 kare (saat) | LoMa, 1.000 kare (saat) | LoMa, 5.000 kare (saat) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| exhaustive | 5,1 | 128 | 16,0 | 393 | 19,3 | 382 |
| vocab_tree | 1,1 | 5,4 | 2,3 | 11,7 | N/A (b) | N/A (b) |
| sequential + loop | 0,3 | 1,4 | 0,8 | 3,9 | N/A (b) | N/A (b) |
| sequential | 0,1 | 0,7 | 0,6 | 3,1 | 5,4 | 26,9 |

![Şekil 8 — Kare sayısına göre çıkarma + eşleştirme süresi (log-log, saat). Kesikli çizgi: 1 gün.](../figures/hafta-04/sekil_h4_3_olcek_kestirimi.png)

---

## 5. Bulgular

1. **Kaliteyi geometrik doğruluk belirliyor, kayıt oranı değil.** Kayıt oranı
   %95'in üstünde olan birçok model yanlış geometri kurdu. Doğru pozlanan kare
   oranı ile 3DGS kalitesi neredeyse doğrusal ilişkili (Şekil 4).
2. **ALIKED + LightGlue tekrar eden mekânda yanlış eşleştiriyor.** Oda katlandı
   (Şekil 2). Aday çiftleri yerele sınırlayan sequential + loop'ta sonuç düzeldi
   (25,11 dB). Binada benzer koridor ve sınıflar bu riski büyütür.
3. **LoMa, ucuz eşleştirmeyle tam kalite veren tek yöntem.** sequential +
   incremental ile 27,64 dB; exhaustive (27,81 dB) ile aynı düzeyde, eşleştirmesi
   19 kat daha kısa. Bedeli, kare başına 18 sn süren özellik çıkarma.
4. **Global mapper her çıkarıcıda kopuk kamera üretiyor** (12 global koşunun
   12'sinde 1–37 kopuk kamera; incremental'da çoğunlukla 0–1). Ayıklama adımı
   bina hattında zorunlu olmalı; ucuz eşleştirmelerde global, incremental'ın
   gerisinde kaldı.
5. **Hierarchical'ın parçaları ancak eşleşme güçlüyse birleşiyor.** SIFT'te
   leaf=100 sahneyi 6–14 parçaya böldü; LoMa'da 2–5 parçayla %97 doğruluk.
6. **vocab_tree kaliteyi koruyor ama bina ölçeğinde kapsam kaybediyor.** SIFT +
   vocab_tree + incremental exhaustive ile aynı geometriyi %36 daha kısa sürede
   kurdu. Vekil deneyde (k=7) kayıt %94'ten %81'e düştü.
7. **Zayıf dokulu yüzeyde öğrenme tabanlı yöntemler SIFT'ten iyi.** Dokusuz
   karelerin SIFT'te %82'si, ALIKED'de %98'i, LoMa'da %100'ü modele girdi
   (bölüm 4.6). Beyaz duvarlı koridorlarda SIFT kare kaybedecektir.
8. **Dense ölçülebilir geometri veriyor.** Kat planı görünümü elde edildi
   (Şekil 7); erişilebilirlik ölçümleri dense / mesh üzerinden yapılmalı.

---

## 6. Koşulamayanlar ve Sınırlılıklar

| Konu | Durum |
| :--- | :--- |
| LoMa + sözlük ağacı stratejileri | N/A (9 SfM, 2 3DGS). COLMAP'in sözlük ağacı aracı yalnızca 128 boyutlu tanımlayıcı destekliyor; LoMa 256 boyutlu olduğu için araç çöküyor. Ağaç COLMAP'in Python arayüzüyle de kurulmaya çalışıldı, tek çekirdekte 67 dakikada tamamlanmadığı için süre sınırında durduruldu. |
| spatial eşleştirme | Video karelerinde GPS bilgisi yok |
| Referans ölçüden sapma | Derslikte şerit metre ölçüsü bekleniyor |

* Tek mekân, tek çekim; bina davranışı vekil deneyle öngörüldü, ölçülmedi.
* Zayıf dokulu yüzey karşılaştırması aynı çekimin dokusuz karelerinden yapıldı;
  tamamen dokusuz uzun bir koridor ayrıca çekilmedi.
* Her kombinasyon tek koşu; birbirine çok yakın sonuçlar (ör. 28,26 ve 28,15 dB)
  arasındaki fark anlamlı sayılmamalı.
* Referans geometri ölçülmüş bir gerçek değer değil, iki bağımsız hattın
  uzlaştığı modeldir. Metrik ölçek henüz yoktur.
* Süreler RTX 2060'a aittir; daha güçlü bir GPU'da özellikle ALIKED / LoMa
  süreleri kısalır (bölüm 7.3). Doğruluk sonuçları donanımdan bağımsızdır.

---

## 7. Bina Ölçeği İçin Öneriler

### 7.1 Bina nasıl bölünmeli: tek parça mı, kat kat mı, oda oda mı?

| Bölme | Artısı | Eksisi | Karar |
| :--- | :--- | :--- | :--- |
| Tüm bina tek SfM | Tek koordinat sistemi | 5.000+ karede exhaustive imkânsız (128–393 sa); tek bir yanlış eşleşme tüm binayı bozar | Hayır |
| **SfM kat kat** | Kat içinde oda ve koridorlar aynı koordinatta; 1.000–2.000 kare yönetilebilir | Katların birbirine hizalanması gerekir | **Evet** |
| SfM oda oda | Küçük ve hızlı | Oda–koridor–kapı bağlantısı kopar; her oda ayrıca hizalanmalı; parça birleştirme zayıf eşleşmede başarısız (bulgu 5) | Hayır |
| **3DGS bölge bölge** | Oda / koridor parçası başına ~300 kare, ~20 dk, ~0,6 M Gaussian (bu deney); VR'da parça parça yüklenebilir | Parça sınırlarında dikiş görünebilir | **Evet** |

**Önerilen yapı: SfM kat kat, 3DGS bölge bölge.** Rota planlaması kapı ve geçiş
eşiklerinin oda ile koridor arasında *aynı koordinatta* olmasını gerektirir. Bu
nedenle kamera pozları bütün kat için tek seferde çözülmeli (kat başına bir SfM).
Bir dersliğin 3DGS modeli ~0,6 milyon Gaussian ve ~135 MB'tır; 10 odalı bir kat
tek modelde ~6 milyon Gaussian ve 1 GB'ı aşar. Daha büyük belleğe sahip bir GPU
bunu eğitebilir, ancak VR gözlüğünde ya da Unity'de tek parça gösterim için ağırdır. Bu nedenle 3DGS, katın
ortak pozları kullanılarak oda / koridor parçaları hâlinde üretilmeli ve
gösterimde parça parça yüklenmeli. Parçalar zaten aynı koordinatta
olduğundan ek hizalama gerekmez. Katlar arası bağlantı, merdiven / asansör
geçişinin iki kata da taşan ayrı bir çekimiyle ve şerit metre referanslarıyla
kurulmalıdır.

### 7.2 Yöntem seçenekleri: kalite ve süre

Kat başına ~1.000 kare varsayımıyla. Süre: RTX 2060'ta ölçülen birim maliyetlerle
çıkarma + eşleştirme (bölüm 4.9); daha güçlü donanımın etkisi için bkz. 7.3. SfM süresi 349 karede 2–15 dk ölçüldü; 1.000 karede
incremental için doğrusalın üstünde büyür, pilotta ölçülmelidir.

| Seçenek (kat başına) | Bu deneyde doğru pozlanan kare (%) | 3DGS PSNR (dB) | Çıkarma + eşleştirme, 1.000 kare (sa) | 5 kat toplam (sa) | Değerlendirme |
| :--- | ---: | ---: | ---: | ---: | :--- |
| **LoMa + sequential + incremental** | 98,9 | 27,64 | 5,4 | 27 | En doğru; dokusuz yüzeyde de kare kaybetmiyor; süreyi özellik çıkarma belirliyor |
| **SIFT + vocab_tree + incremental** | 93,7 | — (b) | 1,1 | 5,4 | En hızlı doğru seçenek; bina ölçeği vekilinde kapsam %81'e düştü, dokusuz karelerin %18'ini kaybediyor |
| SIFT + exhaustive + incremental | 94,6 | 28,26 | 5,1 | 26 | Kalite üst sınırı; kat başına 1.000 kareyi aşarsa süre karesel büyür |
| ALIKED + sequential + loop + incremental | 84,5 | 25,11 | 0,8 | 3,9 | Dokusuz yüzeyde SIFT'ten iyi; tekrar eden mekânda yanlış eşleşme riski |
| SIFT + sequential + loop + incremental | 47,0 | 22,41 | 0,3 | 1,4 | Çok hızlı ama bu sahnede geometri kayıyor |
| Herhangi bir çıkarıcı + global | 18–95 | 15–28 | — | — | Yalnızca hızlı ön izleme; kopuk kamera ayıklaması şart |

(b) vocab_tree için 3DGS eğitilmedi; geometrisi exhaustive ile aynı olduğu için
kalitesinin benzer olması beklenir.

**Önerilen hat:**

1. **Birincil:** LoMa + sequential + incremental, kat başına. 5 katlı bir binada
   çıkarma + eşleştirme ~27 saat sürer; katlar birbirinden bağımsız işlendiği için
   bu süre kat kat bölünebilir. Daha güçlü bir GPU bu süreyi doğrudan kısaltır.
2. **Hızlı alternatif / yedek:** SIFT + vocab_tree + incremental (5 katta ~5 saat).
   Zaman kısıtlıysa ya da bir katta LoMa'da sorun çıkarsa kullanılır. Kapsam kaybı
   pilotta ölçülmelidir.
3. **Her katta zorunlu denetim:** kopuk kamera ayıklama; ayrılmış test kareleriyle
   3DGS kalitesi; katın kendi ilk ve son karelerinin örtüştüğünün (döngü
   kapanışı) kontrolü.
4. **Ölçüm katmanı:** kat başına dense (~15 sn/kare; 1.000 karede ~4 saat), 3DGS
   görsel katman olarak.

### 7.3 Daha güçlü donanımın etkisi

Bu deney RTX 2060 (6 GB) üzerinde yapıldı. Örneğin 24 GB belleğe sahip bir GPU ile
çalışılırsa:

* **Süre kısalır:** LoMa ve ALIKED'in özellik çıkarma ve eşleştirmesi GPU'ya bağlıdır;
  LoMa 6 GB'ın 5,3 GB'ını kullandı, yani sınırdaydı. Yeni nesil GPU'larda LoMa'nın
  daha hızlı BF16 modu da kullanılabilir (RTX 2060 desteklemiyor).
* **Kalite artar:** Dense tam çözünürlükte koşulabilir (bu deneyde 1000 piksel);
  3DGS tam çözünürlükte ve daha büyük bölgeler hâlinde eğitilebilir.
* **Değişmeyenler:** Geometrik doğruluk sonuçları ve exhaustive eşleştirmenin
  karesel büyümesi donanımdan bağımsızdır. SIFT eşleştirme ve incremental SfM
  büyük ölçüde işlemciye bağlı olduğundan GPU'dan az etkilenir.

Bu nedenle bölüm 7.2'deki yöntem önerileri güçlü donanımda da geçerlidir; değişen
yalnızca sürelerdir ve LoMa'nın tek zayıf yanı olan süre kısalacağı için birincil
öneri güçlenir. Kesin süreler pilot çekimde aynı betiklerle yeniden ölçülmelidir.

### 7.4 Pilot ve çekim planı

**Pilot.** Bina çekiminden önce bir katın bölümünde (~1.000 kare, iki koridor +
iki derslik) LoMa + sequential + incremental ile SIFT + vocab_tree + incremental
karşılaştırılmalı. Bakılacaklar: tekrar eden koridorlarda yanlış katlanma, kayıt
oranı, gerçek SfM süresi ve 3DGS parçalarının sınırlarda birleşmesi.

**Çekim planı.** Her koridor ve odada başlangıç noktasına dönülerek döngü
kapatılmalı; odalara koridordan girilip yine koridora çıkılmalı (kapı eşiği iki
tarafta da görünmeli); benzer alanlarda kapı numarası, pano gibi ayırt edici
öğeler kadraja alınmalı; katlar arası geçiş kesintisiz çekilmeli; her katta
şerit metreyle en az üç referans ölçü alınmalı.

---

## Ek — Kayıtlar

| Konum | İçerik |
| :--- | :--- |
| `experiments/hafta-04_sinif-01/` | Tüm ölçümler: `sfm_runs.csv`, `gs_summary.csv`, `scale_estimate.csv`, `zayif_doku.csv`, `dense/`; ortam ve yeniden üretim notları |
| `scripts/hafta04/` | SfM, 3DGS, dense, tablo ve şekil betikleri |
| `setup/colmap4_kurulum.md` | COLMAP 4.2.1, ONNX modelleri, CUDA 12 / cuDNN 9.10 kurulumu |
| `models/sinif-01_h04_*` | Her çıkarıcının en iyi 3DGS modeli (Git LFS) |

**Kaynaklar.** Lowe, IJCV 2004 (SIFT) · Zhao vd., IEEE TIM 2023 (ALIKED) ·
Lindenberger vd., ICCV 2023 (LightGlue) · Edstedt vd., 3DV 2024 (DeDoDe) ·
Nistér ve Stewénius, CVPR 2006 (vocab tree) · Schönberger ve Frahm, CVPR 2016
(COLMAP SfM) · Schönberger vd., ECCV 2016 (COLMAP MVS) · Pan vd., ECCV 2024
(GLOMAP) · Kazhdan ve Hoppe, ACM TOG 2013 (Poisson) · COLMAP 4.2.1 belgeleri.
