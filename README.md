# 3DGS ve VR/Simülasyon Destekli Erişilebilir Rota Planlama Sistemi

**Bursa Uludağ Üniversitesi Bilgisayar Mühendisliği — Tasarım Projesi**
Sabri Duruk · Yunis Teymurlu · Danışman: Öğr. Gör. Koray AKİ

İç mekânların **3D Gaussian Splatting** ile dijital ikizlerini üreten ve
tekerlekli sandalye kullanan bireyler için erişilebilir rota planlayan
simülasyon sistemi.

---

## Durum — Hafta 3

**A1 (mekân modelleme) devam ediyor.** Üretim hattı (çekim → COLMAP → Splatfacto
→ PLY) doğrulandı; metrik ölçek ve Unity aktarımı (A2) bekliyor.

Bu hafta D207 dersliğinde aynı veri üzerinde **10 koşu** karşılaştırıldı:

**→ [Hafta 3 Raporu](docs/raporlar/hafta-03_raporu.md)**

### Eşleştirme stratejisi (349 kare)

| Strateji | Süre | Kaydolan | COLMAP modeli |
| :--- | ---: | ---: | ---: |
| `sequential` | 6,6 dk | 149 (%42,7) | 4 parça |
| **`exhaustive`** | 13,9 dk | **331 (%94,8)** | 1 bütün |
| `vocab_tree` | 16,1 dk | 331 (%94,8) | 1 bütün |

### Eğitim (331 kare, 15.000 iterasyon, 33 kare test)

| Koşu | PSNR | SSIM | LPIPS | Süre | VRAM |
| :--- | ---: | ---: | ---: | ---: | ---: |
| varsayılan | 27,22 | 0,9091 | 0,1759 | 8,9 dk | 2.289 MB |
| **+ antialiased** | **27,38** | **0,9111** | **0,1697** | 9,5 dk | 2.299 MB |
| + ölçek düzenleme | 27,14 | 0,9084 | 0,1838 | 11,2 dk | 2.470 MB |
| + kamera pozu opt. | 22,52 | 0,7794 | 0,2119 | 14,0 dk | 2.673 MB |
| `splatfacto-big` | 26,55 | 0,9031 | 0,1757 | 17,8 dk | 4.285 MB |
| tam çözünürlük | 26,87 | 0,9053 | 0,2705 | 21,6 dk | 4.749 MB |
| `nerfacto` (NeRF) | 22,48 | 0,7874 | 0,3260 | 11,8 dk | 4.459 MB |

---

## Yapı

Sürümlenen klasörler:

```text
docs/raporlar/      Raporlar (.md ve .docx)
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
(örn. `runs/sinif-01/G2_antialiased_30k/`).

Eğitim hattı CUDA destekli GPU gerektirir ve tek bilgisayarda (RTX 2060 6 GB)
kuruludur. Kurulum: [`setup/README.md`](setup/README.md) ·
Çözülen derleyici hataları: [`setup/kurulum_notlari.md`](setup/kurulum_notlari.md)

## Koşuyu tekrarlamak

Adım adım komutlar:
[`experiments/hafta-03_sinif-01/notes.md`](experiments/hafta-03_sinif-01/notes.md)

> `scripts/fix_transforms.py` **zorunlu** adımdır: nerfstudio `transforms.json`
> dosyasını daima `colmap/sparse/0`'dan üretir, ancak COLMAP sahneyi
> parçaladığında en büyük model orada olmayabilir.
