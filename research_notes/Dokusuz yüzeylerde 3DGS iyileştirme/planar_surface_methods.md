# Planar-Prior and Surface-Based Gaussian Splatting for Textureless Indoor Surfaces (2023–2026)

Context: classroom captured as 4K handheld video, with white walls and a grey floor. Pipeline is COLMAP → nerfstudio splatfacto (gsplat 1.4) → Unity/VR via aras-p UnityGaussianSplatting, trained on Colab L4/A100. Units: Chamfer (CD), Acc and Comp are in cm for indoor benchmarks and in mm for DTU. F1 and NC are % or fractions as given in the source.

## 1. Planar-prior methods (PGSR, PlanarSplatting, PlanarGS, IndoorGS, GaussianRoom, Manhattan priors)

### Takeaway
On indoor benchmarks (Replica, ScanNet++, MuSHRoom), the strongest 2025 results come from methods that combine **planar priors with monocular or feed-forward depth and normal priors**: PlanarGS (NeurIPS 2025) and DN-Splatter. PlanarGS is the only one that also beats 3DGS on PSNR in a phone-captured indoor set (MuSHRoom 26.42 vs 25.79). PlanarSplatting (CVPR 2025, Apache-2.0) is the fastest and most practical way to get a clean planar layout. It takes about 3 min per scene and accepts COLMAP input. Used as initialization for 3DGS, it raised ScanNet PSNR by about 1 dB while using 3.4× fewer Gaussians.

### Cited Findings

**PGSR: Planar-based Gaussian Splatting for surface reconstruction (arXiv 2406.06521, DOI 10.1109/TVCG.2024.3494046 → IEEE TVCG)**
- Core idea: each Gaussian is flattened into a plane. Depth is rendered without bias by dividing the rendered plane distance by the rendered normal. Training adds single-view geometric regularization, multi-view photometric regularization and multi-view geometric regularization, plus an exposure-compensation model for scenes with large illumination changes. — [arXiv abs](https://arxiv.org/abs/2406.06521)
- DTU mean CD: PGSR **0.52 mm** in 0.5 h. The same table gives 2DGS 0.80 (0.32 h), GOF 0.74 (2 h), SuGaR 1.33 (1 h), NeuS 0.84 (>12 h) and Neuralangelo 0.61 (>128 h). — [arXiv HTML, PGSR tables](https://arxiv.org/html/2406.06521)
- Tanks & Temples mean F1: PGSR **0.52** in 0.75 h. The same table gives GOF 0.46 (2 h), 2DGS 0.32 (0.57 h), SuGaR 0.19 (2 h) and Neuralangelo 0.50 (>128 h). — [arXiv HTML](https://arxiv.org/html/2406.06521)
- Mip-NeRF360 NVS (PSNR/SSIM/LPIPS):
  - PGSR 27.25 / 0.833 / **0.178**
  - 3DGS 27.24 / 0.803 / 0.246
  - 2DGS 27.03 / 0.804 / 0.239
  - GOF 27.78 / 0.835 / 0.196
  - SuGaR 26.10 / 0.771 / 0.283

  PGSR's indoor subset alone scores 30.36 / 0.934 / 0.147. — [arXiv HTML](https://arxiv.org/html/2406.06521)
- No GPU-memory figures are reported. Project page: zju3dv.github.io/pgsr. — [arXiv HTML](https://arxiv.org/html/2406.06521), [arXiv abs](https://arxiv.org/abs/2406.06521)
- On indoor benchmarks (from the PlanarGS paper), PGSR does not stand out:

  | Dataset | CD | F1 | NC | PSNR |
  |---|---|---|---|---|
  | MuSHRoom | 10.51 | 59.11 | 73.27 | 25.73 (3DGS: 25.79) |
  | ScanNet++ | 7.22 | 53.73 | 87.30 | – |
  | Replica | 8.56 | 62.98 | 83.30 | – |

  PGSR's MuSHRoom accuracy is good (7.52) but its completion is poor (13.50). — [PlanarGS arXiv HTML](https://arxiv.org/html/2510.23930v1)

**PlanarSplatting: Accurate Planar Surface Reconstruction in 3 Minutes (arXiv 2412.03451, CVPR 2025 highlight; Ant Group / Univ. of Louisville)**
- Core idea: the scene is optimized directly as 3D **plane primitives** (rectangles), which are splatted into 2.5D depth and normal maps. There is no 2D/3D plane detection, matching or tracking step. Implemented in CUDA. — [arXiv abs](https://arxiv.org/abs/2412.03451)
- Priors: Metric3Dv2 supplies monocular depth (for initialization and supervision) and Omnidata supplies pseudo-normal maps. — [arXiv HTML](https://arxiv.org/html/2412.03451)
- The repo's demo uses VGGT (pose-free input) and Metric3D v2 normals. A COLMAP input script (`run_demo_colmap.py`) is included. **License: Apache-2.0.** Built on PyTorch 2.3.1 / CUDA 12.1 with PyTorch3D. — [GitHub ant-research/PlanarSplatting](https://github.com/ant-research/PlanarSplatting)
- ScanNetV2 planar reconstruction:

  | Method | CD | F-score | VOI | RI | SC |
  |---|---|---|---|---|---|
  | **PlanarSplatting** | **4.83** | **68.85** | 2.502 | 0.948 | 0.532 |
  | AirPlanes (uses plane annotations) | 5.30 | 64.92 | 2.268 | 0.957 | 0.568 |
  | 2DGS + RANSAC | 14.15 | 31.33 | – | – | – |
  | PlanarRecon | 9.89 | 43.47 | – | – | – |

  — [arXiv HTML Table 1](https://arxiv.org/html/2412.03451)
- ScanNet++ planar reconstruction: PlanarSplatting CD **9.33**, F **47.04**. AirPlanes 13.75 / 32.58; 2DGS + RANSAC 20.39 / 26.46. — [arXiv HTML Table 2](https://arxiv.org/html/2412.03451)
- NVS on ScanNetV2 (Table 4), with planes used as Gaussian initialization:

  | Method | PSNR | SSIM | LPIPS | Total time | Gaussians |
  |---|---|---|---|---|---|
  | 3DGS | 24.417 | 0.781 | 0.321 | 12.2 min | 1.27M |
  | **PlanarSplatting + 3DGS** | **25.471** | **0.816** | **0.296** | **5.6 min** (2.5 plane + 3.1 GS) | **0.37M** |
  | 2DGS | 24.766 | 0.796 | 0.323 | 14.2 min | 0.76M |
  | PlanarSplatting + 2DGS | 25.380 | 0.813 | 0.296 | 7.3 min | – |

  — [arXiv HTML Table 4](https://arxiv.org/html/2412.03451)
- Ablation (10 ScanNetV2 scenes): sphere initialization instead of the default gives CD 8.39 vs 4.66 for the full model. — [arXiv HTML Table 3](https://arxiv.org/html/2412.03451)

**PlanarGS: High-Fidelity Indoor 3DGS Guided by Vision-Language Planar Priors (arXiv 2510.23930, NeurIPS 2025)**
- Core idea: "Language-Prompted Planar Priors" (LP3). A vision-language segmenter (GroundedSAM; YOLO-World + SAM also tested) is prompted with words such as "wall/floor/ceiling" to propose plane regions. These are refined by cross-view fusion and geometric checks. Training adds a planar-consistency loss, plus depth and normal supervision from DUSt3R (VGGT also tested). Gaussians are flattened, and plane priors drive initialization and co-planarity. — [arXiv HTML](https://arxiv.org/html/2510.23930v1), [NeurIPS poster](https://neurips.cc/virtual/2025/poster/120068)
- MuSHRoom (iPhone indoor sequences; closest benchmark to the user's capture):

  | Method | CD | F1 | NC | PSNR | SSIM | LPIPS |
  |---|---|---|---|---|---|---|
  | **PlanarGS** | **4.49** | **77.14** | **83.35** | **26.42** | **0.8874** | 0.2141 |
  | 3DGS | 11.92 | 38.53 | 62.00 | 25.79 | 0.8775 | 0.2059 |
  | 2DGS | 9.71 | 51.50 | – | 25.67 | – | – |
  | GOF | 12.07 | – | – | 24.76 | – | – |
  | PGSR | 10.51 | – | – | 25.73 | – | – |
  | QGS | 9.28 | – | – | 24.37 | – | 0.1994 |
  | DN-Splatter | 5.77 | 61.86 | – | 24.80 | – | 0.2595 |

  — [arXiv HTML Table 1](https://arxiv.org/html/2510.23930v1)
- ScanNet++ (CD / F1 / NC):
  - **PlanarGS 3.66 / 82.78 / 90.52**
  - DN-Splatter 4.16 / 75.86 / 82.06
  - 2DGS 6.70 / 53.46 / 88.20
  - GOF 7.09 / 57.99 / 74.75
  - PGSR 7.22 / 53.73 / 87.30
  - 3DGS 10.57 / 31.78 / 77.65
  - DUSt3R alone 8.17 / 38.17 / 75.27

  — [arXiv HTML Table 2](https://arxiv.org/html/2510.23930v1)
- Replica (CD / F1 / NC):
  - **PlanarGS 4.13 / 81.90 / 89.88**
  - DN-Splatter 5.60 / 68.12
  - PGSR 8.56 / 62.98
  - 2DGS 10.54 / 52.91
  - 3DGS 12.57 / 41.64

  — [arXiv HTML Table 2](https://arxiv.org/html/2510.23930v1)
- Compute: training takes under 1 h on an RTX 3090, but DUSt3R inference was run on an A6000 (48 GB). Project page: planargs.github.io. — [arXiv HTML](https://arxiv.org/html/2510.23930v1)

**IndoorGS: Geometric Cues Guided Gaussian Splatting for Indoor Scene Reconstruction (CVPR 2025; Ruan, Wang, Guan, Zhang, Ju)**
- Core idea: 2D lines are extracted and fused into 3D line cues. SfM points are cleaned with statistical outlier removal. Plane cues for textureless regions come from monocular-depth alignment plus SAM segmentation. These cues drive both initialization and a "geometric-cue-guided adaptive density control". Each primitive carries a type label (line, SfM or plane Gaussian). The paper claims better geometry and rendering than 3DGS approaches on several indoor datasets. — [CVPR 2025 poster](https://cvpr.thecvf.com/virtual/2025/poster/33248), [CVPR supplement](https://openaccess.thecvf.com/content/CVPR2025/supplemental/Ruan_IndoorGS_Geometric_Cues_CVPR_2025_supplemental.pdf)

**GaussianRoom (arXiv 2405.19671): 3DGS + neural SDF, jointly optimized, for indoor scenes**
- Core idea: the SDF guides densification and pruning of the Gaussians, and the Gaussians narrow the SDF's ray-sampling range. Monocular normal and edge priors handle textureless walls and floors. — [arXiv HTML](https://arxiv.org/html/2405.19671)
- 8 ScanNet scenes and 2 ScanNet++ scenes; F-score (ScanNet / ScanNet++):
  - **GaussianRoom 0.768 / 0.872**
  - MonoSDF 0.609 / 0.827
  - SuGaR 0.366 / 0.439
  - 2DGS 0.324 / –
  - DN-Splatter 0.166 / 0.107
  - 3DGS 0.085 / 0.163

  — [arXiv HTML Table I](https://arxiv.org/html/2405.19671)
- PSNR (ScanNet / ScanNet++): GaussianRoom 23.601 / 22.001 vs 3DGS 22.133 / 21.816. — [arXiv HTML Table II](https://arxiv.org/html/2405.19671)
- Training takes about **4.5 h** (3DGS + mono cues about 1 h; MonoSDF about 18 h). Only a project page is linked. — [arXiv HTML](https://arxiv.org/html/2405.19671)

**Manhattan-world and structural priors in GS**
- MG-SLAM (arXiv 2405.20031) is an RGB-D GS-SLAM. It uses fused line segments for tracking in textureless indoor areas and builds on a Manhattan-world hypothesis. — [arXiv HTML](https://arxiv.org/html/2405.20031v3)
- "Structure-Aware Indoor RGB-D SLAM via Manhattan-Constrained 2D Gaussian Splatting" (CSIAM-AM, 2025) aligns Gaussian orientations and positions to the dominant axes. — [global-sci](https://www.global-sci.com/csiam-am/article/view/23858)
- QuickSplat (arXiv 2505.05591) learns data-driven priors that initialize 2DGS for large indoor scenes, which improves flat-wall geometry. — [arXiv abs](https://arxiv.org/abs/2505.05591)

### Inferences
- For white walls, the decisive ingredient is an **external geometric prior**: monocular or feed-forward depth and normals (Omnidata, DSINE, Metric3D, DUSt3R, VGGT) plus a plane assumption. The flat primitive alone is not enough. Evidence: on all three indoor datasets in the PlanarGS tables, PGSR and 2DGS (no external priors) are 2–3× worse in CD than DN-Splatter and PlanarGS.
- The cheapest high-value experiment for the user: run PlanarSplatting on the existing COLMAP model (about 3 min, Apache-2.0), then use its planes as Gaussian initialization for splatfacto. PlanarSplatting's own ScanNet test showed +1 dB PSNR with 0.37M instead of 1.27M Gaussians. Integrating this with gsplat/nerfstudio would require custom glue code.
- PlanarGS is the best documented result on phone-captured rooms (MuSHRoom). It needs about 48 GB VRAM for DUSt3R inference as run by the authors, so on Colab an A100 80GB or swapping in VGGT would likely be necessary.
- GaussianRoom (about 4.5 h) is too slow to be practical at building scale.

### Gaps
- The PGSR code license was not verified. The repo is zju3dv/PGSR, linked from the project page, and its license was not checked.
- PlanarGS code availability and license were not found on the pages fetched; only the project page is cited.
- IndoorGS numeric results, code and license were not retrieved.
- AirPlanes (CVPR 2024) is a non-GS baseline. Its numbers appear only via the PlanarSplatting table.
- QuadricGS / "Planar Gaussian Splatting" (WACV) details were not fetched. QGS (Quadratic GS) numbers appear only via the PlanarGS MuSHRoom table.
- No dedicated Manhattan-prior paper for offline (non-SLAM) indoor 3DGS with benchmark numbers was found.

## 2. Surface-based methods (2DGS, Gaussian Surfels, GOF, RaDe-GS, SuGaR, Trim, MILo): do they help geometry or PSNR?

### Takeaway
Surface methods mostly improve **geometry and normals, not PSNR**. On Mip-NeRF360, 2DGS is slightly below 3DGS (27.03 vs 27.24), PGSR roughly equal (27.25) and GOF slightly above (27.78). On indoor MuSHRoom, 2DGS, GOF, PGSR and QGS all render worse than or equal to 3DGS (24.4–25.7 vs 25.79), even though their CD improves. Without priors, they still fail on textureless indoor walls: CD around 7–12 cm, against about 4 cm for prior-based methods.

### Cited Findings
- **2DGS** (arXiv 2403.17888). Reported results:
  - DTU CD 0.80 mm in 0.32 h; T&T F1 0.32 (0.57 h); Mip-NeRF360 PSNR 27.03 / LPIPS 0.239. — [PGSR tables](https://arxiv.org/html/2406.06521)
  - MILo's table gives T&T F1 0.30. — [MILo arXiv HTML](https://arxiv.org/html/2506.24096)
  - Indoor (CD / F1 / NC): ScanNet++ 6.70 / 53.46 / 88.20; Replica 10.54 / 52.91 / 82.28; MuSHRoom 9.71 / 51.50 / 73.65 with PSNR 25.67. — [PlanarGS arXiv HTML](https://arxiv.org/html/2510.23930v1)
- **GOF (Gaussian Opacity Fields)**:
  - DTU CD 0.74 (2 h); T&T F1 0.46 (2 h); Mip-NeRF360 PSNR 27.78 / SSIM 0.835 / LPIPS 0.196, the best rendering among the surface methods in that table. — [PGSR tables](https://arxiv.org/html/2406.06521)
  - On indoor MuSHRoom it is the weakest: CD 12.07, PSNR 24.76. — [PlanarGS](https://arxiv.org/html/2510.23930v1)
- **RaDe-GS** (arXiv 2406.01467): DTU CD 0.68, T&T F1 0.40. Its mesh rendered on Mip-NeRF360 reaches PSNR 23.56. — [MILo arXiv HTML](https://arxiv.org/html/2506.24096)
- **SuGaR**: DTU CD 1.33; T&T F1 0.19; Mip-NeRF360 PSNR 26.10. — [PGSR tables](https://arxiv.org/html/2406.06521)
  - On ScanNet / ScanNet++, F-score 0.366 / 0.439, still better than vanilla 3DGS (0.085 / 0.163). — [GaussianRoom](https://arxiv.org/html/2405.19671)
- **MILo: Mesh-In-the-Loop GS** (arXiv 2506.24096, ACM TOG 2025). The core idea is to extract a mesh every iteration (Delaunay + differentiable marching tetrahedra) with gradients flowing back into the Gaussians.
  - T&T F1 0.47–0.49 (best explicit method); DTU CD 0.68.
  - About 4.36M mesh vertices, vs about 14.8–16.5M for 2DGS, GOF and RaDe-GS.
  - Mesh-only NVS on Mip-NeRF360: PSNR 24.09, vs RaDe-GS 23.56, GOF 20.78 and 2DGS 15.36.
  - About 50 min and about 10 GB VRAM on an RTX 4090 (dense variant about 110 min).
  - Code at anttwo.github.io/milo; license not stated on the fetched page.

  — [MILo arXiv HTML](https://arxiv.org/html/2506.24096)
- **DN-Splatter / AGS-Mesh** (nerfstudio-native):
  - Registers the `dn-splatter` and `ags-mesh` nerfstudio methods, with a splatfacto-based AGS-Mesh and a 2DGS branch.
  - Priors: Omnidata or DSINE normals, plus monocular depth scale-aligned to COLMAP SfM points.
  - Mesh export via `gs-mesh` (dn / tsdf / o3dtsdf (recommended) / sugar-coarse / marching), plus IsoOctree.
  - Apache-2.0; WACV 2025 (DN-Splatter) and 3DV 2025 (AGS-Mesh); gsplat ≥1.0 support.

  — [GitHub maturk/dn-splatter](https://github.com/maturk/dn-splatter)
  - Indoor results: MuSHRoom CD 5.77 / F1 61.86, but PSNR 24.80 (below 3DGS's 25.79) and LPIPS 0.2595 (worst). ScanNet++ CD 4.16. — [PlanarGS](https://arxiv.org/html/2510.23930v1)
  - GaussianRoom's own runs report a much weaker DN-Splatter (ScanNet F 0.166), which is a conflicting evaluation. — [GaussianRoom](https://arxiv.org/html/2405.19671)
- **Geometry-vs-appearance trade-off, in numbers**:
  - MuSHRoom: every geometry method except PlanarGS has PSNR ≤ 3DGS. — [PlanarGS](https://arxiv.org/html/2510.23930v1)
  - Prior-guided methods can improve both: PlanarGS (+0.63 dB on MuSHRoom), GaussianRoom (+1.47 dB on ScanNet), and PlanarSplatting init (+1.05 dB on ScanNetV2). — [PlanarGS](https://arxiv.org/html/2510.23930v1), [GaussianRoom](https://arxiv.org/html/2405.19671), [PlanarSplatting](https://arxiv.org/html/2412.03451)

### Inferences
- For a VR walkthrough where visual quality matters most, a pure surface method (2DGS, GOF, RaDe-GS) will not make walls look sharper. Their gain is in depth and normal consistency (floaters behind walls are reduced), which may help perceived stability in VR. The prior-plus-plane methods are the ones that improve both geometry and appearance.
- The large disagreement between papers on DN-Splatter (PlanarGS: strong; GaussianRoom: weak) means benchmark tables depend on settings. Claims should be validated on the user's own classroom (for example, wall-flatness RMS against measured dimensions).

### Gaps
- Gaussian Surfels (arXiv 2404.17774), Trim3DGS/Trim2DGS (arXiv 2406.07499) and GS-ROR: exact DTU/T&T numbers were not retrieved in this pass.
- Licenses were not verified for 2DGS (hbb1; believed to be the Inria non-commercial-derived license), GOF and RaDe-GS.
- No GPU-memory figures for PGSR, 2DGS or GOF were found, except gsplat's note that 2DGS adds about 4 GB VRAM overhead.

## 3. Integration with nerfstudio/gsplat 1.4 and export to Unity (aras-p) / standard 3DGS viewers

### Takeaway
gsplat ≥1.4 natively has a 2DGS rasterizer (`rasterization_2dgs`, with normals, depth normals, distortion and median depth). DN-Splatter and AGS-Mesh install as nerfstudio methods. Planar-GS research codes (PGSR, PlanarGS, PlanarSplatting) are standalone repos, not nerfstudio plugins. **2DGS PLYs are not directly compatible with 3DGS viewers**: they store only `scale_0, scale_1`, so conversion is needed. Planar and flattened 3DGS-style methods (PGSR, PlanarGS, PlanarSplatting + 3DGS init) keep the 3-scale 3DGS format.

### Cited Findings
- gsplat 1.4 (September 2024) merged 2DGS support, with about 4 GB VRAM overhead and prebuilt Linux/Windows wheels. gsplat 1.5 fixed 2DGS depth and normal calculations and the densification order. — [radiancefields gsplat 1.4](https://radiancefields.com/nerfstudio-release-gsplat-1-4), [radiancefields gsplat 1.5](https://radiancefields.com/gsplat-1-5-released-by-nef)
- gsplat API: `rasterization_2dgs()` uses ray-splat intersection and returns render_colors, render_alphas, render_normals, surf_normals, render_distort (an L1 variant, unlike the paper's L2), render_median and meta. `distloss=True` enables distortion regularization. — [gsplat docs](https://docs.gsplat.studio/main/apis/rasterization.html)
- 2DGS reference code: `_scaling` has shape (N, 2), and `save_ply` writes only `scale_0` and `scale_1`. — [hbb1/2d-gaussian-splatting gaussian_model.py](https://raw.githubusercontent.com/hbb1/2d-gaussian-splatting/main/scene/gaussian_model.py)
- SuperSplat requires the full 3DGS attribute set (position, `scale_*`, `rot_*`, opacity, `f_dc_*`, optional `f_rest_*`). — [PlayCanvas SuperSplat troubleshooting](https://developer.playcanvas.com/user-manual/supersplat/editor/troubleshooting/)
- aras-p UnityGaussianSplatting imports the original 3DGS PLY layout (plus Scaniverse SPZ) through Tools → Gaussian Splats → Create GaussianSplatAsset. — [aras-p docs index](https://docsearch.algolia.com/mcp/docs/repo/aras-p/unitygaussiansplatting)
- PlanarSplatting accepts COLMAP datasets (`run_demo_colmap.py`) or pose-free images via VGGT. — [GitHub](https://github.com/ant-research/PlanarSplatting)
- DN-Splatter exports meshes (o3dtsdf recommended), which can go to Unity as ordinary meshes. — [GitHub dn-splatter](https://github.com/maturk/dn-splatter)

### Inferences
- **2DGS → Unity**: add a `scale_2` column with a very small log-scale (for example log(1e-4·scene scale)) so each surfel becomes a thin 3D Gaussian. The aras-p importer will then load it. Rendering will be an approximation: 3DGS viewers use projected-covariance splatting, not 2DGS ray-splat intersection, so edge-on surfels and anti-aliasing will look somewhat different. This conversion is an inference; no source documents it.
- **Lowest-friction path** for the user's existing gsplat/splatfacto stack:
  - (a) Add depth and normal prior losses with DN-Splatter (`ns-train dn-splatter`). Output stays a 3DGS PLY, so it is Unity-compatible, and a mesh can be exported as well.
  - (b) Optionally, initialize from PlanarSplatting planes.
  - (c) For VR collision or navigation, export a mesh (DN-Splatter o3dtsdf, MILo or PlanarSplatting planes) and keep the splats for visuals.
- MILo (about 10 GB VRAM, about 50 min on a 4090) should fit on a Colab L4 (24 GB) or A100 for one classroom. Building scale will need chunking.

### Gaps
- No source confirms that nerfstudio's splatfacto exposes a 2DGS mode out of the box. gsplat has the rasterizer; splatfacto integration was not verified.
- No official 2DGS-to-3DGS PLY converter or aras-p documentation for surfels was found.
- Whether PGSR/PlanarGS PLYs load unchanged in aras-p was not verified. Both derive from the Inria 3DGS codebase, so a 3-scale layout is likely, but this is unconfirmed.
- Training time and memory at building scale (thousands of 4K frames) is not reported by any of these papers. All indoor benchmarks are single rooms.
