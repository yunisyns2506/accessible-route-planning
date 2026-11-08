# Hafta 6 · Derslik 4 çekim planı

**Sürüm:** son (06.11.2026 çekimi). Hafta 5'in düz geçişleri korunur, yalnız eksik görüşler eklenir.

**Ne çekiyoruz:** Sınıf tek video (~17 dk) ve koridor ayrı video (~3 dk); lens **0,5× (13mm)**, **4K 30 fps**.
**Rota:** [rota_derslik4.png](rota_derslik4.png). Kullanılmayan 2. sürüm: [rota_v2_kullanilmadi.png](rota_v2_kullanilmadi.png), [cekim_plani_v2_kullanilmadi.md](cekim_plani_v2_kullanilmadi.md).

## Neden bu rota?

05.11 çekiminde lens (1×) ve rota (sıra aralarında 90° yana) birlikte değişti; SfM sıra aralarında bozuldu, PSNR 20,18 dB oldu (hafta 5: 25,23). Ayrıntı: [sonuclar_sinif_kosu1.md](sonuclar_sinif_kosu1.md).

**Hafta 5 yolundaki iki eksik** (kamera yolu verisinden):
1. 1,3 m ve 0,75 m geçişleri her aradan aynı yönde geçiyordu; 3., 4. ve 5. aralar tek yönden çekildi. Kürsüye doğru yürürken sandalyelerin arkası, kürsüden uzaklaşırken önü görünür. Bu aralarda ikisinden yalnız biri görüldü.
2. Telefon hep düz olduğu için görüş yürüme yönünün en fazla 48° yanına ulaşıyordu; sıraların yan yüzü hiç tam görülmedi.

**Bakış yönü karşılaştırması.** Yakın sıradaki bir noktanın kaç karede göründüğü, basit bir geometri modeliyle (aynı yürüyüş, aynı kare aralığı; gerçek çekimle doğrulanmadı):

| Bakış | Yürüme yönüne göre görülen açı | Nokta kaç karede görünür | Kareler arası kayma (model) |
| :--- | :--- | ---: | ---: |
| 0,5×, düz (hafta 5) | −48° … +48° | 14 | %0,6 |
| **0,5×, 45° çapraz** | **−3° … +93°** | **18** | **%0,9** |
| 0,5×, 90° yana | +42° … +138° | 8 | %4,5 |
| 1×, 90° yana (05.11, 1,25 kat seyrek kare) | +59° … +121° | 3 | %11,6 |

Model kaymayı gerçekten düşük veriyor (ölçülen: hafta 5 sıra aralarında %2,6, 05.11'de %17,1); karşılaştırma yalnız sıralama için geçerlidir. Çapraz bakış hem yürüme yönünü hem tam yanı aynı karede tutar. Bu yüzden yan yüz için tam yana değil **45° çapraz** bakıyoruz.

**Düz geçişler neden duruyor?** Hafta 5'te SfM'i sağlam tutan onlardı ve çapraz geçişin SfM'e etkisi henüz denenmedi. Bölüm 4 sorun çıkarırsa kareleri atılır, kalan hat hafta 5'e benzer şekilde çalışır.

## Kısa cevaplar

- **İki tür açı var.** **Dikey açı:** telefonu yukarı ya da aşağı eğmek (+ yukarı, − aşağı). **Yatay açı:** telefonu yürüme yönüne göre sağa ya da sola çevirmek. Aşağıdaki tabloda her bölüm için ikisi ayrı yazıyor. Koridordaki "45°" yatay açıdır: telefon yürüme yönünden duvara doğru 45° çevrili.
- **Telefon yatay mı?** Evet, bütün çekim **yatay** (manzara). Yatay görüş alanı geniş olur ve hafta 5 ile aynıdır.
- **Neden 4K çekiyoruz, kareler 1080p değil mi?** SfM ve 3DGS'ye 1080p kare veriyoruz, ama 4K'dan küçültmek daha iyi kare verir:
  1. 4 pikselin ortalaması alındığı için gürültü azalır, kenarlar keskinleşir. Telefonun kendi 1080p kaydı daha yumuşak ve daha çok sıkıştırılmış.
  2. Hafta 5'te en iyi model 1440p'den çıktı (+0,4 dB) ve Unity'ye o aktarıldı. Ölçüm (dense) de yüksek çözünürlük istiyor. 4K çekersek bu seçenekler açık kalır.
- **Neden 30 fps?** Hafta 5 ile aynı ve dosya küçük. Bulanıklığı fps değil enstantane belirler (1/200). 05.11'in 60 fps karelerinde keskinlik düşük değildi (medyan 491; hafta 5: 364); kötü sonucun sebebi 60 fps'e bağlanamıyor.
- **Kaç kare?** ~17 dk'dan **1500 kare**: kare aralığı ~0,7 sn (hafta 5: 0,62 sn).
- **Elde 1 m'yi nasıl tutarım?** Aşağıdaki vücut hizalarını kullan. Çekimden önce mezurayla bir kez kontrol et.

## A · Akşamdan hazırlık

1. iPhone'a **Blackmagic Camera** kur (ücretsiz; iOS 17+ istiyor, iPhone 11 destekleniyor).
2. **En az 10 GB** boş yer aç (17 dk 4K HEVC, en çok ~7 GB). Şarj %100, yanına powerbank.
3. Mezura, lazer metre (varsa), ölçü fotoğrafları için ikinci telefon.

## B · Kamera ayarları (Blackmagic Camera)

Ayarların çoğu **Ayarlar** sekmesinde değil, **Camera** sekmesindeki değer satırında (LENS · FPS · SHUTTER · ISO · WB · TINT). Bir değere dokunup yanındaki mavi **A**'yı kapatınca o değer manuel olur. Aşağıdakilerin **hepsi manuel**, yani hiçbirinde mavi A kalmamalı.

**Settings sekmesi (bir kez):**

| Bölüm | Ayar | Değer |
| :--- | :--- | :--- |
| Record | Codec | **HEVC (H.265)**; dokununca kalite seçeneği çıkarsa en yükseği |
| | Resolution | **4K** |
| | Color Space | **Rec.709**; HDR Video **kapalı** |
| | Lock White Balance on Record | **açık** (yedek; WB zaten manuel olacak) |
| Camera | Enable Vertical Video | **kapalı** (yatay çekim) |
| | Shutter Measurement | **Speed** |
| | Flicker Free Shutter Based On | **50Hz** |
| | Lens Correction | **açık** (hafta 5 videosu da düzeltilmişti) |
| Media | Record Proxy | **kapalı** (gereksiz ikinci dosya, yer yer) |
| | Auto Upload To Selected Project | **kapalı** (mobil veriyle yükleme yapmasın) |
| | Save Clips to | Photos/Files ya da In-App; aktarırken **Media** sekmesinden dışa aktar |

**Camera sekmesi (telefonu yatay tutup):**

| Değer | Ne yap | Hedef |
| :--- | :--- | :--- |
| **FPS** | Dokun, listeden seç | **30** |
| **LENS** | Dokun | **13mm (0,5× geniş açı)**; bütün çekimde aynı, değiştirme |
| **SHUTTER** | Dokun → A'yı kapat | **1/200** (titreme testinde bant görürsen 1/100) |
| **ISO** | Dokun → A'yı kapat | Salonda önce A'da bak, o değere yakın sabitle; beyaz duvar patlamasın. 13mm daha az ışık alır (f/2,4): ISO 800'ü aşarsa enstantaneyi **1/100** yap |
| **WB** / **TINT** | Dokun → A'yı kapat | Salonda A'nın gösterdiği değeri (~4000–5000 K) sabitle; beyaz duvar beyaz görünsün |
| **± (pozlama telafisi)** | A'yı kapat | **0.0** |
| **Odak** | 13mm lensin odağı sabittir; ayar çıkmazsa dokunma | Deneme kaydında yakın (1 m) ve uzak nesne keskin mi bak |
| **Sabitleme** (ilk simge: iki yanında çizgi olan daire) | Dokun | **Off** |
| Yön kilidi | iOS Denetim Merkezi'nde dikey yön kilidi **kapalı** → telefonu yatay çevir, arayüz yataya dönsün → **sonra** Settings → Camera → **Lock Current Orientation açık** | Önizleme tam ekran yatay olsun; yere/tavana bakarken dikeye dönmesin |

Kayıt başlamadan önce ekranın altındaki depolama kutusu **30 fps 4K'da en az 25 dk** göstermeli (pay dahil). **en az 10 GB** boş yer olsun.

Neden böyle?
- **Kilitli ISO, enstantane ve beyaz dengesi:** Otomatikte duvarın parlaklığı ve rengi kareden kareye değişir; model bunu gri ve renkli lekelerle açıklar (hafta 5'teki lekeler).
- **1/200:** Yürürken bulanıklığı keser. 50 Hz şebekede LED lambalar 1/200'de titreyebilir; 1/100'de titremez (C-3'te test).
- **Sabitleme kapalı:** Yazılım sabitlemesi her kareyi farklı kırpıp büker ve SfM'yi bozar. Gimbal yokken sarsıntıyı yavaş yürüyüş ve tutuş çözer (C).
- **Manuel odak:** Otomatik odak yürürken ileri geri arar ve bulanık kare üretir.

**Blackmagic olmazsa (stok Kamera uygulaması):** Ayarlar → Kamera → Video Kaydet: **4K 30**. "Otomatik Düşük Işık FPS" **kapalı**, "Kamerayı Kilitle" **açık**. Çekimde ekranda salonun ortasına **uzun bas → "AE/AF KİLİDİ"**. Bu uygulamada beyaz dengesi ve enstantane kilitlenemez.

## C · Elle tutuş ve yükseklik

**Tutuş (gimbal yok):** İki elle, telefon yatay, dirsekler gövdeye yapışık. Dizler hafif bükük, topuktan parmağa yuvarlanarak yürü; sarsıntıyı dizler alsın. Hızlı dönme; dönerken adım at.

**Yükseklik, vücut hizasıyla** (~1,75 m boy için; boyun farklıysa çekimden önce mezurayla bir kez kontrol et):

| Telefon yüksekliği | Telefon nerede? |
| :--- | :--- |
| **2,0 m** | Kollar yukarı uzanık, telefon başın üstünde (tavan bölümü) |
| **1,8 m** | Alın hizası; ekrana hafif yukarı bakarsın |
| **1,6 m** | Göz hizası (normal çekim) |
| **1,4 m** | Çene altı / göğüs üstü; dirsekler bükük |
| **1,2 m** | Göğüs altı / mide hizası; telefon önde, ekrana aşağı bakarsın (tekerlekli sandalye göz hizası) |
| **0,9–1,0 m** | Bel / kemer hizası; kollar aşağı uzanık. Zor gelirse hafif çömel |

## D · Salonda çekimden önce (10 dk)

1. Bütün lambaları aç; perde ya da jaluzi varsa kapat. Çekimde salonda kimse dolaşmasın.
2. **Titreme testi:** 1/200'de lambalara ve beyaz duvara 10 sn çek, oynat. Yatay bant ya da yanıp sönme varsa **1/100**'e geç.
3. Beyaz dengesini ve ISO'yu ayarla (B). 20 sn deneme çek, oynat, keskinliğe bak.
4. Ayar ekranının ekran görüntüsünü al; rapora girecek.

## E · Sınıf videosu (kesmeden, ~17 dk)

**Başlangıç:** Krokideki kırmızı nokta (kürsü tarafı, salonun orta hizası), salona dönük, telefon 1,3 m'de. Kaydı başlat, 3 sn kıpırdama.
**Hız:** rahat yavaş yürüyüş; bir sıra arası ~25 sn. **Her bölüm başında 2 sn kıpırdama:** bölümleri videoda böyle ayıracağız.

| # | Bölüm | Nerede yürü | Yükseklik | Dikey açı | Yatay açı | Süre |
| :---: | :--- | :--- | :--- | :---: | :--- | ---: |
| **1** | Salon turu | Duvarlardan ~1 m içeride tam tur | 1,3 m | 10° aşağı | düz | ~2 dk |
| **2** | Aralar, düz | 6. aradan 1. araya zikzak | 1,3 m | 10° aşağı | düz | ~3 dk |
| **3** | Aralar, alçak, **yön ters** | 1. aradan 6. araya zikzak; her ara 2. bölümün tersi yönünde | 0,75 m (bel altı) | 5° yukarı | düz | ~3 dk |
| **4** | Aralar, **çapraz** | 6. aradan 1. araya; her aradan arkaya git, aynı aradan öne dön | 1,5 m | 20° aşağı | **hep 45° sola** | ~5 dk |
| **5** | Kürsü ve masa | Çevresinde 1 tur 1,3 m'de, 1 tur 0,9 m'de; ~1,5 m uzaktan | 1,3 m, 0,9 m | 15° aşağı | **45° nesneye** | ~1,5 dk |
| **6** | Açık zemin | Kürsü önünde 2 şerit, sonra kapı duvarı boyunca | 1,4 m | **35° aşağı** | düz | ~1,5 dk |
| **7** | Tavan, dönüş | 2. ve 5. ara hizasında uzun kenar, sonra başlangıca | kollar yukarı (~2 m) | **35° yukarı** | düz | ~1,5 dk |

**Yön ters ne demek?** Aynı ara, karşı yönden yürünür. Örneğin 3. arada bölüm 2'de kürsüye doğru yürürsün (sandalyelerin arkası görünür), bölüm 3'te kürsüden uzaklaşırsın (önü görünür).

**Bitiş:** Başlangıç noktasında ilk kadrajla 3 sn dur, kaydı durdur.

**Açılar ne zaman değişir?** Bölüm içinde sabit. Geçişlerde 3–4 adımda (~3 sn) yavaşça değiştir. Yerinde hızlı dönme; dönerken adım at.

**Genel kurallar:**
- Beyaz duvara düz ve yakından bakma; kadrajda her zaman köşe, kapı, pano ya da pencere kenarı olsun.
- Bir yeri bozarsan kaydı kesme; o kısmı yavaşça tekrarla ve devam et.

## F · Koridor videosu (ayrı kayıt, ~3 dk)

**Amaç:** Asansörden K3 kapısına giden yolu çıkarmak. Şema: [rota_koridor.png](rota_koridor.png) (ölçeksiz). Ayarlar aynı: 0,5×, 4K 30 fps, her şey kilitli. Hafta 5 ile aynı bakış kullanıldığı için çapraz geçiş yok; duvarların yakın ayrıntısı bu hedefin dışında.

| # | Geçiş | Nerede | Yükseklik | Bakış | Süre |
| :---: | :--- | :--- | :--- | :--- | ---: |
| **1** | Gidiş | Asansör önünde 3 sn dur, orta hattan K3'e yürü | göğüs üstü (1,3–1,4 m) | düz, 10° aşağı | ~75 sn |
| **2** | K3 kapısı | Kapının bir yanından (A), sonra öbür yanından (B) kapıya bak; ~2 m içeri gir, dönüp kapıya bak, çık | 1,3 m | kapıya | ~30 sn |
| **3** | Dönüş | Aynı yoldan asansöre, sonda 3 sn dur | bel (~1 m) | düz, 5° yukarı | ~75 sn |

**İnsanlar:** Ders saatinde, koridor boşken çek. Biri kadraja girerse kaydı kesme: olduğun yerde bekle, geçince devam et. Geçtiği saniyeyi not al; o kareleri çıkarırız. K3 kapısı sınıf videosundaki gibi açık kalsın.

## G · Ölçümler (mezura)

Her ölçüyü iki kez al; uç noktaların fotoğrafını çek.

| Kod | Ne | Nasıl |
| :--- | :--- | :--- |
| M1 | Koridor genişliği | 3 yerde: asansör önü, orta, K3 önü; yerden ~1 m'de, duvardan duvara |
| M2 | Kapı net geçiş açıklığı | K3, asansör, merdiven kapısı (vakit kalırsa K1, K2, K4): kanat 90° açıkken kasa içinden kasa içine. Çift kanatlıda tek ve iki kanat ayrı |
| M3 | Kapı eşiği yüksekliği | K3 ve asansör: zeminden eşiğin üstüne |
| M4 | Başlangıç–hedef mesafesi | Asansör kapısı ortası → K3 ortası: düz çizgi ve yürüme yolu boyunca |
| M5 | Salon eni ve boyu, platform basamağı | Duvardan duvara (lazer metre varsa); basamak yüksekliği |
| Kal1–3 | Ölçek kalibrasyonu | Keskin köşeli üç büyük nesne: kapı kasası yüksekliği, bir pencere genişliği, yazı tahtası genişliği |

Kalibrasyonda kullanılan nesne doğrulamada kullanılmaz. Model ile ölçü arasındaki farklardan **MAE** = ortalama |hata| ve **RMSE** = √(ortalama hata²) hesaplanır.

## H · Sonra (Colab)

Hat hafta 5 ile aynı; farklar raporda belirtilir.
1. Kare seçimi: **1500 kare** (eşit pencere, hareket < 15 px/kare olan en net kare, hafta 5 ile aynı), 4K'dan 1080p. Her 10. kare test karesi.
2. SfM: LoMa + sequential + döngü + incremental, aynı ayarlar.
3. 3DGS: splatfacto, 30.000 iterasyon, 1080p.

Sonuç hafta 5 modeliyle yan yana konur: test karelerinde PSNR / SSIM / LPIPS ve Unity'de aynı noktalardan ekran görüntüleri (sıra yanı, kürsü arkası, zemin, tavan). Süre ve Colab birimi `logs/`'a yazılır. Koridor videosu ayrıca işlenir.

Kaynaklar: [Blackmagic Camera teknik özellikler](https://www.blackmagicdesign.com/products/blackmagiccamera/techspecs/W-APP-01) · [App Store](https://apps.apple.com/app/blackmagic-camera/id6449580241) · [PlayCanvas çekim rehberi](https://developer.playcanvas.com/user-manual/gaussian-splatting/creating/taking-photos/)
