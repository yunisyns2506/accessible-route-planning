# Hafta 6 · Derslik 4: beyaz zemindeki lekelerin kaynağı (08.11.2026)

Yöntem: `scripts/hafta06/zemin_tani.py`, `zemin_derinlik.py`. Zemin 10 cm ızgaraya bölündü, 1500 karede aynı noktaların rengi karşılaştırıldı (4,37 milyon örnek). Görsel: `zemin_tani.png`.

## Gerçek karelerde ölçülen etkiler

| Etken | Ölçüm | Sonuç |
| :--- | :--- | :--- |
| Pozlama | Kare parlaklığı std %6,7 (p5–p95 −%10,7 / +%8,9) | Var; H2 bunu telafi etmek için kullanılıyor |
| Beyaz denge | R/G std %0,95, B/G std %1,37 | İhmal edilebilir |
| Tavan lambası yansıması | Aynalanan ışın lambaya yakınken +%5,4, uzakken −%0,7 | Gerçek ama küçük ve yumuşak |
| Pencere yansıması | Aynalanan ışın pencereye düşerken −%0,7, uzakken −%6,1 | Gerçek ama küçük ve yumuşak |
| Çeken kişinin gölgesi | Kameraya yakın zemin parlaklığı +%2–3 | Karartma görülmedi (0,7 m altı örnek yok) |

## Modeldeki zemin (boş sıra arası zemin, 17–18 bin hücre)

Seyrek SfM noktalarına göre zemin düzlemi RMS 0,75 cm.

| Model | Zeminin 8 cm altında | Düzlemde ±8 cm |
| :--- | ---: | ---: |
| 1080p, H2'siz | %88,2 | %10,1 |
| 1080p, H2 | %53,8 | %43,9 |
| 1440p big, H2 | %63,2 | %35,3 |

Ağırlık: opaklık × Gaussian alanı.

## Yorum

Parlak ve dokusuz zeminde yansıma görüşe göre değişir. Model bunu yüzeyin rengi yerine zeminin altına Gaussian koyarak (bazıları −1,2 m'ye kadar) öğreniyor. Ölçülen gerçek yansıma etkisi %5–6; lekeler ise eğitim karelerinden uzak açılarda belirginleşiyor. H2 kısmen düzeltiyor (%88'den %54'e), 1440p big düzeltmiyor.

Bu bir çıkarımdır: yerleşim kanıtlandı, lekelerin tamamen bundan kaynaklandığı henüz deneyle gösterilmedi.

Sınır: gerçek zemin haritası sandalyeler nedeniyle sınıfın yalnız bir kısmını kapsıyor; 'model / gerçek' paneli bu yüzden 544 hücreyle sınırlı ve karar için kullanılmadı.

## Deney: zemin altı Gaussian'ları düzleme indirme (`scripts/hafta06/zemin_duzle.py`)

Sınıfın ana zemininde (platform ve koridor hariç) y < −3 cm olan Gaussian'lar zemin düzlemine indirildi, şekilleri yatay düzleme izdüşürüldü, görüşe bağlı renk terimleri sıfırlandı. Yeniden eğitim yok.

| Dosya (Drive `birlesik/`) | Taşınan | Oran | Kalan zemin altı | MB |
| :--- | ---: | ---: | ---: | ---: |
| `birlesik_sinif1080_koridor_zemin_duz_unity.ply` | 18.705 | %1,92 | 0 | 242 |
| `birlesik_sinif1440_koridor_zemin_duz_unity.ply` | 19.815 | %1,51 | 0 | 325 |

Görsel sonuç Unity'de henüz görülmedi; lekelerin azalıp azalmadığı oradan anlaşılacak.

**Unity sonucu (08.11):** Deney başarısız. Düzleştirilmiş zeminde lekeler daha sert ve uzun çizgiler halinde görünüyor; `birlesik_*_koridor_unity.ply` dosyaları kullanılmaya devam edecek. Zemin altındaki Gaussian'lar zeminin görünümünü taşıyor; yalnız konumlarını değiştirmek düzeltme sağlamadı. Lekelerin giderilmesi için eğitimde zemin kısıtı ya da gerçek karelerden üretilen düz bir zemin gerekir.

## Deney: gerçek karelerden düz zemin (`scripts/hafta06/zemin_gercek.py`)

Ana zemin 5 cm ızgaraya bölündü, her hücre yakın ve yeterince dik bakan karelere izdüşürüldü (derinlik < 10 m). Sandalye benzeri pikseller renkle elendi, kare parlaklık farkı medyanla düzeltildi, hücre rengi kalan örneklerin medyanı alındı. Çevresinden %10'dan koyu hücreler (sandalye altı ve gölge kalıntısı) yakındaki temiz zeminin rengiyle dolduruldu. Birleşik dosyada zemin + 3 cm altındaki Gaussian'lar silindi, yerine hücre başına bir yassı Gaussian kondu (σ 3,3 cm, normal yönünde 2 mm, görüşe bağlı renk yok). Yeniden eğitim yok.

| Girdi | Değer |
| :--- | ---: |
| Örnek sayısı | 10.411.294 |
| Sandalye altı doldurulan hücre | %38,2 |
| Dolu hücre | %100 |

| Dosya (Drive `birlesik/`) | Silinen | Toplam Gaussian | MB |
| :--- | ---: | ---: | ---: |
| `birlesik_sinif1080_koridor_gercek_zemin_unity.ply` | 29.473 | 1.059.235 | 262,7 |
| `birlesik_sinif1440_koridor_gercek_zemin_unity.ply` | 35.843 | 1.387.985 | 344,2 |

Üstten harita: `zemin_harita_son.jpg`. Dalga ve renk lekeleri görüşe bağlı olmadığı için kalkıyor, ancak harita düzgün değil: sandalye sıraları tırtıklı kenarlı, biraz daha koyu adacıklar olarak görünüyor, sıra araları açık bantlar halinde kalıyor; z− duvarı tarafında açık renkli lekeler var (sebebi incelenmedi). Unity'de henüz görülmedi.
