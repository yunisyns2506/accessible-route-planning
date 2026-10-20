# 3DGS ve VR/Simülasyon Destekli Erişilebilir Rota Planlama Sistemi

**Bursa Uludağ Üniversitesi Bilgisayar Mühendisliği — Tasarım Projesi**
Sabri Duruk · Yunis Teymurlu · Danışman: Öğr. Gör. Koray AKİ

İç mekânların **3D Gaussian Splatting** ile dijital ikizlerini üreten ve
tekerlekli sandalye kullanan bireyler için erişilebilir rota planlayan
simülasyon sistemi.

---

## Durum — Hafta 4

**A1 (mekân modelleme) devam ediyor.** COLMAP'in tüm yöntem ailesi aynı veri
(D207, 349 kare) ve aynı donanımda karşılaştırıldı: **3 özellik çıkarıcı × 5
eşleştirme × 3 SfM yöntemi = 39 SfM koşusu, 16 3DGS eğitimi (30k), 3 dense
rekonstrüksiyon.** LoMa'nın sözlük ağacı gerektiren 3 stratejisi koşulamadı
(gerekçe raporda). Sonuçlar çok katlı bina için yöntem seçimine bağlandı.

**→ [Hafta 4 Raporu](docs/raporlar/hafta-04_raporu.md)** · [Hafta 3 Raporu](docs/raporlar/hafta-03_raporu.md)

### Öne çıkanlar

| Bulgu | Sonuç |
| :--- | :--- |
| Kalite ölçütü | Kayıt oranı yanıltıcı; **doğru pozlanan kare oranı** 3DGS kalitesini belirliyor |
| SIFT | exhaustive + incremental en iyi (PSNR 28,26) ama 5.000 karede eşleştirme ~128 sa |
| ALIKED + LightGlue | Tekrar eden mekânda yanlış eşleşme → oda katlanıyor (doğru pozlanan kare %44, PSNR 19) |
| **LoMa** | **sequential + incremental = exhaustive kalitesi** (27,64 / 27,81), eşleştirme 19× ucuz; çıkarma 18 sn/kare |
| Zayıf dokulu yüzey | SIFT dokusuz karelerin %18'ini kaybediyor; ALIKED %2, LoMa hiç kaybetmiyor |
| Global mapper | Tüm koşularda kopuk kameralar; aykırı kamera filtresi zorunlu |
| Dense | 1,7–1,9 M nokta, kat planı görünümü elde edildi; ölçüm katmanı dense olmalı |

### Teslim edilen raporlar

| Rapor | Dosya |
| :--- | :--- |
| Literatür Araştırması (27 yayın) | [`01_literatur_arastirmasi.docx`](docs/raporlar/01_literatur_arastirmasi.docx) |
| Benzer Çalışmaların Karşılaştırılması | [`02_benzer_calismalarin_karsilastirilmasi.docx`](docs/raporlar/02_benzer_calismalarin_karsilastirilmasi.docx) |
| Yazılım Altyapısı ve Araç Seçimi | [`03_yazilim_altyapisi_ve_arac_secimi.docx`](docs/raporlar/03_yazilim_altyapisi_ve_arac_secimi.docx) |
| Sistem Tasarımı ve Uygulama Planı | [`04_sistem_tasarimi_ve_uygulama_plani.docx`](docs/raporlar/04_sistem_tasarimi_ve_uygulama_plani.docx) |
| Hafta 3 — Üretim hattı ve yöntem karşılaştırması | [`hafta-03_raporu.docx`](docs/raporlar/hafta-03_raporu.docx) |
| Hafta 4 — COLMAP yöntemleri ve bina ölçeği önerileri | [`hafta-04_raporu.docx`](docs/raporlar/hafta-04_raporu.docx) |

---

## Yapılacaklar

### Hafta 3 sonrası görüşme maddeleri

✅ yapıldı · ⏳ sonraki aşama · ❌ yapılmadı

| Madde | Durum | Nerede |
| :--- | :---: | :--- |
| Bütün raporlar GitHub'da | ✅ | [`docs/raporlar/`](docs/raporlar/) |
| Sistem bilgisi (system info) | ✅ | [`environment/system-info.md`](environment/system-info.md) |
| Her 3DGS sürümünü hafta hafta kaydetmek | ✅ | [`models/`](models/) (`sinif-01_h04_*`) |
| Sistemin kurulum basamakları | ✅ | [`setup/README.md`](setup/README.md), [`setup/colmap4_kurulum.md`](setup/colmap4_kurulum.md) |
| Her şey ayrı klasörde | ✅ | Yapı bölümü |
| Algoritmaların ayrıntılı anlatımı (COLMAP nasıl çalışır, özellik çıkarma, yöntemlerin maliyeti) | ✅ | Hafta 4 raporu, bölüm 2 ve 4.8 |
| SIFT / ALIKED / LoMa aynı veri setinde karşılaştırma | ✅ | Rapor 4.1–4.4 (LoMa'da sözlük ağacı gerektiren 3 strateji koşulamadı) |
| ALIKED + LightGlue (öğrenme tabanlı eşleştirme) | ✅ | Rapor 4.1–4.4 |
| Zayıf dokulu yüzeylerde ALIKED | ✅ | Rapor 4.6 |
| Görüntü eşleştirme yöntemleri | ✅ | exhaustive, sequential, sequential + loop, vocab_tree; spatial uygulanamadı (GPS yok) |
| SfM'in üç yöntemi | ✅ | incremental, global, hierarchical |
| Yoğun geometri: PatchMatch, stereo fusion, meshing | ✅ | Rapor 4.7 |
| SIFT + sequential + incremental | ✅ | Rapor 4.2 |
| SIFT + exhaustive + incremental | ✅ | Rapor 4.2 |
| SIFT + sequential + global | ✅ | Rapor 4.2 |
| Minimum sistem gereksinimleri | ✅ | Rapor 4.8 |

**Ölçütler**

| Ölçüt | Durum | Nerede |
| :--- | :---: | :--- |
| Başarıyla pozlanan görüntü oranı | ✅ | Rapor 4.1–4.2 (doğru pozlanan kare) |
| Sahnenin oluşturulabilen kısmı (%) | ✅ | Rapor 4.1–4.2 (modele giren kare) |
| 3B noktaların 2B izdüşüm hatası | ✅ | Rapor 4.2 |
| Geometrik tutarlılık | ✅ | Rapor 3, 4.1–4.3 (referansa hizalama) |
| Seyrek 3B nokta sayısı (sparse point count) | ✅ | Rapor 4.2 |
| İz uzunluğu (track length) | ✅ | Rapor 4.2 |
| İşlem süresi | ✅ | Rapor 4.8 |
| Bellek tüketimi | ✅ | Rapor 4.8 |
| Referans ölçüden sapma | ❌ | Derslikte şerit metreyle ölçü gerekiyor |
| VR performansı | ⏳ | Sonraki aşama |

### Hafta 4 — COLMAP yöntem karşılaştırması

- [x] COLMAP 4.2.1 + ONNX modelleri + CUDA 12 / cuDNN 9.10 kurulumu ([`setup/colmap4_kurulum.md`](setup/colmap4_kurulum.md))
- [x] Ölçüm betikleri (`scripts/hafta04/`): süre, tepe RAM / VRAM, model istatistikleri, kare kare test metrikleri
- [x] SIFT bloğu: 15 SfM + 6 3DGS + dense
- [x] ALIKED + LightGlue bloğu: 15 SfM + 6 3DGS + dense
- [x] LoMa bloğu: 6 SfM + 4 3DGS + dense (sözlük ağacı gerektiren 9 SfM / 2 3DGS N/A: COLMAP aracı 256 boyutu desteklemiyor, pycolmap ile kurulum süre sınırını aştı)
- [x] Karşılaştırma tabloları ve görseller ([`experiments/hafta-04_sinif-01/`](experiments/hafta-04_sinif-01/), `docs/figures/hafta-04/`)
- [x] Hafta 4 raporu: yöntemlerin çalışma biçimi, maliyeti, gereksinimleri, sonuçlar, bina önerileri
- [x] Haftalık 3DGS modellerinin `models/` altına kaydı (`sinif-01_h04_*`)

### Açık işler

- [ ] Referans ölçüden sapma: derslikte şerit metreyle en az 3 ölçü
- [ ] Bina pilotu: bir katın bölümünde ~1.000 kare ile SIFT + vocab_tree ve LoMa + sequential karşılaştırması (rapor 7.4)
- [ ] Unity sürümünün `environment/system-info.md`'ye işlenmesi; yerel modellerin Unity aktarımı (A2)
- [ ] VR performans ölçümü (sonraki aşama)

---

## Yapı

Sürümlenen klasörler:

```text
docs/raporlar/      Teslim raporları (.docx) ve haftalık rapor kaynağı (.md)
docs/figures/       Rapor şekilleri
experiments/        Koşu kayıtları: ayarlar, metrikler, yeniden üretim adımları
models/             Üretilen 3DGS modelleri (Git LFS)
environment/        Donanım, sürümler ve lisanslar
scripts/            Koşu ve ölçüm betikleri
setup/              Kurulum ve çözülen derleyici hataları
```

Yerel çalışma klasörleri (boyut nedeniyle sürümlenmez):

```text
data/<veri-kümesi>/        ham kareler ve COLMAP çıktıları        11 GB
runs/<veri-kümesi>/<koşu>/ eğitim çıktıları ve kontrol noktaları   5,4 GB
```

Üretilen `.ply` modelleri `models/` altında Git LFS ile sürümlenir.

Veri kümesi adları: `oda-01_video`, `oda-01_79foto`, `oda-01_512foto`,
`sinif-01`. Koşu adları `experiments/` altındaki kayıtlarla birebir aynıdır
(örn. `runs/sinif-01/G2_antialiased_30k/`, hafta 4 için
`runs/sinif-01/hafta-04/loma_sequential_incremental/`).

Eğitim hattı CUDA destekli GPU gerektirir ve tek bilgisayarda (RTX 2060 6 GB)
kuruludur. Kurulum: [`setup/README.md`](setup/README.md) ·
Çözülen derleyici hataları: [`setup/kurulum_notlari.md`](setup/kurulum_notlari.md)

## Koşuyu tekrarlamak

Adım adım komutlar:
[hafta 3](experiments/hafta-03_sinif-01/notes.md) ·
[hafta 4](experiments/hafta-04_sinif-01/notes.md) (COLMAP 4.2.1, `scripts/hafta04/`)

> `scripts/fix_transforms.py` **zorunlu** adımdır: nerfstudio `transforms.json`
> dosyasını daima `colmap/sparse/0`'dan üretir, ancak COLMAP sahneyi
> parçaladığında en büyük model orada olmayabilir.
