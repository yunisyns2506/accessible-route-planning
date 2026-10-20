# sinif-01 — Hafta 4 Koşu Kayıtları (COLMAP yöntem karşılaştırması)

Yorum ve bulgular: [`docs/raporlar/hafta-04_raporu.md`](../../docs/raporlar/hafta-04_raporu.md)

## Veri ve ortam

Kareler hafta 3 ile aynıdır: `data/sinif-01/frames_1fps/` (349 kare, 1080×1920).
Ortam: [`environment.md`](environment.md). Kurulum: [`setup/colmap4_kurulum.md`](../../setup/colmap4_kurulum.md).

## Koşulanlar

| Blok | Koşu | Tarih |
| :--- | :--- | :--- |
| SIFT | 15 SfM (5 eşleştirme × 3 SfM) + varsayılan hierarchical (3, eşdeğerlik kanıtı) + 6 3DGS + dense | 2026-10-19 |
| ALIKED + LightGlue | 15 SfM + 6 3DGS + dense | 2026-10-19/20 |
| LoMa | 6 SfM + 4 3DGS + dense; sözlük ağacı gerektiren 9 SfM / 2 3DGS N/A | 2026-10-20 |

Her kombinasyon bir kez koşulmuştur (tohum 1). Özellik çıkarma çıkarıcı başına,
eşleştirme strateji başına bir kez yapılıp paylaşılmıştır.

## LoMa sözlük ağacı denemeleri

1. COLMAP `vocab_tree_builder`: 256 boyutlu tanımlayıcıda çöküyor (yalnızca 128 boyut destekli).
2. pycolmap 4.2.1 ile 256 boyutlu dizin (`build_vocab_tree.py`): 65.536 sözcükle 13 dk,
   8.192 sözcükle 67 dk içinde bitmedi (tek çekirdek); süre sınırında durduruldu.
   Kayıtlar: `data/sinif-01/hafta-04/logs/loma_vocab_*`.

Doğruluk ölçütü: referans LoMa + exhaustive + incremental (349 karenin tamamı);
"doğru pozlanan kare" = referansla sahne ölçeğinin %5'i içinde örtüşen kare / 349.

## Dosyalar

| Dosya | İçerik |
| :--- | :--- |
| `sfm_runs.csv` | Her SfM kombinasyonu: durum / N/A nedeni, ana modeldeki kare, model sayısı, aykırı kamera, nokta, iz uzunluğu, yeniden izdüşüm hatası, çift bulma oranı (exhaustive'e göre), aşama süreleri, tepe RAM/VRAM, referansa göre örtüşme % ve medyan / %90 dönme-konum hatası |
| `gs_summary.csv` | 3DGS: kendi test karelerinde ve ortak 13 karede PSNR/SSIM/LPIPS, eğitim süresi, tepe VRAM/RAM, Gaussian sayısı |
| `gs_common_frames.txt` | Ortak karşılaştırmada kullanılan 13 test karesi |
| `scale_estimate.csv` | Birim maliyetler (sn/kare, ms/çift) ve 1k/5k/10k kare için çıkarma + eşleştirme süre kestirimi |
| `zayif_doku.csv`, `zayif_doku_kareler.csv` | Zayıf dokulu (alanın ≥ %60'ı dokusuz, 45 kare) ve normal karelerde çıkarıcı karşılaştırması; kare bazında dokusuz alan, anahtar nokta, eşleşme, modele giriş (`weak_texture.py`) |
| `dense/*.json` | Dense aşama süreleri, bellek, yoğun nokta ve mesh sayıları |

Ham çıktılar (veritabanları, seyrek modeller, eğitimler, dense) boyut nedeniyle
sürümlenmez: `data/sinif-01/hafta-04/` ve `runs/sinif-01/hafta-04/`.
`runs/sinif-01/hafta-04/_aykiri_dahil_sift_exhaustive_global/` aykırı kamera
filtresi olmadan eğitilen ilk denemedir (PSNR 14,15); karşılaştırmaya girmez.

## Yeniden üretim (depo kökünden)

```bash
# Her blok: 15 SfM -> 6 3DGS -> tablolar -> (isteğe bağlı) dense
bash scripts/hafta04/run_block.sh sift
bash scripts/hafta04/run_block.sh aliked sift exhaustive incremental
bash scripts/hafta04/run_block.sh loma aliked exhaustive incremental
python scripts/hafta04/dense_run.py loma exhaustive incremental

# Tablolar ve şekiller
python scripts/hafta04/collect.py
python scripts/hafta04/make_figures.py
python scripts/md_to_docx.py docs/raporlar/hafta-04_raporu.md docs/raporlar/hafta-04_raporu.docx
```

Not: SIFT bloğu tarihsel olarak `run_sift_3dgs.sh` ile koşulmuştur; varsayılan
hierarchical ve `sequential_loop` / `hierarchical_leaf100` varyantları sonradan
eklenmiştir. `run_block.sh sift` aynı sonucu tek seferde üretir.
