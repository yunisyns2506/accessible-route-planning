# Dokusuz iç mekân yüzeylerinde 3DGS: kök nedenler ve derinlik/normal öncülü (prior) yöntemleri

Bağlam: 4K el kamerası video, beyaz duvar / gri zemin derslik, COLMAP (LoMa/SIFT) + nerfstudio splatfacto (gsplat 1.4), Unity/VR görüntüleme, Colab L4/A100. Notlar İngilizce/Türkçe karışık; tüm sayılar kaynak tablolarından aynen alınmıştır.

## Soru 1 — Kök nedenler: 3DGS beyaz duvar/zemin/tavanda neden bulanık, yanlış ve floater'lı?

### Takeaway
Dört mekanizma üst üste biniyor: (1) SfM dokusuz bölgelerde çok seyrek nokta üretir → başlangıç Gaussianları yok/çok büyük; (2) sadece fotometrik kayıp, düz renkli yüzeyde geometriyi belirleyemez (yüzey eğri, delikli veya floater'lı olsa da aynı görüntü çıkar); (3) standart yoğunlaştırma (densification) gradyan ortalamasıyla çalıştığı için düşük gradyanlı büyük Gaussianlar bölünmez → bulanıklık/iğne artefaktı; (4) el kamerası hareket bulanıklığı ve pozlama/beyaz dengesi değişimleri, tutarsız renkleri "açıklamak" için sahte geometri (floater) üretir.

### Cited Findings
- **Seyrek SfM başlangıcı:** GaussianRoom, dokusuz bölgelerdeki kötü sonucu doğrudan "poor initialization of the SfM point cloud in textureless regions" ile açıklar; özette "incomplete and noisy reconstructions due to poor point cloud initialization" — [GaussianRoom, arXiv 2405.19671](https://arxiv.org/html/2405.19671v2)
- DN-Splatter ablasyonu (MuSHRoom): COLMAP SfM başlangıcı (~54.8K nokta) F1 = .9066, 1M sensör-derinlik noktasıyla başlatma F1 = .9381 (Tablo 5) — başlangıç yoğunluğu geometriyi ölçülebilir etkiliyor — [DN-Splatter, arXiv 2403.17822](https://arxiv.org/html/2403.17822v3)
- **Fotometrik belirsizlik:** PlanarGS: büyük, az dokulu yüzeyler çok az görünüm değişimi sağlar, sadece görünüm sinyali geometriyi çözemez; mevcut yöntemler düzlem olması gereken yerde "pürüzsüz ama eğri" yüzeyler üretir — [PlanarGS, arXiv 2510.23930](https://arxiv.org/html/2510.23930v1)
- DN-Splatter: "Textureless and less-observed regions cause ambiguities in reconstructions and do not provide enough constraints"; yalnız fotometrik kayıpla eğitilen Gaussian yöntemleri düşük dokulu ortamda geometriyi yakalamakta "severely struggle"; 2DGS de dokusuz bölgelerde zorlanır (Sec. 5.3) — [DN-Splatter](https://arxiv.org/html/2403.17822v3)
- 2DGS-Room: dokusuz bölgeler MVS için "geometric ambiguities" yaratır; Gaussian yöntemleri yapısal geometrik kısıttan yoksundur — [2DGS-Room, arXiv 2412.03428](https://arxiv.org/html/2412.03428v1)
- **Yoğunlaştırma davranışı:** Pixel-GS: başlangıç noktaları seyrek olan bölgelerde 3DGS bulanıklık ve "needle-like" artefakt üretir; neden, büyüme koşulunun görünür görüşler üzerinden *ortalama* gradyan büyüklüğünü kullanması — çok görüşte görünen ama çoğunlukla kenarından kapsanan büyük Gaussianlar büyümez. Çözüm: görüş başına kapsanan piksel sayısıyla ağırlıklı gradyan ortalaması + kameraya yakın floater büyümesini bastırmak için gradyanı kamera mesafesiyle ölçekleme — [Pixel-GS, arXiv 2403.15530](https://arxiv.org/abs/2403.15530)
- AbsGS: büyük Gaussianların aşırı-rekonstrükte bölgelerde bölünmemesini "gradient collision" ile açıklar (zıt yönlü piksel gradyanları birbirini götürür); çözüm "homodirectional" (mutlak) görünüm-uzayı gradyanı — [AbsGS, arXiv 2404.10484](https://arxiv.org/abs/2404.10484). gsplat'ta bu `DefaultStrategy(absgrad=True)` olarak mevcut — [gsplat simple_trainer.py](https://raw.githubusercontent.com/nerfstudio-project/gsplat/main/examples/simple_trainer.py)
- **Hareket bulanıklığı / rolling shutter:** "Gaussian Splatting on the Move" (ECCV 2024) el videosu için görüntü oluşumunu modeller; poz, pozlama süresi boyunca sabit kabul edilmez, VIO hızları kullanılır ve pozlar eğitimde iyileştirilir — [arXiv 2403.13327](https://arxiv.org/html/2403.13327v3). Aynı grup (Spectacular AI/Aalto) DN-Splatter'ın da yazarıdır.
- **Pozlama / beyaz dengesi:** Robust Gaussian Splatting (Darmon ve ark.) bulanıklığı poz dağılımı olarak modeller ve ortam ışığı, gölge, beyaz dengesi kaynaklı renk tutarsızlıkları için görüntü başına parametreli RGB decoder ekler — [arXiv 2404.04211](https://arxiv.org/html/2404.04211v1). PGSR de büyük aydınlatma değişimli sahneler için kamera pozlama telafisi modeli içerir — [PGSR, arXiv 2406.06521](https://arxiv.org/abs/2406.06521)
- gsplat'ta pozlama/renk telafisi seçenekleri: `post_processing: "bilateral_grid" | "ppisp"`, `bilateral_grid_shape=(16,16,8)`, TV düzenlemesi `10 * total_variation_loss(grids)`; ayrıca `app_opt` (görüntü başına appearance embedding, dim 16) — [gsplat simple_trainer.py](https://raw.githubusercontent.com/nerfstudio-project/gsplat/main/examples/simple_trainer.py). CasualHDRSplat tablosunda "gsplat+bilagrid" taban çizgisi olarak geçer — [arXiv 2504.17728](https://arxiv.org/pdf/2504.17728)

### Inferences
- Beyaz duvarda fotometrik kayıp neredeyse sıfır gradyan verir; derinlik/normal öncülü olmadan optimizasyonun duvar konumunu "doğru" bulması için hiçbir sinyal yoktur. Bu, NeRF literatüründeki shape–radiance ambiguity'nin (NeRF++, Zhang ve ark. 2020, arXiv 2010.07492 — bu oturumda ayrıca doğrulanmadı) Gaussian karşılığıdır; SH katsayıları görüşe bağlı rengi ezberleyerek yanlış geometriyi telafi edebilir.
- Pozlama/beyaz dengesi değişen 4K telefon videosunda, renk tutarsızlığı modele "farklı görüşte farklı renk" olarak öğretilir → yüksek dereceli SH ve kameraya yakın floater'lar. Bilateral grid / app_opt bunu kameraya özgü parametrelere aktararak geometriden ayırır. Pratik öneri: çekimde pozlama ve WB kilitlenmeli; eğitimde bilateral grid açılmalı.
- Seyrek SIFT/LoMa noktaları yüzünden gsplat'ın yerleşik derinlik kaybı (aşağıda) zaten duvarlarda neredeyse hiç denetim vermez — sorun tam da noktasız bölgelerde.

### Gaps
- SH aşırı uyumunun (view-dependent overfitting) dokusuz yüzeylerde floater ürettiğini nicel olarak gösteren 3DGS'e özgü bir makale bu oturumda bulunmadı.
- AbsGS ve Pixel-GS'in PSNR sayıları özet sayfalarında yoktu; çekilmedi.

## Soru 2 — Derinlik/normal öncülü kullanan yöntemler: ne yapıyor, sonuçlar, kod, entegrasyon

### Takeaway
Yoğun video ile iç mekân için en olgun ve nerfstudio-uyumlu seçenek **DN-Splatter** (Apache-2.0, 849★, `ns-train dn-splatter`). En yüksek raporlanan geometri **PlanarGS** (NeurIPS 2025; DUSt3R çok-görüş derinlik/normal + GroundedSAM düzlem maskeleri) ile; SDF tabanlı **GaussianRoom** ScanNet'te F-score'da çok güçlü ama ~4.5 saat eğitim. Seyrek-görüş yöntemleri (DNGaussian, FSGS, SparseGS) 3–10 kare senaryosu içindir; yoğun video için birincil seçim değildir.

### Cited Findings

#### DN-Splatter (WACV 2025) — nerfstudio eklentisi
- Ne yapar: 3DGS'i derinlik ve normal ipuçlarıyla düzenler; komşu Gaussianlar arası yerel pürüzsüzlük; hazır monoküler ağlar; renk-görüntü gradyanına dayalı uyarlanır (edge-aware) derinlik kaybı; doğrudan mesh çıkarımı — [arXiv 2403.17822](https://arxiv.org/abs/2403.17822), [WACV 2025](https://openaccess.thecvf.com/content/WACV2025/html/Turkulainen_DN-Splatter_Depth_and_Normal_Priors_for_Gaussian_Splatting_and_Meshing_WACV_2025_paper.html)
- Öncüller: derinlik için ZoeDepth, DepthAnything, Metric3D, MVSNet (SfM noktalarına ölçek hizalı); normal için Omnidata. Repo ayrıca DSINE normallerini destekler (`--normal-format dsine`) — [paper](https://arxiv.org/html/2403.17822v3), [GitHub](https://github.com/maturk/dn-splatter)
- **MuSHRoom mesh (Tablo 1, 6 sahne ort.)** — Splatfacto: Acc .0749 / Comp .0555 / C-L1 .0652 / NC .7727 / F1 .5835; **DN-Splatter: .0239 / .0194 / .0216 / .8822 / .9243** (aynı 1.18M Gaussian); 2DGS F1 .6039; MonoSDF F1 .9211 — [paper](https://arxiv.org/html/2403.17822v3)
- **ScanNet++ mesh (Tablo 2, 2 sahne)** — Splatfacto F1 .1790, C-L1 .1719, 8.9 dk; **DN-Splatter F1 .7658, C-L1 .0667, NC .8316, 36.9 dk**; MonoSDF F1 .8577 ama 47.5 dk; 2DGS F1 .4196 — [paper](https://arxiv.org/html/2403.17822v3)
- **MuSHRoom derinlik + NVS (Tablo 3)** — Splatfacto Abs Rel .0787, PSNR 24.44, SSIM .8486, LPIPS .1387; **DN-Splatter Abs Rel .0228, PSNR 24.58, SSIM .8558, LPIPS .1293** → geometri ~3.5× iyileşir, render kalitesi düşmez — [paper](https://arxiv.org/html/2403.17822v3)
- **Ablasyon (Tablo 4, MuSHRoom VR room, 4090):** Splatfacto F1 56.3, PSNR 26.6, 12.9 dk; +Normal F1 60.2; **+Derinlik F1 86.6, PSNR 27.1, 13.1 dk**; +Derinlik+Normal F1 87.7, NC 90.0, 17.5 dk → kazancın çoğu derinlik kaybından; normal kaybı NC'yi artırır, ~4 dk ekler — [paper](https://arxiv.org/html/2403.17822v3)
- **Derinlik kaybı türleri (Tablo 6, ScanNet++):** yok: AbsRel .1481; MSE .0551; L1 .0351; LogL1 .0364; EdgeAware (önerilen) .0285; PSNR 23.4–23.8 arasında — [paper](https://arxiv.org/html/2403.17822v3)
- **Derinlik kaynağı (Tablo 8, ScanNet++ tek sahne, F-score):** denetimsiz .1343; ZoeDepth .1455; Metric3D .1439; MVSNet .1903; **Pearson kaybı + Metric3D .2236**; iPhone sensör derinliği .5833 → monoküler derinlik için ölçek-bağımsız Pearson kaybı doğrudan L1'den belirgin daha iyi; sensör derinliği hâlâ çok önde — [paper](https://arxiv.org/html/2403.17822v3)
- **Tablo 7 (MuSHRoom):** DN-Splatter mono derinlik (Zoe) ile F1 .6963, PSNR 24.48; sensör derinliğiyle F1 .9243. 2DGS + mono derinlik F1 .5446 (2DGS'in kendisinden kötü!) — [paper](https://arxiv.org/html/2403.17822v3)
- Kod/entegrasyon: Apache-2.0, 849★, 74 fork; gsplat v1.0.0 desteği (Haziran 2024), son tarihli girdi AGS-Mesh (29.11.2024). Özel COLMAP verisi: `ns-train dn-splatter ... coolermap --data PATH` (`colmap/sparse/0/`). Bayraklar: `--pipeline.model.use-depth-loss True`, `--pipeline.model.depth-loss-type {MSE,LogL1,HuberL1,L1,EdgeAwareLogL1,PearsonDepth}` (mono için PearsonDepth önerilir), `--pipeline.model.depth-lambda 0.2`, `--pipeline.model.use-normal-loss True`, `--pipeline.model.use-normal-tv-loss True`, `--pipeline.model.normal-supervision {mono,depth}`. Mesh: `gs-mesh {dn,tsdf,o3dtsdf,sugar-coarse,gaussians,marching}` (o3dtsdf önerilir). Bilinen sorun: `align_depth.py` TypeError → Torch 2.1.2→2.0.1 düşürme — [GitHub](https://github.com/maturk/dn-splatter)

#### AGS-Mesh (arXiv 2411.19271, Kasım 2024) — DN-Splatter'ın devamı, aynı repoda
- Derinlik/normal öncüllerini eğitim sırasında tutarlılık kontrolüyle uyarlanır şekilde filtreler, belirsiz yerlerde düzenlemeyi azaltır; TSDF + octree tabanlı ölçek-farkında meshleme; akıllı telefonla oda taraması hedefli — [arXiv 2411.19271](https://arxiv.org/abs/2411.19271), kod [maturk/dn-splatter](https://github.com/maturk/dn-splatter)

#### GaussianRoom (arXiv 2405.19671, v2 Nisan 2025)
- Neural SDF + 3DGS ortak eğitim; SDF rehberli densification/pruning ve ızgara tabanlı global densification (SDF≈0 ve Gaussian seyrek bölgelere yeni Gaussian); monoküler normal öncülü hem Gaussian hem SDF normallerine; kenar öncülü ile örnekleme ve fotometrik ağırlık [1,2] — [arXiv](https://arxiv.org/html/2405.19671v2)
- **ScanNet / ScanNet++ F-score:** 3DGS .085 / .163; 2DGS .324 / –; DN-Splatter .166 / .107; MonoSDF .609 / .827; **GaussianRoom .768 / .872** — [arXiv](https://arxiv.org/html/2405.19671v2)
- **Render (ScanNet / ScanNet++ PSNR):** 3DGS 22.133 / 21.816; DN-Splatter 21.621 / 20.445; **GaussianRoom 23.601 / 22.001**; LPIPS ScanNet'te 3DGS'ten biraz kötü (.391 vs .387) — [arXiv](https://arxiv.org/html/2405.19671v2)
- Maliyet: ~4.5 saat (MonoSDF ~18 saat; "3DGS + monoküler ipuçları" ~1 saat); render >170 fps. Kod linki sayfada yok, proje sayfası: [xhd0612.github.io/GaussianRoom](https://xhd0612.github.io/GaussianRoom.github.io/)

#### PlanarGS (NeurIPS 2025, arXiv 2510.23930)
- LP3 hattı: GroundedSAM (Grounding DINO + SAM) ile "wall, floor, door, screen, window, ceiling, table" (+ "blackboard, sofa") istemleriyle düzlem bölgeleri; çok-görüş füzyonu; DUSt3R'dan derinlik+normal öncülü (monoküler Depth Anything yerine bilinçli tercih). Kayıplar: düzlem öncülü + geometrik öncül. VGGT ve YOLO-World+SAM ile değiştirmek sonucu az etkiler — [arXiv HTML](https://arxiv.org/html/2510.23930v1)
- **MuSHRoom (Tablo 1, cm / %):** 3DGS CD 11.92, F1 38.53, PSNR 25.79; 2DGS CD 9.71, F1 51.50; PGSR CD 10.51, F1 59.11; GOF CD 12.07; QGS CD 9.28; DN-Splatter CD 5.77, F1 61.86, NC 77.13, PSNR 24.80; **PlanarGS CD 4.49, F1 77.14, NC 83.35, PSNR 26.42, SSIM .8874** — [arXiv](https://arxiv.org/html/2510.23930v1)
- **ScanNet++ (Tablo 2):** DN-Splatter CD 4.16 / F1 75.86 / NC 82.06; PGSR F1 53.73; 2DGS F1 53.46; **PlanarGS CD 3.66 / F1 82.78 / NC 90.52**. **Replica:** DN-Splatter F1 68.12; **PlanarGS F1 81.90, NC 89.88** — [arXiv](https://arxiv.org/html/2510.23930v1)
- Maliyet: sahne başına <1 saat, RTX 3090, 30k iter; DUSt3R A6000 (48 GB) üzerinde çalıştırıldı. Kod: [SJTU-ViSYS-team/PlanarGS](https://github.com/SJTU-ViSYS-team/PlanarGS) — [proje](https://planargs.github.io)
- Sınırlama: düzlem öncülü yalnız tespit edilen düz bölgelerde yardımcı; eğri duvar/dış mekânda değil — [arama özeti, PlanarGS](https://arxiv.org/pdf/2510.23930)

#### 2DGS-Room (arXiv 2412.03428, Aralık 2024)
- 2DGS + filtrelenmiş SfM'den voksel "seed" noktaları; derinlik Depth Pro, normal Bae ve ark. 2021 tahmincisi; 7k iter sonrası çok-görüş geometrik + NCC fotometrik kayıp; RTX 4090, 30k iter, NeRF/SDF'den ~30× hızlı — [arXiv](https://arxiv.org/html/2412.03428v1)
- F-score: ScanNet 2DGS .341 → **.575**; ScanNet++ 2DGS .183 → **.464**; PSNR raporlanmaz; kod linki yok, proje: [valentina-zhang.github.io/2DGS-Room](https://valentina-zhang.github.io/2DGS-Room/) — [arXiv](https://arxiv.org/html/2412.03428v1)

#### VCR-GauS (arXiv 2406.05774)
- Normali Gaussian'ın diğer geometrik parametrelerine bağlayan view-consistent depth-normal düzenleyici; çok-görüş tutarsız normal tahminleri için güven terimi; boyut/dağılım düzenleyen densification; 100+ FPS — [arXiv](https://arxiv.org/abs/2406.05774), [proje](https://hlinchen.github.io/projects/VCR-GauS/)

#### PGSR (TVCG 2024, arXiv 2406.06521)
- Düzlemsel Gaussian; kamera→düzlem mesafesi / normal ile yansız (unbiased) derinlik; tek-görüş geometrik + çok-görüş fotometrik/geometrik tutarlılık; pozlama telafisi — [arXiv](https://arxiv.org/abs/2406.06521), [proje](https://zju3dv.github.io/pgsr). Öncülsüz olduğu için iç mekânda PlanarGS tablolarında DN-Splatter'ın gerisinde (ScanNet++ F1 53.73 vs 75.86) — [PlanarGS](https://arxiv.org/html/2510.23930v1)

#### IndoorGS (CVPR 2025)
- Monoküler derinlik, seyrek SfM noktaları ve çizgilerden düzlem-benzeri ipuçları; zayıf dokulu bölgeleri SIFT nokta yoğunluğuyla işaretler (yalnız ek materyal görüldü) — [CVPR 2025 supplemental](https://openaccess.thecvf.com/content/CVPR2025/supplemental/Ruan_IndoorGS_Geometric_Cues_CVPR_2025_supplemental.pdf)

#### Seyrek-görüş yöntemleri (DNGaussian vb.)
- DNGaussian (CVPR 2024): Hard/Soft derinlik düzenlemesi + Global-Local Depth Normalization (yerel derinlik yamalarını normalize ederek küçük derinlik değişimlerine odak); DPT monoküler derinlik; LLFF/DTU/Blender; 25× daha hızlı eğitim; derinlik modeli değişimi LLFF PSNR'ı ~19.0–19.1 dB aralığında tutar (3-görüş ablasyonu) — [arXiv 2403.06912](https://arxiv.org/pdf/2403.06912), [GitHub](https://github.com/Fictionarry/DNGaussian)
- 2026 bir çalışma: Splatfacto, seyrek KITTI sahnelerinde maskeli monoküler derinlik denetiminden fayda görür (PSNR 14.903 → 15.932); başka bir 2026 çalışma, iyi rekonstrükte bölgelerde naif monoküler derinlik denetiminin performansı düşürebileceğini not eder — [arXiv 2607.02554](https://arxiv.org/pdf/2607.02554), [arXiv 2604.05715](https://arxiv.org/pdf/2604.05715)

#### gsplat / nerfstudio yerleşik derinlik desteği
- gsplat `simple_trainer.py`: `depth_loss: bool = False` ("experimental"), `depth_lambda = 1e-2`; render modu "RGB+ED"; kayıp `depth_l1_loss(...)` disparity uzayında — [simple_trainer.py](https://raw.githubusercontent.com/nerfstudio-project/gsplat/main/examples/simple_trainer.py)
- Derinlik kaynağı: **yalnızca o görüntüde görülen seyrek COLMAP 3B noktaları** kameraya projekte edilir (`depths = points_cam[:, 2]`, görüntü içi ve depth>0 filtresi) — [gsplat datasets/colmap.py](https://raw.githubusercontent.com/nerfstudio-project/gsplat/main/examples/datasets/colmap.py)
- DN-Splatter'ın WACV ek materyali: taban çizgisi nerfstudio 1.1.3 Splatfacto + gsplat 1.0.0; Depth-Nerfacto sensör derinliği için DS-NeRF tarzı ışın sonlanma kaybı kullanır — [WACV supplemental](https://openaccess.thecvf.com/content/WACV2025/supplemental/Turkulainen_DN-Splatter_Depth_and_WACV_2025_supplemental.pdf). Depth-Nerfacto MuSHRoom'da F1 .6966 (Nerfacto .7212'den bile düşük) — [DN-Splatter](https://arxiv.org/html/2403.17822v3)

### Inferences
- gsplat'ın yerleşik `depth_loss`'u SfM noktalarını kullandığı için beyaz duvarda (nokta yok) neredeyse etkisizdir; dokusuz yüzey için **yoğun** (dense) monoküler/çok-görüş derinlik haritası gerekir → DN-Splatter'ın `align_depth.py` + PearsonDepth yolu veya kendi yoğun derinlik kaybınız.
- Mono derinlikte ölçek-bağımsız (Pearson / scale-shift hizalı) kayıp şart: DN-Splatter Tablo 8'de Metric3D ile doğrudan kayıp F .1439, Pearson ile .2236.
- Normal kaybı tek başına zayıf (F1 56.3→60.2), derinlikle birlikte NC'yi yükseltir; duvar düzlüğü (VR'da "dalgalı duvar" algısı) için NC önemlidir, bu yüzden ikisi birlikte önerilir.
- Splatfacto'ya göre süre artışı küçük (12.9 → 17.5 dk, 4090); L4'te ~2× daha yavaş beklenebilir (çıkarım, ölçülmedi).
- Bina ölçeği için: PlanarGS'in "wall/floor/ceiling" istemli düzlem öncülü tam bu senaryoya uyuyor; fakat DUSt3R adımı 48 GB GPU kullanmış — Colab A100 40GB'de çalıştırılabilirliği doğrulanmalı veya VGGT varyantı denenmeli.

### Gaps
- MonoGSDF, FSGS, SparseGS, DepthSplat, Gaussian Opacity Fields'in normal varyantı ve 2025–2026 yeni öncül modellerinin (Depth Anything v2, Metric3D v2, DSINE, StableNormal, Marigold, MoGe) 3DGS içinde karşılaştırmalı sayıları bu oturumda çekilmedi (araç çağrısı sınırı).
- VCR-GauS, PGSR, AGS-Mesh için nicel tablolar, lisanslar ve repo yıldızları alınmadı; PlanarGS ve GaussianRoom kod lisansı doğrulanmadı.
- gsplat 1.4 sürümünde `depth_loss`'un tam olarak aynı olup olmadığı (main dalı okundu) doğrulanmadı; nerfstudio splatfacto'nun çekirdekte derinlik kaybı bayrağı olup olmadığı bulunamadı.
- DN-Splatter'ın gsplat 1.4 / güncel nerfstudio ile uyumluluğu (son commit tarihi) doğrulanmadı.

## Soru 3 — İç mekân dokusuz duvarlarda hangisi en iyi (raporlanan karşılaştırmalara göre)?

### Takeaway
Aynı tablolardaki doğrudan karşılaştırmalarda sıralama: **PlanarGS > DN-Splatter > PGSR ≈ 2DGS ≈ QGS > GOF ≈ 3DGS/Splatfacto** (MuSHRoom, ScanNet++, Replica). GaussianRoom ScanNet/ScanNet++'ta DN-Splatter'ı geçiyor ama farklı protokolle; GaussianRoom ile PlanarGS doğrudan karşılaştırılmamış. Pratikte: derslik için ilk adım DN-Splatter (PearsonDepth + mono normal), geometri kritikse PlanarGS.

### Cited Findings
- PlanarGS tablolarında (aynı protokol) MuSHRoom F1: PlanarGS 77.14 > DN-Splatter 61.86 > PGSR 59.11 > QGS 55.15 > 2DGS 51.50 > GOF 42.57 > 3DGS 38.53; PSNR'da da PlanarGS en iyi (26.42), DN-Splatter 24.80 (3DGS 25.79'un altında) — [PlanarGS](https://arxiv.org/html/2510.23930v1)
- ScanNet++ F1: PlanarGS 82.78 > DN-Splatter 75.86 > GOF 57.99 > PGSR 53.73 ≈ 2DGS 53.46 > DUSt3R 38.17 > 3DGS 31.78 — [PlanarGS](https://arxiv.org/html/2510.23930v1)
- GaussianRoom tablosunda DN-Splatter ScanNet++ F-score .107 (GaussianRoom .872), oysa PlanarGS tablosunda DN-Splatter ScanNet++ F1 %75.86 ve DN-Splatter'ın kendi makalesinde ScanNet++ F1 .7658 — protokol/derinlik kaynağı farkı (DN-Splatter kendi tablolarında sensör derinliği kullanır) nedeniyle sayılar **çelişkili** — [GaussianRoom](https://arxiv.org/html/2405.19671v2) vs [PlanarGS](https://arxiv.org/html/2510.23930v1) vs [DN-Splatter](https://arxiv.org/html/2403.17822v3)
- 2DGS-Room'un ScanNet++ F-score'u .464, GaussianRoom'un .872 — farklı sahne/protokol, doğrudan karşılaştırılamaz — [2DGS-Room](https://arxiv.org/html/2412.03428v1), [GaussianRoom](https://arxiv.org/html/2405.19671v2)
- Öncülsüz yüzey yöntemleri (2DGS, PGSR, GOF) iç mekânda öncüllü yöntemlerin belirgin gerisinde; 2DGS'e naif mono derinlik eklemek F1'i düşürdü (.6039 → .5446) — [DN-Splatter Tablo 7](https://arxiv.org/html/2403.17822v3)

### Inferences
- Kullanıcının hattı (COLMAP + nerfstudio + gsplat) için entegrasyon maliyeti en düşük ve kanıtı en sağlam seçenek DN-Splatter (`coolermap` dataparser doğrudan COLMAP sparse/0 okur). Telefon LiDAR'ı yoksa beklenen kazanç sensör-derinlikli sayılardan (F1 .92) değil mono-derinlikli sayılardan (F1 ~.70, Tablo 7) tahmin edilmeli.
- Mono öncüllerin sınırı çok-görüş tutarsızlığı; PlanarGS (DUSt3R/VGGT) ve AGS-Mesh (tutarlılık filtresi) tam bunu hedefliyor — bina ölçeğinde çok sayıda düz alan için bu iki yaklaşım en umut verici.
- Geometri öncülleri tek başına bulanıklığı çözmez: el videosunda motion blur ve pozlama değişimi ayrı ele alınmalı (keskin kare seçimi, pozlama/WB kilidi, gsplat bilateral grid/app_opt, absgrad).

### Gaps
- Bu yöntemlerin el kamerası 4K video + COLMAP pozlarıyla (sensör derinliği olmadan) karşılaştırıldığı bir benchmark bulunamadı; MuSHRoom kısmen iPhone/Kinect verisi içerir.
- Unity/VR'a aktarım (PLY uyumluluğu; 2DGS/PlanarGS'in standart 3DGS PLY ile uyumu) incelenmedi.
