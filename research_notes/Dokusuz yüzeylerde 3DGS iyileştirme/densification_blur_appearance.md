# 3DGS Improvements in Densification, Anti-Aliasing/Deblurring and Appearance/Exposure Modeling (2023–2026), for Blurry Low-Texture Indoor Surfaces and Floaters

Context: classroom reconstructed from 4K handheld video (motion blur, possible auto-exposure drift), COLMAP + nerfstudio splatfacto / splatfacto-big (gsplat 1.4), viewed in Unity/VR. Current model: ~25.6 dB PSNR, SSIM 0.91, LPIPS 0.21 on held-out frames. White walls, floors and ceilings look blurry.

## Q1. Densification: why default ADC under-reconstructs low-gradient regions, which fixes exist, and what gsplat/nerfstudio already expose

### Takeaway
Vanilla ADC splits or clones a Gaussian only when its view-averaged 2D positional gradient passes a threshold. Large Gaussians on flat, low-texture surfaces get small or cancelling gradients, so they never split and stay as big blurry blobs. The most important practical point: **nerfstudio splatfacto already uses absgrad by default** (`use_absgrad=True`, `densify_grad_thresh=0.0008`), and splatfacto-big only lowers that threshold to 0.0005. The remaining levers are a lower absgrad threshold, the MCMC strategy (`splatfacto-mcmc`) with a larger Gaussian budget, scale regularization, and Pixel-GS-style pixel-weighted gradients (not in gsplat/nerfstudio). In gsplat's own MipNeRF360 benchmark, absgrad gave +0.11 dB and LPIPS 0.14→0.12 with fewer Gaussians. MCMC gave +0.18 dB at 1M Gaussians and up to about +0.6 dB per scene at 3M.

### Cited Findings
**Mechanism (why large blurry Gaussians survive)**
- Pixel-GS (Zhang, Hu, Lao, He, Zhao; arXiv 2403.15530, ECCV 2024): 3DGS's growth condition averages gradients across views without accounting for how many pixels the Gaussian covers in each view. As a result, large Gaussians that are visible in many views, but cover only boundary regions in many of them, fail to grow. This produces blur and needle-like artifacts where the initial SfM points are sparse. — [arXiv 2403.15530](https://arxiv.org/abs/2403.15530); [ECCV paper](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/02926.pdf)
- Pixel-GS fix 1: weight each view's gradient by the number of pixels the Gaussian covers, which promotes growth of large Gaussians in under-initialized areas. Fix 2: scale the gradient field by distance to the camera to suppress **floaters near the camera**. Claimed SOTA on Mip-NeRF360 and Tanks & Temples. — [arXiv 2403.15530](https://arxiv.org/abs/2403.15530)
- AbsGS (Ye, Li, Liu, Qiao, Dou; arXiv 2404.10484): ADC "frequently suffers from over-reconstruction issue in intricate scenes," which shows up as blur. The cause is **gradient collision**: the signed per-pixel gradients of a large Gaussian cancel, so it is never split. The fix is to accumulate the homodirectional (absolute) view-space gradient, so large Gaussians in over-reconstructed regions are identified and split. — [arXiv 2404.10484](https://arxiv.org/abs/2404.10484)
- The gsplat paper describes absgrad as accumulating absolute values of view-space gradients instead of signed sums, "which avoids gradient cancellation". — [gsplat paper arXiv 2409.06765](https://arxiv.org/html/2409.06765)
- Revising Densification (Rota Bulò, Porzi, Kontschieder; arXiv 2404.06109): replaces the gradient criterion with a **per-pixel error-driven** density control, adds a cap on total primitives per scene, and corrects a bias in opacity handling during cloning. The abstract reports "consistent quality improvements" but gives no numbers. — [arXiv 2404.06109](https://arxiv.org/abs/2404.06109)
- 3DGS-MCMC (Kheradmand et al.; arXiv 2404.09591): treats the Gaussians as MCMC samples and Gaussian updates as SGLD with noise. Clone/split heuristics become relocalization of dead Gaussians, and an opacity/scale regularizer removes unused ones. Claimed benefits are better quality, explicit control of the Gaussian count, and robustness to initialization (abstract has no numbers). — [arXiv 2404.09591](https://arxiv.org/abs/2404.09591)

**Quantitative (gsplat's own benchmark, MipNeRF360, 7-scene average, 30k steps; arXiv 2409.06765 Table 2)**

| Config | PSNR | SSIM | LPIPS | #GS | Mem | Time |
|---|---|---|---|---|---|---|
| gsplat default ADC | 29.00 | 0.87 | 0.14 | 3.24 M | 5.62 GB | 19.39 min |
| w/ absgrad | 29.11 | 0.88 | 0.12 | 2.47 M | 4.40 GB | 18.10 min |
| w/ mcmc (1M cap) | 29.18 | 0.87 | 0.14 | 1.00 M | 1.98 GB | 15.42 min |
| w/ antialiased | 29.03 | 0.87 | 0.14 | 3.38 M | 5.87 GB | 19.52 min |
— [gsplat paper](https://arxiv.org/html/2409.06765)
- Indoor scenes in the same per-scene tables. Room PSNR: default 31.23, absgrad 31.43, MCMC-1M 32.01, MCMC-2M 32.34, MCMC-3M 32.40. Room LPIPS: 0.17 (default), 0.15 (absgrad), 0.14 (MCMC-2M/3M). Counter PSNR: 29.01, 29.07, 29.40, 29.56, 29.65. MCMC-3M memory is about 5.4 GB on room. — [gsplat paper](https://arxiv.org/html/2409.06765)
- Third-party comparisons (Mip-NeRF360, 3DGS resolution) differ by setup:
  - GDAGS: Pixel-GS* 27.67 dB at ~1.2 GB; AbsGS-0004 27.49 dB at 728 MB; AbsGS-0008 27.41 dB at 450 MB. GDAGS argues AbsGS over-densifies with little quality gain. — [GDAGS arXiv 2508.09239](https://arxiv.org/html/2508.09239v1)
  - ResGS: baseline 27.69, AbsGS 27.49 (728 MB), Pixel-GS* 27.52 (1.32 GB), residual-split variant 27.94 (342 MB). — [ResGS arXiv 2412.07494 (ICCV 2025)](https://arxiv.org/html/2412.07494)
  - Pixel-GS's own ablation: 27.88 vs 27.83 for 3DGS. — via search summary of [Pixel-GS ECCV paper](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/02926.pdf) (not independently verified)
- Taming 3DGS: about 27.85 dB with ~3.3M Gaussians vs 3DGS 27.55 at the same count, and 30.07 dB with 2.8M Gaussians on a second dataset. Mini-Splatting2-Dense: 27.56 dB with 3.6M Gaussians at 18K iterations. These are from a third-party table whose dataset labels were unclear. — [arXiv 2603.09277](https://arxiv.org/html/2603.09277v1)
- Other density-control papers found but whose numbers I did not verify: Mini-Splatting ([arXiv 2403.14166](https://arxiv.org/pdf/2403.14166)), Efficient Density Control / EDC ([arXiv 2411.10133](https://arxiv.org/pdf/2411.10133)), Improving Densification / Improved-GS ([arXiv 2508.12313](https://arxiv.org/pdf/2508.12313)), Structure-aware densification (Mip-NeRF360 ablation: 27.25 dB with AbsGS densification vs 27.12 without, 4.05M vs 3.51M Gaussians) ([arXiv 2604.28016](https://arxiv.org/pdf/2604.28016)).

**What is available in gsplat (DefaultStrategy / MCMCStrategy; source `gsplat/strategy/default.py`)**
- `DefaultStrategy` parameters and defaults:
  - Growth: `grow_grad2d=0.0002`, `grow_scale3d=0.01`, `grow_scale2d=0.05`.
  - Pruning: `prune_opa=0.005`, `prune_scale3d=0.1`, `prune_scale2d=0.15`.
  - Schedule: `refine_scale2d_stop_iter=0` (disabled), `refine_start_iter=500`, `refine_stop_iter=15_000`, `reset_every=3000`, `refine_every=100`, `pause_refine_after_reset=0` (the docstring suggests setting it to the number of training images).
  - Absgrad: `absgrad=False` by default. The docstring says it typically gives better results but needs a higher `grow_grad2d`, e.g. 0.0008, and `rasterization(..., absgrad=True)`.
  - Revised opacity: `revised_opacity=False`, described as an "experimental" heuristic from arXiv:2404.06109 (Bulò et al.). Only the opacity-bias correction is implemented, not the full error-based densification.
  - `key_for_gradient="means2d"`.
  — [gsplat default.py](https://raw.githubusercontent.com/nerfstudio-project/gsplat/main/gsplat/strategy/default.py)
- gsplat `examples/simple_trainer.py`: `strategy: Union[DefaultStrategy, MCMCStrategy]`. The `mcmc` subcommand sets `init_opa=0.5`, `init_scale=0.1`, `opacity_reg=0.01`, `scale_reg=0.01`. The trainer reads `cfg.strategy.absgrad` for DefaultStrategy. — [simple_trainer.py](https://raw.githubusercontent.com/nerfstudio-project/gsplat/main/examples/simple_trainer.py)

**What is available in nerfstudio splatfacto (`SplatfactoModelConfig`, current main)**
- Densification: `densify_grad_thresh=0.0008`, `use_absgrad=True` ("if False, will use grad rather than absgrad"), `densify_size_thresh=0.01`, `n_split_samples=2`, `split_screen_size=0.05`, `stop_split_at=15000`.
- Schedule: `warmup_length=500`, `refine_every=100`, `reset_alpha_every=30` (in refinement steps).
- Culling: `cull_alpha_thresh=0.1` (the comment suggests 0.005 "for higher quality"), `cull_scale_thresh=0.5`, `cull_screen_size=0.15`, `stop_screen_size_at=4000`.
- Scale regularization: `use_scale_regularization=False` (PhysGauss-style; reduces huge spiky Gaussians) with `max_gauss_ratio=10.0`.
- Strategy: `strategy: "default"|"mcmc"`, `max_gs_num=1_000_000`, `noise_lr=5e5`, `mcmc_opacity_reg=0.01`, `mcmc_scale_reg=0.01`.
— [splatfacto.py](https://raw.githubusercontent.com/nerfstudio-project/nerfstudio/main/nerfstudio/models/splatfacto.py)
- Method presets (`method_configs.py`):
  - **splatfacto-big** = splatfacto with `cull_alpha_thresh=0.005`, `densify_grad_thresh=0.0005`.
  - **splatfacto-mcmc** = `strategy="mcmc"`, `cull_alpha_thresh=0.005`, `stop_split_at=25000`.
  - All presets: 30,000 iterations, the same optimizers (including `camera_opt` lr 1e-4→5e-7 and `bilateral_grid` lr 2e-3→1e-4, both with 1000 warmup steps).
  — [method_configs.py](https://raw.githubusercontent.com/nerfstudio-project/nerfstudio/main/nerfstudio/configs/method_configs.py)

### Inferences
- The setup already runs absgrad. Switching to "absgrad" will not help; the threshold value and the Gaussian budget are the levers. For white walls, candidates are:
  - Lowering `--pipeline.model.densify-grad-thresh` below 0.0005 (e.g. 0.0003–0.0004).
  - `splatfacto-mcmc` with `--pipeline.model.max-gs-num` of 2–3M. gsplat's indoor "room" scene gained +0.8–1.2 dB over default ADC.
  - `--pipeline.model.use-scale-regularization True` to break up huge anisotropic wall Gaussians.
  CLI names follow nerfstudio/tyro's underscore→hyphen convention. They are derived from the config field names, not tested here.
- Some wall "blur" may not be a densification failure. Truly textureless walls are correctly represented by a few large Gaussians. Perceived blur then comes from motion-blurred training frames (Q3) or exposure inconsistency (Q4) being averaged into the wall color. Densification fixes alone may raise #GS without visible gain there.
- Pixel-GS's distance-scaled gradient specifically targets near-camera floaters, which are typical in handheld indoor capture. It is not in gsplat/nerfstudio and would need porting (a small change to how gradients are accumulated in the strategy).
- MCMC's random relocalization plus opacity/scale regularizers tends to reduce floaters compared with clone/split, and gives a hard Gaussian cap. A hard cap is useful for VR/Unity frame-rate budgets.

### Gaps
- I did not verify primary-paper tables for Taming 3DGS, Mini-Splatting2, EDC, Improved-GS, Perceptual-GS or Steepest Descent Density Control (SteepGS). No arXiv IDs or numbers for Perceptual-GS or SteepGS were verified in this session.
- I found no ScanNet++ results for these densification methods, and none specific to textureless indoor walls.
- The Revising Densification paper's quantitative gains were not retrieved; the abstract has no numbers.

## Q2. Anti-aliasing / scale: Mip-Splatting, Analytic-Splatting, gsplat antialiased mode, VR viewing distances

### Takeaway
Mip-Splatting (CVPR 2024 best student paper) adds a 3D smoothing filter, which caps Gaussian frequency at the training views' Nyquist limit, and a 2D Mip filter in place of the screen-space dilation. gsplat/nerfstudio implement the 2D part as `rasterize_mode="antialiased"` (splatfacto) or `antialiased=True` (gsplat). This mode does not raise single-scale PSNR (29.00→29.03 on MipNeRF360). Its value is consistency when the render resolution or distance differs from training, which is the VR case. **Caveat:** antialiased PLYs are not compatible with classic-mode viewers, which matters for Unity import.

### Cited Findings
- Mip-Splatting: the 3D smoothing filter limits the maximum frequency of 3D Gaussians to the Nyquist limit of the training views and becomes part of the representation. The 2D Mip filter approximates a pixel box filter, replacing 3DGS's 2D dilation. Removing the 3D filter causes high-frequency artifacts when zooming in. Removing the 2D filter causes aliasing and degradation when zooming out. Code: autonomousvision/mip-splatting, with a script to fuse the 3D filter into the Gaussian parameters. — [CVPR paper](https://openaccess.thecvf.com/content/CVPR2024/papers/Yu_Mip-Splatting_Alias-free_3D_Gaussian_Splatting_CVPR_2024_paper.pdf); [GitHub](https://github.com/autonomousvision/mip-splatting)
- Analytic-Splatting (arXiv 2403.11056): analytically approximates the pixel-window integral instead of using a Gaussian low-pass. It argues Mip-Splatting "synthesizes over-smoothing results" and suppresses high-frequency detail. — [arXiv 2403.11056](https://arxiv.org/html/2403.11056v2)
- gsplat's anti-aliasing is based on Mip-Splatting. A low-pass filter on projected 2D covariances keeps each Gaussian at least about one pixel wide, which reduces aliasing at lower resolution or larger distance. MipNeRF360 single-scale: 29.03 dB / 0.87 / 0.14, 3.38M GS vs default 29.00 / 0.87 / 0.14, 3.24M GS. — [gsplat paper](https://arxiv.org/html/2409.06765)
- nerfstudio `rasterize_mode: Literal["classic","antialiased"]="classic"`. Classic uses EWA splatting with a fixed screen-space blur, which can alias at other resolutions. Antialiased compensates opacities to preserve integrated density. Antialiased PLYs are not compatible with classic-mode viewers. gsplat `simple_trainer.py`: `antialiased=False` by default. — [splatfacto.py](https://raw.githubusercontent.com/nerfstudio-project/nerfstudio/main/nerfstudio/models/splatfacto.py); [simple_trainer.py](https://raw.githubusercontent.com/nerfstudio-project/gsplat/main/examples/simple_trainer.py)

### Inferences
- In VR the HMD's effective pixel footprint differs from the 4K training frames. Walls seen far away or at grazing angles shimmer in classic mode, and close-ups of thin Gaussians look "dilated". Training with `--pipeline.model.rasterize-mode antialiased` is cheap (+~0.6% time in the gsplat table). It is only useful if the Unity renderer applies the same 2D Mip filter / opacity compensation; otherwise opacities will look wrong.
- Anti-aliasing will not fix blur caused by motion-blurred training images or under-densification. Mip-Splatting's 3D filter actually enforces smoothness, so it is not a fix for "blurry walls".

### Gaps
- Mip-Splatting's multi-scale numbers (e.g. multi-scale Blender / single-to-multi-scale Mip-NeRF360 tables) were not retrieved in this session.
- I found no evaluation of anti-aliasing specifically for VR/HMD viewing. Whether common Unity splat plugins support the antialiased-mode opacity compensation was not verified.

## Q3. Deblurring and motion blur / rolling shutter for handheld video

### Takeaway
For handheld video with COLMAP poses, the most directly usable option is **SpectacularAI's 3dgs-deblur ("Gaussian Splatting on the Move", ECCV 2024)**. It is a fork of nerfstudio splatfacto with a one-script video pipeline, motion-blur compensation, and optional rolling-shutter compensation (`ROLLING_SHUTTER=ON`). It works without IMU, with velocities initialized to zero, but it pins old nerfstudio 1.1.0 / gsplat 0.1.11. **BAD-Gaussians (ECCV 2024)** is also a nerfstudio method (`ns-train bad-gaussians`). It models the in-exposure trajectory with a spline, trains in about 30 min, and leads on synthetic Deblur-NeRF PSNR (28.37 vs 24.17 for Deblurring-3DGS and 24.61 for BAGS in a third-party table). Real-data advantages are smaller. A cheaper first step is to drop the blurriest frames before COLMAP and enable splatfacto's camera optimizer.

### Cited Findings
- Gaussian Splatting on the Move (Seiskari et al., arXiv 2403.13327, ECCV 2024): models image formation with motion blur and rolling shutter, uses VIO velocities, and optimizes poses during reconstruction. The abstract has no numbers. — [arXiv 2403.13327](https://arxiv.org/abs/2403.13327)
- 3dgs-deblur repo:
  - Built on SpectacularAI forks: v2 uses nerfstudio 1.1.0 + gsplat 0.1.11; v1 uses nerfstudio 1.0.2 + gsplat 0.1.8. Requires Linux and an RTX GPU with ≥8 GB.
  - Custom video: `./scripts/process_and_train_video.sh /path/to/video.mp4` (motion blur). Add `ROLLING_SHUTTER=ON` for rolling shutter. The video pipeline is COLMAP-based.
  - Other flags: `--optimize-eval-cameras`, `--optimize-eval-velocities=True`, `--min-rgb-level`.
  - Without IMU, velocities start at zero. Plain video supports motion blur *or* rolling shutter. Combining both needs known readout/exposure times (Spectacular Rec data).
  — [GitHub SpectacularAI/3dgs-deblur](https://github.com/SpectacularAI/3dgs-deblur)
- BAD-Gaussians (Zhao, Wang, Liu; arXiv 2403.11831, ECCV 2024):
  - Models camera motion during exposure with a spline and jointly optimizes the trajectory and the Gaussians.
  - Reports >200 FPS rendering and about 30 min training vs >10 h for compared NeRF methods.
  - Install with `pip install -e .`, train with `ns-train bad-gaussians`.
  - Quantitative eval needs sharp GT images, which only synthetic data have. For real captures the maintainers suggest the standard nerfstudio dataparser for a train/eval split.
  — [arXiv 2403.11831](https://arxiv.org/pdf/2403.11831); [GitHub issue](https://github.com/WU-CVGL/BAD-Gaussians/issues/3); [ECCV paper](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/03633.pdf)
- Third-party comparison on Deblur-NeRF synthetic (RoMo-GS table): BAD-Gaussians 28.367 dB, Deblurring 3DGS 24.174, BAGS 24.606. The authors note BAD-Gaussians needed about 4 h of offline optimization. — [RoMo-GS arXiv 2610.24605](https://arxiv.org/html/2610.24605)
- On real ExbluRF scenes, BAD-Gaussians has relatively good LPIPS but lower PSNR/SSIM, "indicating that their camera poses are not properly optimized" (CoMoGaussian). — [CoMoGaussian arXiv 2503.05332](https://arxiv.org/pdf/2503.05332)
- BAGS (arXiv 2403.04926): blur-agnostic multi-scale kernel modeling. It reports gains mainly in LPIPS and notes that PSNR is unreliable because GT images have different exposure from the training images. — [arXiv 2403.04926](https://arxiv.org/pdf/2403.04926)
- Related 2025 work: Casual3DHDR (deblurring + HDR from casually captured video, arXiv 2504.17728), GeMS (extreme motion blur, arXiv 2508.14682), CoMoGaussian (continuous motion). — [Casual3DHDR](https://arxiv.org/pdf/2504.17728); [GeMS](https://arxiv.org/pdf/2508.14682); [CoMoGaussian](https://arxiv.org/pdf/2503.05332)
- gsplat `simple_trainer.py` has no rolling-shutter option. The 3DGUT-related flags are `with_ut` and `with_eval3d`, and `with_eval3d` is incompatible with DefaultStrategy. — [simple_trainer.py](https://raw.githubusercontent.com/nerfstudio-project/gsplat/main/examples/simple_trainer.py)
- splatfacto `camera_optimizer` defaults to `CameraOptimizerConfig(mode="off")`. The `camera_opt` optimizer is preconfigured (Adam lr 1e-4→5e-7). — [splatfacto.py](https://raw.githubusercontent.com/nerfstudio-project/nerfstudio/main/nerfstudio/models/splatfacto.py); [method_configs.py](https://raw.githubusercontent.com/nerfstudio-project/nerfstudio/main/nerfstudio/configs/method_configs.py)

### Inferences
- On white walls, motion blur hardly changes per-pixel color, so it adds little error locally. Blur at wall edges, posters and the board makes the optimizer fit soft edges, which spreads into the large wall Gaussians. Deblur models mostly sharpen edges and texture, not uniform areas.
- Practical ladder from cheapest to most expensive:
  1. Pre-filter frames with a sharpness metric (e.g. variance of Laplacian), keeping the sharpest frame per time window. This matches the planned 500–1000 frames from 4K video.
  2. `--pipeline.model.camera-optimizer.mode SO3xR3` (nerfstudio CameraOptimizer mode name; not tested here).
  3. 3dgs-deblur or BAD-Gaussians as a separate run. Their old nerfstudio/gsplat pins mean a separate Colab environment, and PLY export compatibility with the current pipeline must be checked.
- Phone/consumer 4K video normally uses a CMOS rolling shutter. With fast pans, the rolling-shutter mode of 3dgs-deblur is the only verified ready-made option found.

### Gaps
- I did not retrieve primary-paper numbers for Deblurring 3DGS (Lee et al.), DeblurGS or MBA-SLAM.
- I found no evaluation of deblurring methods on ScanNet++ or indoor classroom-like data. No verified integration of deblurring in current nerfstudio main / gsplat 1.4+ was found.

## Q4. Appearance / exposure modeling: embeddings, bilateral grids, PPISP, in-the-wild methods

### Takeaway
Auto-exposure and white-balance drift across a handheld video are absorbed by the 3DGS colors as view-dependent "floaters" and smeared wall colors unless they are modeled explicitly. Ready-to-use options:
- **splatfacto `use_bilateral_grid=True`** (BilaRF, SIGGRAPH 2024; grid 16×16×8): a per-image, image-space affine correction.
- **gsplat `post_processing="bilateral_grid"` or `"ppisp"`**: PPISP is NVIDIA's CVPR 2026 physically plausible ISP (exposure, vignetting, color correction, CRF, plus a controller for novel views).
- **gsplat `app_opt=True`**: per-image embedding plus a color MLP.
In-the-wild methods (Splatfacto-W, WildGaussians, GS-W, Luminance-GS) target tourist photos with much larger lighting and occluder changes.

### Cited Findings
- BilaRF (Wang, Wang, Gong, Xue; arXiv 2406.00448, ACM TOG 43(4), SIGGRAPH 2024): a differentiable 3D bilateral grid acting as a per-view locally affine ISP model during training, plus a low-rank 4D grid for lifting 2D edits to 3D. Code: yuehaowang/bilarf. A 3DGS/splatfacto port ("bilags") observed about a 20% training slowdown. The method was merged into nerfstudio Splatfacto behind a flag. — [arXiv 2406.00448](https://arxiv.org/abs/2406.00448); [project](https://bilarfpro.github.io/); [bilags](https://github.com/KevinXu02/bilags); [radiancefields.com](https://radiancefields.com/bilateral-guided-radiance-fields-merged-into-nerfstudio)
- splatfacto config:
  - `use_bilateral_grid: bool=False` ("model image-space ISP changes", BilaRF) and `grid_shape=(16,16,8)` (X, Y, W).
  - `color_corrected_metrics=False` ("apply color correction to the rendered images before computing the metrics").
  - The `bilateral_grid` optimizer is Adam lr 2e-3→1e-4.
  - There is no `appearance` embedding field in SplatfactoModelConfig.
  — [splatfacto.py](https://raw.githubusercontent.com/nerfstudio-project/nerfstudio/main/nerfstudio/models/splatfacto.py); [method_configs.py](https://raw.githubusercontent.com/nerfstudio-project/nerfstudio/main/nerfstudio/configs/method_configs.py)
- gsplat `simple_trainer.py` (main):
  - Post-processing: `post_processing=None` with choices `"bilateral_grid"` and `"ppisp"`, plus `bilateral_grid_shape=(16,16,8)` and `bilateral_grid_fused=False`. There is no `use_bilateral_grid` field on main.
  - Appearance: `app_opt=False`, `app_embed_dim=16`, `app_opt_lr=1e-3`, `app_opt_reg=1e-6`. When enabled, each Gaussian gets a 32-D feature. A per-image embedding plus a view-direction MLP (zero-initialized last layer) outputs a color offset. For PLY export the appearance is baked into `sh0` with an empty `shN`, so view-dependence is lost.
  — [simple_trainer.py](https://raw.githubusercontent.com/nerfstudio-project/gsplat/main/examples/simple_trainer.py)
- PPISP (Deutsch et al., NVIDIA; arXiv 2601.18336, CVPR 2026):
  - A differentiable post-render ISP with exposure offset, chromatic vignetting, linear color correction and a nonlinear camera response function.
  - A controller trained in a second phase predicts per-frame exposure and white balance for novel views. This enables fair evaluation without GT, which is the problem with per-frame latents and affine corrections.
  - Claims SOTA on standard benchmarks (numbers not retrieved). Code: nv-tlabs/ppisp.
  — [arXiv 2601.18336](https://arxiv.org/html/2601.18336); [CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Deutsch_PPISP_Physically-Plausible_Compensation_and_Control_of_Photometric_Variations_in_Radiance_CVPR_2026_paper.html); [project](https://research.nvidia.com/labs/sil/projects/ppisp)
- PPISP commentary: the target cases are auto-exposure drifting while panning past a window, white balance shifts, vignetting and response curves. It warns that a strong correction module can "explain away" real scene content. — [radiancefields.com](https://radiancefields.com/nvidia-announces-ppisp-for-radiance-fields)
- A 2025 volumetric-capture paper uses 32×32 spatially varying exposure and black-level grids upsampled by FFT. It reports a much faster backward pass than bilateral-grid slicing at high resolution. — [arXiv 2511.21697](https://arxiv.org/pdf/2511.21697)
- Splatfacto-W (arXiv 2407.12306), a nerfstudio implementation for unconstrained photo collections:
  - Reports +5.3 dB average PSNR over 3DGS and 150× faster training than NeRF-based methods.
  - On three NeRF-W datasets: about 26.9 / 22.7 / 22.5 dB vs 3DGS 19.99 / 18.47 / 17.57. GS-W is higher on two of the three (27.96, 22.91).
  — [arXiv 2407.12306](https://arxiv.org/pdf/2407.12306); [project](https://kevinxu02.github.io/splatfactow/)
- WildGaussians (arXiv 2407.08447) uses DINO features to remove occluders and an appearance module that predicts per-Gaussian color affine transforms (numbers not readable in the extract). — [arXiv 2407.08447](https://arxiv.org/html/2407.08447v2)
- Luminance-GS (arXiv 2504.01503) uses view-adaptive curve adjustment for challenging lighting. Examples: bicycle 18.52 dB vs 3DGS 18.63 / GS-W 18.33; garden 20.93 vs GS-W 20.49. — [arXiv 2504.01503](https://arxiv.org/html/2504.01503)

### Inferences
- For a single-session classroom video with auto-exposure, a full in-the-wild method (Splatfacto-W, WildGaussians) is overkill. The bilateral grid or PPISP matches the physical cause (ISP drift) better. `--pipeline.model.use-bilateral-grid True` is a one-flag experiment in the current nerfstudio pipeline, with about 20% extra training time per the bilags port.
- The bilateral grid and PPISP correct images in image space, so the 3D Gaussians learn a single canonical, exposure-consistent color. The exported PLY used in Unity contains no grid. That is desirable: walls get one consistent color instead of per-view-baked exposure blotches. gsplat `app_opt` instead bakes appearance at export and drops view-dependent SH.
- Evaluation pitfall: if held-out frames have different exposure, raw PSNR penalizes the canonical color. Report both raw metrics and `color_corrected_metrics=True` metrics (PPISP's controller is the principled alternative). Part of the 25.6 dB gap may be photometric, not geometric.
- Expected effect on floaters: unmodeled exposure changes are a known source of view-dependent floaters, because the optimizer places semi-transparent Gaussians in front of the camera to darken or brighten specific views. Bilateral grid / PPISP should reduce these. This is mechanistic reasoning; I found no indoor-specific quantitative evidence.

### Gaps
- Numeric PSNR/SSIM/LPIPS gains of BilaRF and PPISP on standard benchmarks were not retrieved in this session.
- Whether nerfstudio's splatfacto exposes `ppisp` (as opposed to gsplat's `simple_trainer.py`) was not verified.
- Whether the bilateral grid exists in the gsplat 1.4 release (vs main) was not verified. The field naming changed from a boolean to `post_processing` on gsplat main.
- No primary numbers were retrieved for GS-W, and the WildGaussians table was garbled.
