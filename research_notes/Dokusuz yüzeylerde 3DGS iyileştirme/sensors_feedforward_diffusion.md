# Improving Gaussian Splatting of large textureless indoor scenes / whole buildings: extra sensors, feed-forward priors, diffusion refinement (2023–2026)

Context for the reader: the team uses 4K phone video, COLMAP, and nerfstudio splatfacto (gsplat). Scenes are classrooms and corridors with white walls and grey floors, viewed in Unity/VR, and trained on Colab L4/A100. An iPhone Pro with LiDAR or a 360° camera may be available for future captures.

Search budget note: about 16 tool calls were used. Items marked "(arXiv ID only; numbers not verified in this session)" are cited only to identify the paper. No quantitative claim about them is made.

---

## Q1. LiDAR / RGB-D / iPhone depth / IMU-SLAM assisted GS: what improves textureless walls and scale?

### Takeaway
The strongest, most transferable evidence is DN-Splatter (WACV 2025). It is a nerfstudio extension of splatfacto that adds iPhone sensor-depth and monocular-normal losses. On MuSHRoom it cuts depth Abs Rel about 3.4x (0.0787 to 0.0228) and raises mesh F1 from 0.58 to 0.92. PSNR barely changes (+0.1 to +0.6 dB). Sensor depth therefore mainly fixes geometry (flat walls, metric scale), not image sharpness. Training cost goes up about 1.4x to 4x. LiDAR-initialized large-scale systems (LetsGo) show LiDAR init helps where SfM fails on textureless or repetitive surfaces. They also show that a cleaned or meshed LiDAR point cloud beats a raw LiDAR point cloud by 2.6 to 3.4 dB PSNR.

### Cited Findings
**DN-Splatter (Turkulainen et al., WACV 2025), [arXiv 2403.17822](https://arxiv.org/abs/2403.17822), code [github.com/maturk/dn-splatter](https://github.com/maturk/dn-splatter)**
- Method: adds depth and normal priors to 3DGS for indoor scenes. It uses a depth loss whose weight adapts to color-image gradients, so regularization is stronger on smooth, textureless regions. It also adds a normal loss from Omnidata monocular normals and a smoothness term, and supports direct mesh extraction. Monocular depth (ZoeDepth, DepthAnything) aligned to SfM points is supported as an alternative to sensor depth. Metric3D and MVSNet are compared in ablations. — [arXiv HTML v3](https://arxiv.org/html/2403.17822v3)
- Runs inside nerfstudio as `ns-train dn-splatter`, with flags for depth loss, depth smoothness, and normal loss. There is a `dn-splatter-big` variant with less aggressive culling, which keeps more Gaussians, and a MuSHRoom mesh evaluation script with `--device iphone`. — [GitHub](https://github.com/maturk/dn-splatter/)
- MuSHRoom mesh results (6 scenes, about 1.18M Gaussians each), Splatfacto vs DN-Splatter with iPhone depth: Accuracy 0.0749 vs 0.0239, Completion 0.0555 vs 0.0194, Chamfer-L1 0.0652 vs 0.0216, Normal Consistency 0.7727 vs 0.8822, F1 0.5835 vs 0.9243. — [arXiv HTML v3, Table 1](https://arxiv.org/html/2403.17822v3)
- ScanNet++ mesh results (2 scenes, RTX 4090), Splatfacto vs DN-Splatter with iPhone depth: Accuracy 0.1934 vs 0.0940, Completion 0.1503 vs 0.0395, Chamfer-L1 0.1719 vs 0.0667, NC 0.6741 vs 0.8316, F1 0.179 vs 0.766. Training time is 8.9 min vs 36.9 min. — [arXiv HTML v3, Table 2](https://arxiv.org/html/2403.17822v3)
- MuSHRoom novel view synthesis and depth (6 scenes; values given as two test splits):
  - Splatfacto: Abs Rel 0.0787/0.0817, PSNR 24.44/21.33, SSIM 0.849/0.782, LPIPS 0.139/0.224.
  - Splatfacto + depth loss: Abs Rel 0.0234/0.0364, PSNR 24.77/21.95, LPIPS 0.124/0.185.
  - Full DN-Splatter: Abs Rel 0.0228/0.0354, PSNR 24.58/21.89, LPIPS 0.129/0.180.
  — [arXiv HTML v3, Table 3](https://arxiv.org/html/2403.17822v3)
- ScanNet++ scene b20a261fdf: Splatfacto Abs Rel 0.148, RMSE 0.512, PSNR 23.41. With the iPhone depth loss: Abs Rel 0.0285, RMSE 0.179, PSNR 23.61. — [arXiv HTML v3, Table 6](https://arxiv.org/html/2403.17822v3)
- Cost on the MuSHRoom "VR room" scene (RTX 4090, 30k iterations): Splatfacto 12.9 min; with depth and normal losses 17.5 min. — [arXiv HTML v3, Table 4](https://arxiv.org/html/2403.17822v3)
- Against Faro laser-scan ground truth on MuSHRoom (10 scenes), Abs Rel is about 8.3 for Splatfacto, 3.7 with the depth loss, and 3.6 with depth plus normal losses. Nerfacto is about 14.7 and MonoSDF about 10.9. — [paper PDF, Table 13, via search snippet](https://arxiv.org/pdf/2403.17822)
- Paper's own textureless claim: Splatfacto, SuGaR and 2DGS "severly struggle" with geometry in low-texture environments (Fig. 3). The paper has no wall-specific metric. — [arXiv HTML v3](https://arxiv.org/html/2403.17822v3)
- MuSHRoom dataset: room-scale captures from iPhone and Kinect, with Faro laser-scan ground truth. — [arXiv 2311.02778](https://arxiv.org/abs/2311.02778) (arXiv ID only; dataset details not verified in this session beyond the DN-Splatter usage)

**LetsGo (Cui et al., ACM TOG 2024 / SIGGRAPH Asia), [arXiv 2404.09748](https://arxiv.org/abs/2404.09748)**
- Hardware: a handheld "Polar" scanner with IMU, LiDAR and a fisheye camera. GarageWorld dataset has 8 scenes; earlier versions said 5. Motivation: SfM/MVS fail because of "texture-less regions and repetitive structural designs", reflective surfaces and glass. — [arXiv HTML v3](https://arxiv.org/html/2404.09748v3)
- Scene scale is 7,109 to 38,448 m², with 2,280 to 13,296 images. The scenes include an Office Building (22,159 m², 9,308 images) and an Arts Center (10,392 m², 5,779 images). — [Table 1](https://arxiv.org/html/2404.09748v3)
- Table 2 (all GS baselines LiDAR-initialized, marked *):
  - GarageWorld PSNR/LPIPS: LOD-LiDAR-GS 25.77/0.210, Splatfacto* 25.45/0.261, 3DGS* 23.52/0.412, Octree-GS* 25.19/0.315.
  - ScanNet++: Octree-GS* is best at 31.55 PSNR, LetsGo 29.19, Splatfacto* 28.35.
  - The text claims "consistently best", but the table does not fully support it (3DGS* has higher SSIM on GarageWorld; Octree-GS* has higher PSNR on ScanNet++).
  - There is no SfM-initialized baseline, so the LiDAR-vs-SfM gain is not isolated.
  — [Table 2](https://arxiv.org/html/2404.09748v3)
- Point-source ablation at 4 cm:
  - Arts Center: mesh-sampled points 25.70 PSNR with 5.0M Gaussians; raw LiDAR 23.11 PSNR with 10.0M Gaussians.
  - Shopping Mall 3: mesh 24.91, raw LiDAR 21.52.
  - Mesh-point density on Arts Center: 2 cm gives 25.87 dB (17.7M Gaussians), 10 cm gives 25.08 dB (0.84M).
  — [Table 3](https://arxiv.org/html/2404.09748v3)
- Training: RTX A6000, 12 to 16 h per scene. Each scene has 3 to 10 blocks of 1.5 to 4 h each. Settings: depth-loss weight 0.8, densification delayed to 75k iterations, opacity reset disabled. — [Sec. 5.1](https://arxiv.org/html/2404.09748v3)
- LOD rendering is about 3 to 4x faster than the SIBR viewer (RTX 3090). The web renderer runs at 60 FPS with about 2M Gaussians on an i9 desktop and an M2 MacBook, with a 2 GB browser cap. — [Sec. 6](https://arxiv.org/html/2404.09748v3)
- LiDAR limits stated by the authors: sparse with holes, and inaccurate on reflective or transparent surfaces. — [arXiv HTML v3](https://arxiv.org/html/2404.09748v3)

**Gaussian-LIC / Gaussian-LIC2 (LiDAR-inertial-camera SLAM), [arXiv 2404.06926](https://arxiv.org/abs/2404.06926), [arXiv 2507.04004](https://www.alphaxiv.org/overview/2507.04004)**
- Gaussian-LIC fuses LiDAR, IMU and camera. Gaussians are initialized from LiDAR points plus online-triangulated visual SfM points. It targets unbounded outdoor scenes. — [arXiv 2404.06926 HTML](https://arxiv.org/html/2404.06926v3)
- Gaussian-LIC2 adds depth completion to fill sparse-LiDAR holes and photometric constraints for odometry. No numbers were retrieved. — [alphaXiv 2507.04004](https://www.alphaxiv.org/overview/2507.04004)

**RGB-D Gaussian SLAM (SplaTAM, MonoGS, RTG-SLAM, Photo-SLAM)**
- SplaTAM averages 33.69 dB PSNR on Replica, vs Co-SLAM 30.54 and ESLAM 30.75. This comes from RTG-SLAM's appendix, Table 8. — [RTG-SLAM arXiv 2404.19706](https://arxiv.org/pdf/2404.19706)
- RTG-SLAM (SIGGRAPH 2024) claims about 2x the speed and about half the memory of NeRF-based SLAM. — [SIGGRAPH archive](https://history.siggraph.org/?p=164125)
- MonoGS tracking ATE on Replica: 0.76 cm (RGB-D table in RGS-SLAM) and 0.565 cm (monocular table in SEGS-SLAM; protocols differ). MonoGS renders at 769 FPS in RGS-SLAM's table. — [RGS-SLAM arXiv 2601.00705](https://arxiv.org/pdf/2601.00705); [SEGS-SLAM arXiv 2501.05242](https://arxiv.org/pdf/2501.05242)
- GPU memory on Replica room0: MonoGS 14.96 GB, SplaTAM 11.34 GB. — [MonoGS++ BMVC 2024 supplement](https://bmva-archive.org.uk/bmvc/2024/papers/Paper_133/supplementary133.pdf)
- Paper identifiers: SplaTAM [arXiv 2312.02126](https://arxiv.org/abs/2312.02126), MonoGS [arXiv 2312.06741](https://arxiv.org/abs/2312.06741), Photo-SLAM [arXiv 2311.16728](https://arxiv.org/abs/2311.16728). (arXiv IDs only; their own tables were not fetched in this session.)

**iPhone capture apps into nerfstudio (Polycam, Record3D, ARKit)**
- nerfstudio's `ns-process-data` lists Polycam and Record3D (both "iOS with LiDAR") and KIRI Engine as capture sources. Polycam raw exports (images, camera poses, depth maps) are only available on LiDAR iPhones and iPads. — [nerfstudio README mirror](https://pypi.org/project/nerfstudio/1.0.3); [nerfstudio fork README](https://github.com/chambinlee/nerfstudio)
- A community comparison (nerfstudio issue #3421) found Postshot output crisper than splatfacto from the same COLMAP data. The user reported that Postshot registers more images from the same COLMAP `.bin` files than nerfstudio's `transforms.json` path. — [GitHub issue #3421](https://github.com/nerfstudio-project/nerfstudio/issues/3421)

**360° cameras**
- OmniGS (2024): calibrated monocular 360° images plus sparse SfM points, with a rasterizer that splats directly to equirectangular space. — [arXiv 2404.03202](https://arxiv.org/html/2404.03202v1)
- 360-GS (2024): indoor roaming from a few panoramas, using room-layout and depth priors to guide the Gaussians. — [arXiv 2402.00763](https://arxiv.org/pdf/2402.00763)
- SC-OmniGS (ICLR 2025): adds self-calibration of poses and intrinsics for 360° GS. — [arXiv 2502.04734](https://arxiv.org/html/2502.04734v1)
- ODGS-SLAM (CVPR 2026): omnidirectional GS SLAM for panoramic RGB or RGB-D sequences. — [CVF open access](https://openaccess.thecvf.com/content/CVPR2026/papers/Spiss_ODGS-SLAM_Omnidirectional_Gaussian_Splatting_SLAM_CVPR_2026_paper.pdf)

### Inferences
- For white walls and grey floors, sensor depth mainly buys flat, correctly scaled geometry and fewer floaters. In DN-Splatter's MuSHRoom results, NVS PSNR changes by under 1 dB. If the measurement or route-planning use case needs metric accuracy (door widths, corridor widths), iPhone LiDAR depth plus DN-Splatter is the most direct path. It is already a nerfstudio plugin, so it stays inside the current splatfacto toolchain.
- Even without new hardware, DN-Splatter accepts monocular depth (DepthAnything, ZoeDepth) aligned to COLMAP points, plus Omnidata normals. This can be tried on the existing 4K videos on Colab. Expect smaller gains than with sensor depth (the paper's main numbers use sensor depth).
- LetsGo's ablation suggests a caution: raw LiDAR points as init gave about 2× more Gaussians and 2.6 to 3.4 dB lower PSNR than mesh-sampled points. If iPhone LiDAR points are used for init, downsampling or cleaning (e.g., a voxel grid of about 4 cm, or mesh resampling) is likely better than dumping raw points.
- Real-time RGB-D SLAM systems (SplaTAM, MonoGS, RTG-SLAM) are benchmarked mostly on Replica (synthetic) and small TUM/ScanNet rooms. They need 11 to 15 GB of GPU memory per room and are not obviously better than offline COLMAP plus splatfacto for a whole building. Their value would be live capture feedback, not final quality.
- 360° capture reduces the number of frames needed for full coverage of corridors and gives wide baselines for pose estimation in low-texture spaces. However, nerfstudio splatfacto has no native equirectangular rasterizer, so the usual practice is to split panoramas into cubemap or perspective crops before COLMAP.

### Gaps
- There is no published wall-specific metric for any method (all report whole-scene Abs Rel, Chamfer or PSNR).
- Gaussian-LIC, Photo-SLAM and RTG-SLAM Replica PSNR tables were not retrieved. A consistent SplaTAM/MonoGS/RTG-SLAM comparison under one protocol was not found.
- The exact `ns-process-data record3d/polycam` behavior was not verified: whether ARKit poses replace COLMAP, and whether splatfacto (not DN-Splatter) consumes the depth maps.
- No quantitative study was found of iPhone ARKit pose accuracy vs COLMAP over building scale (multi-room drift).
- Scaniverse and Luma internal pipelines are not documented in papers. Nothing citable was found.

---

## Q2. Building-scale / multi-room: chunking and LOD for VR

### Takeaway
Large-scene methods (Hierarchical 3DGS, LetsGo, LODGE, CityGaussian, VastGaussian, Octree-GS) all rely on spatial partitioning into blocks or chunks plus an LOD hierarchy. That is what makes VR or web rendering feasible: LetsGo runs at 60 FPS with about 2M Gaussians in a browser, and LODGE renders in real time on mobile. None of them specifically addresses textureless surfaces. They solve scale and rendering budget, not wall blur.

### Cited Findings
- Hierarchical 3DGS (Kerbl et al., SIGGRAPH 2024 / TOG):
  - Splits the scene into chunks trained independently, then consolidates them into a Gaussian hierarchy whose interior nodes are optimized.
  - Provides LOD selection with smooth transitions.
  - Adapts and regularizes training for sparse coverage.
  - Demonstrated on captures of tens of thousands of images spanning several km.
  — [arXiv 2406.12080](https://arxiv.org/html/2406.12080v1); [TU Wien page](https://www.cg.tuwien.ac.at/research/publications/2024/kerbl-2024-ah3/)
- "A LoD of Gaussians" (Windisch et al., 2025) argues against chunking. It keeps one global model to avoid seam artifacts and notes that chunked rendering may need all visible chunks in memory at once. — [arXiv 2507.01110](https://arxiv.org/pdf/2507.01110v4)
- LODGE (NeurIPS 2025; Google, CTU Prague, TUM):
  - Builds LOD levels via a depth-aware 3D smoothing filter, then importance pruning and fine-tuning.
  - Splits the scene into spatial chunks loaded on demand, with opacity blending at seams.
  - Claims SOTA quality and speed on the Hierarchical-3DGS (outdoor) and Zip-NeRF (indoor) datasets, with real-time rendering on mobile.
  — [arXiv 2505.23158](https://arxiv.org/html/2505.23158v2); [NeurIPS 2025](https://papers.nips.cc/paper_files/paper/2025/hash/f00475398609746d67821a02765eb8e8-Abstract-Conference.html)
- LetsGo includes an indoor 22,159 m² "Office Building" scene. Its LOD-LiDAR-GS uses a 4 cm finest level, √2 per-level scaling and distance-based level selection. It is about 3 to 4x faster than SIBR, with a web renderer at 60 FPS and about 2M Gaussians. — [arXiv 2404.09748v3](https://arxiv.org/html/2404.09748v3)
- Octree-GS (LiDAR-initialized) reached 31.55 PSNR on ScanNet++ in LetsGo's benchmark, the best of all methods on that indoor set. — [LetsGo Table 2](https://arxiv.org/html/2404.09748v3)
- Paper identifiers: CityGaussian [arXiv 2404.01133](https://arxiv.org/abs/2404.01133), VastGaussian [arXiv 2402.17427](https://arxiv.org/abs/2402.17427), Octree-GS [arXiv 2403.17898](https://arxiv.org/abs/2403.17898). (arXiv IDs only; their own numbers were not fetched in this session.)

### Inferences
- A university building (a few thousand m², tens of rooms) is about 1/3 to 1/10 of a LetsGo scene. Per-floor or per-wing chunks of a few million Gaussians each, merged with an LOD scheme, fit the scale.
- For Unity/VR, the practical constraint is the Gaussian count per visible region (LetsGo's web viewer is capped at about 2 to 3M). That favors per-room training with LOD or pruning over one giant splat.
- Indoor rooms are separated by walls, so occlusion-based chunk streaming (load the current room and its neighbours) is natural. This is an inference; no paper found tests it explicitly for multi-room buildings.

### Gaps
- No dedicated "indoor multi-room building GS" benchmark with numbers was found in this session.
- No CityGaussian, VastGaussian or Octree-GS training-time or memory numbers were retrieved.
- Hierarchical 3DGS quantitative results and training time were not retrieved.
- Unity-specific GS plugin performance (e.g., aras-p UnityGaussianSplatting) in VR was not covered.

---

## Q3. Feed-forward / learned priors (DUSt3R/MASt3R/VGGT init, InstantSplat, pixelSplat/MVSplat/DepthSplat/NoPoSplat)

### Takeaway
Feed-forward 3D models give dense point clouds without feature matching, which is exactly where COLMAP is weak on textureless walls. However, the best dense-view study (VGGT-X, 2025) still trails COLMAP-initialized 3DGS by about 1 dB PSNR on MipNeRF360 (26.40 vs 27.39). Feed-forward splatting networks (pixelSplat, MVSplat, DepthSplat, NoPoSplat) are designed for 2 to 6 views and are not suitable for whole-building reconstruction from 500 to 1000 frames. The most practical uses are pose and init backup for COLMAP failures (InstantSplat, MASt3R-SfM, VGGT-X) and learned initializers for indoor scenes (QuickSplat).

### Cited Findings
- InstantSplat (Fan et al., NVIDIA):
  - Uses DUSt3R/MASt3R for dense initialization, then jointly optimizes Gaussians and poses.
  - Works with 3DGS, 2DGS and Mip-Splatting from 2 to 3 views.
  - Reports 7.5 s reconstruction, with SSIM improving from 0.3755 to 0.7624 in a 3-view setting. A v3 figure shows 22.3 PSNR in 9 s vs 14.3 for COLMAP-free 3DGS and 13.0 for COLMAP+3DGS; the dataset is unclear.
  - Claimed speedup grows across versions (>20x in v4, >30x in v5).
  — [arXiv 2403.20309](https://arxiv.org/html/2403.20309v5); [NVIDIA page](https://research.nvidia.com/labs/avg/publication/fan.cong.etat.cvpr.nri24)
- VGGT-X (Sept 2025):
  - Memory-efficient VGGT scaling to 1,000+ images, adaptive global alignment, and robust 3DGS training.
  - MipNeRF360: COLMAP-initialized 3DGS SSIM 0.8148 / PSNR 27.39 vs VGGT-X 0.7821 / 26.40.
  - Authors say the gap is "substantially" closed but remains.
  — [HF papers 2509.25191](https://huggingface.co/papers/2509.25191); [review](https://www.themoonlight.io/review/vggt-x-when-vggt-meets-dense-novel-view-synthesis)
- GASE (2026) tested VGGT, DA3 and Pi3 as initializers on Mip-NeRF 360 and ETH3D. It found blurriness, loss of fine detail and "discrete structural approximations", and reverted to COLMAP. — [arXiv 2606.17520](https://arxiv.org/pdf/2606.17520)
- WorldExplorer used VGGT on more than 1,000 generated images because COLMAP was too slow, downsampling to 200K points for 3DGS init. — [arXiv 2506.01799](https://arxiv.org/pdf/2506.01799)
- QuickSplat (2025): a learned Gaussian initializer and densifier evaluated on ScanNet++. Its authors argue that photometric-only optimization produces curved surfaces and floaters on flat, low-texture walls, and that learned priors give flatter structures and much faster convergence. — [arXiv 2505.05591](https://arxiv.org/pdf/2505.05591)
- Prior-regularized indoor GS evaluated on ScanNet and ScanNet++, using monocular priors rather than feed-forward networks:
  - GaussianRoom uses a neural SDF to guide densification and pruning from poor SfM init, plus normal and edge priors for textureless areas. — [arXiv 2405.19671](https://arxiv.org/html/2405.19671v2)
  - 2DGS-Room uses seed-guided 2DGS, with a normal prior "for textureless regions". — [arXiv 2412.03428](https://arxiv.org/html/2412.03428v1)
- DepthSplat vs MVSplat on DL3DV (PSNR): 2 views 19.31 vs 17.54, 4 views 23.12 vs 21.63, 6 views 24.19 vs 22.93. — [arXiv 2410.13862](https://arxiv.org/pdf/2410.13862)
- DepthSplat on RealEstate10K: 27.47 PSNR, 0.889 SSIM, 0.114 LPIPS (secondhand review figure). — [review](https://liner.com/review/depthsplat-connecting-gaussian-splatting-and-depth)
- MVSplat reports 22 fps feed-forward inference on RealEstate10K and ACID. — [Papers with Code](https://paperswithcode.com/paper/mvsplat-efficient-3d-gaussian-splatting-from-sparse-multi-view-images)
- Paper identifiers: VGGT (CVPR 2025) [arXiv 2503.11651](https://arxiv.org/abs/2503.11651), DUSt3R [arXiv 2312.14132](https://arxiv.org/abs/2312.14132), MASt3R-SfM [arXiv 2409.19152](https://arxiv.org/abs/2409.19152), pixelSplat [arXiv 2312.12337](https://arxiv.org/abs/2312.12337), MVSplat [arXiv 2403.14627](https://arxiv.org/abs/2403.14627), NoPoSplat [arXiv 2410.24207](https://arxiv.org/abs/2410.24207). (arXiv IDs only; their own numbers were not fetched in this session.)

### Inferences
- For 500 to 1000 frames of a classroom, COLMAP (when it registers all frames) still likely gives the best final PSNR. VGGT or MASt3R is most useful as (a) a fallback when COLMAP drops frames or breaks into several models on white corridors, and (b) a source of dense init points in wall regions, where SfM leaves holes and splatfacto then grows floaters.
- A hybrid is plausible: COLMAP poses plus dense VGGT or MASt3R points (or monocular-depth-backprojected points) merged into the init cloud. GASE's finding of blur in feed-forward outputs suggests using them for init only and letting photometric optimization refine.
- VGGT-scale models on 1000 frames need memory-efficient variants (VGGT-X). Plain VGGT on an L4 (24 GB) will likely need frame subsampling or chunking. This is an inference; no exact memory numbers were retrieved.

### Gaps
- No exact numbers were found for MASt3R-SfM vs COLMAP registration rates on textureless indoor scenes.
- DepthSplat ScanNet table values and NoPoSplat numbers were not retrieved.
- No study was found that specifically measures "VGGT init vs COLMAP init" on ScanNet++ or MuSHRoom wall regions.
- QuickSplat's numerical results were not retrieved.

---

## Q4. Diffusion / generative refinement (Difix3D+, 3DGS-Enhancer, GenFusion, ReconFusion, GSFixer): do they fix wall blur, and are they faithful enough for measurement?

### Takeaway
Single-step diffusion fixers (Difix3D+, CVPR 2025) greatly improve perceptual quality: FID drops about 2.6x (107 to 41 on DL3DV) and LPIPS from 0.38 to 0.29. PSNR gains are modest (+0.8 to 1.8 dB). They add 76 ms per frame on an A100. The authors themselves report hallucinated pixels that contradict ground truth under high noise. Gains are bounded by the base reconstruction. These methods suit visual polish of under-observed views in VR. They should not be used for geometry or metric measurement, and they add nothing to depth accuracy.

### Cited Findings
- Difix3D+ (Wu et al., NVIDIA, CVPR 2025), [arXiv 2503.01774](https://arxiv.org/abs/2503.01774):
  - Difix is fine-tuned from SD-Turbo (frozen VAE encoder, LoRA decoder). It cleans pseudo-training views that are distilled back into NeRF or 3DGS, and is used again as a real-time post-render enhancer.
  - Trained on 112 DL3DV scenes; evaluated on 28 held-out DL3DV scenes and 12 Nerfbusters captures.
  — [arXiv HTML](https://arxiv.org/html/2503.01774)
- Difix3D+ Table 2 (3DGS base):
  - DL3DV: PSNR 17.18 to 17.99, SSIM 0.588 to 0.602, LPIPS 0.384 to 0.293, FID 107.23 to 40.86.
  - Nerfbusters: PSNR 17.66 to 18.51, LPIPS 0.327 to 0.264, FID 113.84 to 41.77.
  — [arXiv HTML](https://arxiv.org/html/2503.01774)
- Difix3D+ Table 2 (Nerfacto base): DL3DV PSNR 17.16 to 17.82, FID 112.30 to 41.77. Table 3 (RDS driving): PSNR 19.95 to 21.75, FID 91.38 to 73.08. — [arXiv HTML](https://arxiv.org/html/2503.01774)
- Difix3D+ cost and limits: 76 ms per image on an A100, said to be more than 10x faster than multi-step diffusion. Performance is bounded by the initial reconstruction and it struggles where reconstruction "entirely failed". Some regions remain blurry. High noise levels cause hallucinated pixels that contradict ground truth. — [arXiv HTML](https://arxiv.org/html/2503.01774)
- 3DGS-Enhancer (NeurIPS 2024): a video diffusion model produces view-consistent enhanced novel views, which are used to fine-tune the 3DGS. The teaser shows sparse-view PSNR of 16.29 to 26.04 and 12.83 to 22.26 on two example scenes; DL3DV-10K ablation values are around 17 to 18 dB. — [arXiv 2410.16266](https://arxiv.org/html/2410.16266v1); [NeurIPS slides](https://neurips.cc/media/neurips-2024/Slides/95333_HJhpDzu.pdf)
- GSFixer (2025): reference-guided video diffusion that compares against GenFusion and Difix3D+. A third-party summary reports +2.16 dB on artifact restoration and +3.55 dB with 3-view input over prior generative methods; the dataset is unspecified. — [arXiv 2508.09667](https://arxiv.org/pdf/2508.09667v1); [emergentmind](https://www.emergentmind.com/topics/gsfixer)
- Paper identifiers: GenFusion (CVPR 2025) [arXiv 2503.21219](https://arxiv.org/abs/2503.21219), ReconFusion [arXiv 2312.02981](https://arxiv.org/abs/2312.02981), Deceptive-NeRF [arXiv 2305.15171](https://arxiv.org/abs/2305.15171). (arXiv IDs only; numbers not verified in this session.)

### Inferences
- Wall blur in dense 4K captures is mostly a geometry problem (floaters, wrong depth on textureless walls), not a lack of views. Diffusion fixers mask the symptom in renders but leave the floaters in the 3D model. In VR, the user moves freely, and Difix's 76 ms per frame on an A100 rules out per-frame post-render enhancement at VR framerates (72 to 90 Hz). Only the "distill into 3DGS" mode is usable. The headset then sees ordinary Gaussians, with whatever hallucinations were baked in.
- For faithfulness and measurement (door widths, signs, accessibility features), generative refinement is risky. The Difix authors themselves report hallucinations contrary to ground truth. Any measurements should come from the un-refined, depth-regularized model or the sensor-depth mesh.
- Benchmarks are mostly sparse-view or outdoor (DL3DV, Nerfbusters, driving). There is no evidence here specifically on dense indoor captures with white walls.

### Gaps
- GenFusion's own numbers were not retrieved.
- ReconFusion, Deceptive-NeRF and FixerGS indoor results were not retrieved.
- No study was found measuring geometric accuracy (Chamfer or depth error) before vs after diffusion refinement. Faithfulness is only discussed qualitatively.
- Whether Difix3D+ public code and weights allow commercial or academic use on Colab was not verified.

---

## Q5. Practicality summary for the team's workflow (COLMAP + splatfacto/gsplat, Colab L4/A100, Unity VR)

### Takeaway
Ranked by expected payoff and ease (inference from the findings above):
1. **DN-Splatter inside nerfstudio.** Monocular depth and normals on current videos now; iPhone LiDAR depth in future captures. It is the only method here with quantified indoor geometry gains on MuSHRoom and ScanNet++ that runs in the same toolchain, at about 13 to 37 min per scene on a 4090-class GPU.
2. **Dense init from MASt3R/VGGT, or cleaned LiDAR points**, where COLMAP leaves wall holes.
3. **Chunking plus LOD** (Hierarchical 3DGS, LODGE, LetsGo-style) for building scale in VR.
4. **Diffusion fixers only for cosmetic polish**, never for measurement.

### Cited Findings
- DN-Splatter costs 12.9 min (splatfacto) vs 17.5 min (with depth and normal losses) at 30k iterations on an RTX 4090 for a MuSHRoom room. On ScanNet++ it is 8.9 vs 36.9 min. — [arXiv HTML v3](https://arxiv.org/html/2403.17822v3)
- Building-scale LiDAR-GS (LetsGo) needed 12 to 16 h per scene on an A6000, over 3 to 10 blocks. — [arXiv HTML v3](https://arxiv.org/html/2404.09748v3)
- Difix runs at 76 ms per image on an A100. — [arXiv HTML](https://arxiv.org/html/2503.01774)
- Feed-forward init (VGGT-X) is about 1 dB below COLMAP init on MipNeRF360. — [HF 2509.25191](https://huggingface.co/papers/2509.25191)

### Inferences
- On Colab: an A100 (40/80 GB) comfortably fits DN-Splatter on room-scale scenes. An L4 (24 GB) should fit per-room runs but may need fewer Gaussians or the non-"big" variant. This is not verified with a benchmark.
- An iPhone Pro LiDAR capture via Polycam or Record3D gives poses plus depth together. The depth is low-resolution (the DN-Splatter paper calls it "low-resolution depth sensors"), but it is enough to make walls flat and fix metric scale. This matters for accessibility measurement, since the current COLMAP-only pipeline has arbitrary scale.
- A 360° camera mainly helps coverage and pose robustness in corridors. It requires cubemap splitting for splatfacto. No quantitative indoor gain vs phone video was found.

### Gaps
- No head-to-head study was found of iPhone LiDAR (ARKit poses) vs 4K video plus COLMAP on the same building.
- No VR framerate benchmark was found for Gaussian counts in Unity on standalone headsets.
- No verified L4 memory numbers were found for DN-Splatter or VGGT on 500 to 1000 frame inputs.
