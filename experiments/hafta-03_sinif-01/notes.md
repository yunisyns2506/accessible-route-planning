# sinif-01 — Koşu Kayıtları (Hafta 3)

Bu klasör D207 dersliğinde yapılan koşuların ham kayıtlarıdır. Yorum ve bulgular
için: [`docs/raporlar/hafta-03_raporu.md`](../../docs/raporlar/hafta-03_raporu.md)

## Veri kümesi

| Özellik | Değer |
| :--- | :--- |
| Kaynak | iPhone 11, 0.5× ultra geniş açı |
| Video | H.264, 1920×1080, 29,97 FPS, 348,8 s, 10.459 kare |
| Kare çıkarma | FFmpeg `fps=1` → **349 kare**, dikey 1080×1920, JPEG q=2 |
| Kare netliği | Laplacian varyansı: medyan 205; eşik 100 altında 34 kare (%9,7) |

Kareler üç SfM koşusunda da ortaktır (`data/sinif-01/frames_1fps/`).

## Deneysel kontrol

Yedi eğitim koşusunun tamamı **aynı SfM çıktısını** (`sfm_exhaustive`, 331 kare),
**aynı iterasyon sayısını** (15.000) ve aynı donanımı kullanır. Her koşuda
varsayılana göre yalnızca bir ayar değişir; G7 ise yöntem karşılaştırmasıdır.

Veri bölünmesi: **298 kare eğitim / 33 kare test**. Bildirilen PSNR, SSIM ve LPIPS
değerleri `ns-eval` ile ayrılmış test karelerinde ölçülmüştür.

## Dosyalar

| Dosya | İçerik |
| :--- | :--- |
| `sfm_metrics.csv` | Üç eşleştirme stratejisinin süre ve kalite ölçümleri |
| `egitim_metrics.csv` | Yedi eğitim koşusunun ayar, metrik, süre, VRAM ve boyut kaydı |
| `environment.md` | Donanım ve kütüphane sürümleri |
| `kosular/<ad>/config.yml` | Nerfstudio'nun kaydettiği tam ayar listesi |
| `kosular/<ad>/summary.json` | Birleştirilmiş metrikler |

## Yeniden üretim

```bash
# 1. Kareleri çıkar
ffmpeg -i Sinif_D207.MOV -vf fps=1 -q:v 2 data/sinif-01/frames_1fps/frame_%04d.jpg

# 2. SfM (üç strateji)
python scripts/sfm_run.py exhaustive  data/sinif-01/sfm_exhaustive
python scripts/sfm_run.py sequential  data/sinif-01/sfm_sequential
python scripts/sfm_run.py vocab_tree  data/sinif-01/sfm_vocabtree

# 3. ZORUNLU: transforms.json en büyük COLMAP modelinden üretilsin
python scripts/fix_transforms.py data/sinif-01/sfm_*

# 4. İstatistikler
python scripts/colmap_stats.py data/sinif-01/sfm_*

# 5. Eğitim kuyruğu (7 koşu)
bash scripts/run_queue.sh

# 6. Değerlendirme ve görseller
python scripts/eval_run.py runs/sinif-01/*
python scripts/render_compare.py runs/sinif-01/*
```

> **4. adım atlanmamalıdır.** Nerfstudio `transforms.json` dosyasını daima
> `colmap/sparse/0` klasöründen üretir; COLMAP sahneyi parçaladığında en büyük
> model `sparse/0` olmayabilir. Bu veri kümesinde 331 görüntülük model
> `sparse/1`'e, 2 görüntülük artık `sparse/0`'a yazılmıştır.

## Çıktıların yeri

Eğitim çıktıları (`runs/sinif-01/`) ve PLY dosyaları (`exports/sinif-01/`) boyutları
nedeniyle sürümlenmez; ayar ve metrik kayıtları bu klasörde tutulur.
