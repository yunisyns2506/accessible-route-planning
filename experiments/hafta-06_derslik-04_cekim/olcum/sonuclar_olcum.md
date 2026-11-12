# Hafta 6 · Derslik 4: mezura ölçüleriyle ölçek ve geometri doğrulaması (08.11.2026)

Uç noktalar 1920×1080 video karelerinde işaretlendi, SfM pozlarıyla üçgenlendi (`scripts/hafta06/olcum_hesap.py`, `olcum_sonuc.py`). Mezura fotoğraflarının üzerinde çizim olduğu için raporda kullanılmaz.

## Ölçek

**212,51 cm/birim** (önceki tahmin 210; fark +%1,2). Kalibrasyon en küçük karelerle üç ölçüden yapıldı. Koridor, hizalama dönüşümüyle aynı ölçeğe bağlıdır.

| Kod | Ölçü | Tür | Mezura (cm) | Model (cm) | Hata (cm) | Hata (%) |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| K1 | Büyük pencere genişliği | Kalibrasyon | 217,5 | 216,5 | −1,0 | −0,5 |
| K2 | Çift kanat kapı, kasa içi | Kalibrasyon | 152,5 | 153,4 | +0,9 | +0,6 |
| K3 | Küçük pencere genişliği | Kalibrasyon | 115,7 | 116,4 | +0,7 | +0,6 |
| D1 | Sınıf kısa kenarı | Doğrulama | 1480,0 | 1475,6 | −4,4 | −0,3 |
| D2 | Sahne yüksekliği | Doğrulama | 46,0 | 46,6 | +0,6 | +1,2 |
| D3 | K3 kapısı, kasa içi (koridor modeli) | Doğrulama | 152,5 | 155,7 | +3,2 | +2,1 |
| D4 | K3 tek kanat net açıklık (koridor modeli) | Doğrulama | 74,5 | 77,9 | +3,4 | +4,5 |
| D5 | Öğretmen masası genişliği | Doğrulama | 130,0 | 125,1 | −4,9 | −3,7 |
| D6 | Askı yüksekliği | Doğrulama | 34,0 | 30,8 | −3,2 | −9,3 |
| D7 | Kürsü üst levha, ön kenar genişliği | Doğrulama | 69,0 | 67,7 | −1,3 | −1,9 |
| D8 | Askı genişliği (K3 yanındaki uzun askı, alt kenar) | Doğrulama | 200,0 | 194,8 | −5,2 | −2,6 |
| D9 | Radyatör genişliği (pencere altı, üst kenar) | Doğrulama | 100,0 | 98,4 | −1,6 | −1,6 |

| Küme | Ölçü | MAE (cm) | RMSE (cm) | En büyük (cm) |
| :--- | ---: | ---: | ---: | ---: |
| Kalibrasyon | 3 | 0,87 | 0,88 | 1,0 |
| Doğrulama | 9 | 3,09 | 3,45 | 5,2 |

Kalibrasyon kümesi sonradan değiştirildi. İlk seçim (büyük pencere, askı, masa) 229,2 cm/birim verdi; askı diğer ölçülerle tutarsız çıktı. Pencere, kapı, kısa kenar ve sahne 208–214 cm/birimde toplandı.

**Düzeltme (11.11.2026):** İlk turda askı (−38,0 cm), radyatör (−21,9 cm) ve kürsü (+16,3 cm) şüpheli bırakılmıştı. Nesneler mezura fotoğraflarıyla eşleştirildi (görseller `kontrol/`):
- Askı: kapının yanındaki kısa askı ölçülmüştü; mezura K3'e en yakın uzun askıdan alınmış. Uzun askı 0708, 0192, 0634, 0636 karelerinde, alt kenar 194,8 cm (izdüşüm hatası ≤ 2,2 px, üçlü kombinasyonlar 193–199 cm).
- Radyatör: başka bir radyatör ölçülmüştü. Doğru radyatör (kullanıcının gösterdiği görüntü 1296 numaralı kareyle eşleşti) 1290, 1292, 1296, 1300, 1302 karelerinde, üst kenar 98,4 cm (izdüşüm hatası ≤ 6,7 px, üçlüler 85–125 cm). Aynı radyatörü uzaktan gören 1100, 1210, 1213, 1215 kareleri 49–85 cm arası tutarsız sonuç verdi ve kullanılmadı.
- Kürsü: bir uç levhanın arka köşesine düşmüştü. Ön üst köşeler 1145, 0965, 1055'te, 67,7 cm.
Bu karelerin bir kısmı `kareler/` klasöründe yok (Drive `derslik4_cekim2/frames_1080/`); `olcum_hesap.py` bunlarda işareti inceltmeden kullanır.

## Geometri (LoMa seyrek noktaları, 210 cm/birim çerçevesinde)

| Ölçüt | Sonuç |
| :--- | :--- |
| Karşılıklı duvarların paralelliği | 1,23° (x), 0,79° (z) |
| Komşu duvar açıları | 89,6°, 89,9°, 88,4°, 88,9° |
| Duvar–zemin açıları | 89,2°, 88,8°, 89,3°, 89,9° |
| Duvar düzlemine uyum (RMS) | 0,9–1,1 cm |
| Zemin düzlemine uyum (RMS) | 0,75 cm |
| Yatay düzeltme sonrası zemin kotu | Sınıf −7 ile −1 cm; koridor −3 ile +1 cm |

Belirgin bir duvar kayması yok. `x+` duvarı daha az noktayla kestirildi (261 nokta), açıları daha az güvenilir.

## Dense

Bu ölçüler için dense gerekmedi: uç noktalar üçgenlemeyle, duvar ve zemin düzlemleri seyrek noktalarla çıktı. Dense, yüzeyin her yerini denetlemek için daha yoğun nokta verir; ölçek veya doğruluk kendiliğinden gelmez. Hafta 5'te 1000 kare için 9 sa 45 dk (~15 birim) sürdü, duvarların yalnız %36–60'ını doldurdu.

## Yapılamayanlar

- Basamaklar (16,5 / 15 / 13 cm) ve sandalye yüksekliği (83 cm) modelden ölçülmedi: net köşe yok.
- Koridor genişliği, kapı eşiği yüksekliği ve başlangıç–hedef mesafesi klasörde yok.
- D3 ve D4'te mezura K3 ile aynı kapı tipinden alındı; doğrudan K3'ün ölçüsü olduğu doğrulanmadı.

## Temizlik ve tek PLY (`scripts/hafta06/birlestir.py`)

Ölçek 212,51 cm/birim uygulandı. Silinen Gaussian'lar: opaklık < 0,05; en uzun eksen > 1 m; iğne biçimli; yalnız kalan; koridorda kamera yolundan > 15 m.

| Dosya (Drive `Hafta 6 Çalışmaları/birlesik/`) | Sınıf | Koridor | Toplam | MB |
| :--- | ---: | ---: | ---: | ---: |
| `birlesik_sinif1080_koridor_unity.ply` | 330.984 | 644.186 | 975.170 | 242 |
| `birlesik_sinif1440_koridor_unity.ply` | 666.104 | 644.186 | 1.310.290 | 325 |

Silinen oran: 1080p sınıf %4,8, 1440p sınıf %23,8, koridor %29,9. Unity'de görsel kontrol henüz yapılmadı.
