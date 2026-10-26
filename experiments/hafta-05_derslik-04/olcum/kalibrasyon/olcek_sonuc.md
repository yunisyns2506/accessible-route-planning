# Ölçek kalibrasyonu (LoMa + sequential + döngü + incremental)

Uç noktalar 2–3 karede elle işaretlendi, komşu karelerde NCC ile eşlendi (3 px'ten sapan eşleşmeler atıldı),
bilinen SfM pozlarıyla üçgenlendi. Her köşe 3–13 karede görülüyor; yeniden izdüşüm hatası çoğunlukla 1–3 px.

## Kalibrasyon (3 ölçü, en küçük kareler)

Ölçek = Σ(L·m) / Σ(m²) = **207,2 cm / model birimi**

| Kod | Nesne | Ölçülen | Model (birim) | Tek başına ölçek | Uydurmayla model | Sapma |
|---|---|---:|---:|---:|---:|---:|
| M1 | masa ön üst kenarı | 120 cm | 0,603 | 199 cm/b | 124,9 cm | +4,9 cm (+%4) |
| K1 | kürsü üst tablası | 70 cm | 0,396 | 177 cm/b | 82,1 cm | +12,1 cm (+%17) |
| D1 | kapı (koyu kasa dış köşeleri, üst) | 155 cm | 0,694 | 223 cm/b | 143,8 cm | −11,2 cm (−%7) |

Tek tek ölçeklerin yayılımı ±%12. Masa ile kürsü aynı bölgede durduğu için bu fark SfM kaymasıyla açıklanamaz;
ölçülerin kaba (cetvelle, "civarı") alınmasından ve D1 tanımındaki belirsizlikten gelir. D1 "kasa içi" olarak
alınırsa ölçek 235–258 cm/b çıkar; bu durumda kapı 2,4 m, masa 0,84 m yüksekliğe çıkar, gerçekçi değil.

## Bağımsız denetim (207,2 cm/b ile)

| Büyüklük | Model | Beklenen | Not |
|---|---:|---:|---|
| B1 platform yüksekliği (doğrulama ölçüsü) | 40,6 cm | 43,5 cm (42–45) | −2,9 cm (−%7) |
| Masa üst yüzeyi, platformdan | 0,74 m | ~0,75 m | standart masa |
| Kürsü üst tablası, platformdan | 1,09–1,14 m | ~1,1 m | standart kürsü |
| Kapı kasası üst köşesi, zeminden | 2,05–2,09 m | ~2,1 m | standart kapı |
| Kamera yüksekliği (medyan) | 1,28 m | elde çekim | |
| Tavan ızgarası, zeminden | 4,12 m | — | |

D2 (tek kanat) ve S2 (sıra tablası) henüz üçgenlenmedi.

Dosyalar: `isaretler.json` (elle işaretler), `noktalar_kalibrasyon.json` (3B noktalar, gözlemler, hatalar),
`isaretler_kalibrasyon.jpg` (her gözlemin yakın kırpımı). Betik: `scripts/hafta05/olcek_ucgenle.py`.
