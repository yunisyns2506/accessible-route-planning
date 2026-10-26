# Capture-side best practices for 3DGS/NeRF/photogrammetry of textureless indoor spaces (2022–2026)

Context: a classroom was captured with handheld 4K phone video (white walls, grey floor, large windows) and processed with COLMAP and nerfstudio splatfacto. The walls and floors came out blurry or "cloudy". The next step is capturing whole buildings (corridors, stairs, classrooms).

Source caveat: most capture guidance is vendor or practitioner documentation (PlayCanvas, Magnopus, Aholo, Scaniverse, Polycam, RadianceFields), not controlled studies. The only peer-reviewed quantitative evidence found here is Seiskari et al., ECCV 2024, on blur and rolling shutter.

## 1. Camera settings (exposure, shutter, fps, 4K vs photos, HDR, stabilization, lens, focus, apps)

### Takeaway
Lock everything (exposure, ISO, white balance, focus) for the whole session. Use a shutter of at least 1/125 s as a hard floor; practitioners prefer about 1/250–1/500 s. Stills beat video for sharpness and resolution. If you use video, record 4K at 60 fps or more with manual exposure and high bitrate, then extract and cull frames. Turn stabilization off on dedicated cameras.

### Cited Findings
- Exposure consistency is called "the most critical aspect". Use manual mode to lock aperture, shutter and ISO for the entire session. If unsure, read the auto settings from the first shot and enter them manually. — [PlayCanvas: Taking photos](https://developer.playcanvas.com/user-manual/gaussian-splatting/creating/taking-photos/)
- PlayCanvas numeric settings:
  - Shutter: at least 1/125 s handheld.
  - Aperture: f/8–f/11. Avoid f/1.4–2.8 and f/16 or smaller.
  - ISO: indoor 200–400 (max 800), low light 400–800 (max 1600). Adding light is preferred over pushing ISO.
  - Focal length: 35–85 mm equivalent. Avoid lenses under 24 mm (distortion).
  - Resolution: 20 MP or more for room-scale scenes.
  - RAW, or the highest-quality JPEG.
  - Manual focus, or single-point AF on the same feature throughout.
  - Manual white balance for mixed lighting.

  — [PlayCanvas](https://developer.playcanvas.com/user-manual/gaussian-splatting/creating/taking-photos/)
- PlayCanvas video recommendations: 4K minimum ("1080p is insufficient"), 60 fps or higher, manual exposure, maximum bitrate, stable colour temperature. Extract every 2nd–5th frame depending on movement speed, and check for motion blur. Stills give higher resolution, better low-light performance and no compression artefacts. — [PlayCanvas](https://developer.playcanvas.com/user-manual/gaussian-splatting/creating/taking-photos/)
- RadianceFields gives 1/500 s as the slowest shutter its contacts would use. The author has gone down to 1/100 s depending on the subject. Best-case combination: 1/500 s, f/11, ISO 800. Raise ISO freely (clean results above 1000, up to 3200) rather than lengthen the shutter. Do not go below f/3.2. The iPhone's deep depth of field makes it a good capture device. — [RadianceFields: Best camera settings](https://radiancefields.com/what-are-the-best-camera-settings-to-take-a-nerf)
- Magnopus (indoor house capture):
  - Use one prime lens and one sensor per room.
  - Lock shutter, aperture, ISO, colour temperature and focus.
  - Turn off in-body image stabilization (IBIS).
  - Prefer stills over video, and RAW.
  - Use a polarizer for reflections.
  - Use a monopod, tripod or faster shutter against blur.
  - Adjust shutter and aperture before ISO. One scene shot at ISO 40,000 on full frame still reconstructed.

  — [Magnopus: Allee Willis House](https://www.magnopus.com/blog/lessons-in-gaussian-splats-from-the-allee-willis-house)
- Magnopus found that 4K video frames carry less detail than full-frame stills. Video worked when good light allowed fast shutters. — [Magnopus](https://www.magnopus.com/blog/lessons-in-gaussian-splats-from-the-allee-willis-house)
- Aholo also recommends AE lock to prevent brightness flicker between frames, a shutter of at least about 1/125 s, and f/8–f/11. — summarized in search results from [Aholo: Space capture optimization](https://aholo.featurebase.app/help/articles/7063834-space-capture-optimization). Not fetched directly.
- Blackmagic Camera for iOS provides the controls practitioners need: shutter set as speed or angle, "Lock White Balance on Record", a flicker-free shutter option for 50 Hz or 60 Hz, and colour spaces Rec.709, P3, HLG, HDR10, Apple Log and ACES. — [Blackmagic Camera for iOS tech specs](https://www.blackmagicdesign.com/uk/products/blackmagiccamera/techspecs)
- Rolling shutter: Android phones (Samsung S20 FE, Pixel 5) have a "relatively large" readout time. On the iPhone the rolling-shutter effect was described as "negligible". — [Seiskari et al., ECCV 2024](https://arxiv.org/html/2403.13327v3)
- Seiskari et al. measured PSNR on synthetic scenes with and without their compensation:

  | Degradation | Scene | PSNR uncompensated | PSNR compensated |
  |---|---|---|---|
  | Motion blur | Cozyroom | 26.6 dB | 32.2 dB |
  | Rolling shutter | Cozyroom | 19.2 dB | 35.8 dB |

  On real phone data the average was 26.9 dB → 28.6 dB. Blurry frames also make COLMAP registration fail. Pre-processing deblur or de-rolling-shutter (MPR, CVR) gave mixed results and hurt on the iPhone. — [Seiskari et al., ECCV 2024](https://arxiv.org/html/2403.13327v3)

### Inferences
- The phone's default video mode probably caused part of the blur. In normal light, auto exposure on phones often picks a shutter around 1/50–1/100 s (the 180° rule at 30 fps is 1/60 s). Smart HDR or Dolby Vision tone-mapping and auto white balance also shift the appearance of white walls between frames. Both effects would show up as blurry, cloudy walls. Use a manual-control app (Blackmagic Camera, ProCam or Filmic-style), set SDR Rec.709 (HDR off), and fix ISO, shutter, WB and focus.
- A neutral, non-log profile is likely safer. COLMAP and 3DGS assume consistent 8-bit-like images, and Apple Log or HLG footage needs a correct LUT conversion before frame extraction. No source tested log profiles for GS. See Gaps.
- Electronic image stabilization (EIS) crops and warps each frame differently, which breaks the fixed-intrinsics assumption in COLMAP. This agrees with Magnopus's "turn off IBIS" advice for dedicated cameras. OIS is less harmful but still shifts the principal point slightly. Turn EIS ("Enhanced stabilization", Action mode) off and use slow movement or a gimbal instead.
- Lens choice: the main 1x (about 24–26 mm equivalent) phone camera is the safest. The ultra-wide (13 mm) sees more texture per frame, which helps registration on white walls, but it is softer, more distorted and often has fixed focus. If you use it, use only that lens for the whole capture and model it as OPENCV/fisheye in COLMAP. Do not mix lenses.
- Choosing between video and stills: 4K video (8.3 MP) at 1/500 s and 60 fps can reach comparable splat quality if frames are culled. A 12–48 MP still burst at fixed intervals gives more detail on low-texture surfaces, where fine grain (paint roller texture, floor speckle) is the only feature signal.

### Gaps
- No primary source gave a controlled test of EIS on vs off, OIS, or log vs Rec.709 for GS or NeRF quality.
- No official GS-specific settings guides were found for ProCam or LumaFusion. LumaFusion is an editor, not a capture app.
- No Jawset Postshot capture documentation was found in this search.
- Luma AI's former capture best-practices page now serves Dream Machine content, so the old capture guidance could not be retrieved.

## 2. Capture trajectory (distance, overlap, patterns, corners, heights, loops, speed, windows)

### Takeaway
Walk the perimeter at about 1–3 m from walls, start at a corner, and do at least one full loop plus a center pass, at multiple heights. Keep 70–80% overlap. Use inward-facing ("concave") arcs, never turn in place like a panorama, and include room context (edges, doors, furniture) in every frame of a white wall. Scaniverse adds that 1–3 minute captures can beat longer ones.

### Cited Findings
- Aholo indoor guide:
  - Walk at about 0.6 m/s, holding the device with both hands.
  - Stay 1–3 m from walls.
  - Capture walls floor-to-ceiling and tilt up for ceiling edges.
  - Start at a corner, aim at it, and walk at least one full perimeter loop (an extra loop for large rooms).
  - Focus on corners, edges, doors, windows and furniture backs.
  - Get at least about 20 key viewpoints and at least 70% overlap.
  - For blank white walls, step back and include textured elements in frame.

  — [Aholo: Indoor space capture guide](https://aholo.featurebase.app/help/articles/7830674-indoor-space-capture-guide)
- PlayCanvas overlap and patterns:
  - 70–80% overlap within a row, 60–70% between rows or heights, 15–30° between adjacent viewpoints.
  - For rooms, a systematic grid at varied heights (standing, crouching, elevated), covering corners, edges and ceiling-floor junctions.
  - 200–500+ photos for large subjects.

  — [PlayCanvas](https://developer.playcanvas.com/user-manual/gaussian-splatting/creating/taking-photos/)
- Magnopus trajectory advice:
  - At least 70% overlap, ideally 80%.
  - Circles or domes at several heights. Where blocked, concave half-shell arcs pointed at a focal point.
  - Avoid convex arcs (camera pointing outward).
  - If moving in straight lines, change angle occasionally.

  — [Magnopus](https://www.magnopus.com/blog/lessons-in-gaussian-splats-from-the-allee-willis-house)
- Scaniverse capture advice:
  - Spend 1–3 minutes ("Any longer, and the quality may actually decline").
  - Walk slowly and vary high/low, near/far, face-on and angled views.
  - For large scenes, imagine an object at the centre. Don't spin in place like a panorama.
  - Move even slower in dim scenes.
  - Re-cover areas that stay blurry in the preview.

  — [Scaniverse: Top 10 scanning tips](https://community.scaniverse.com/t/top-10-scanning-tips/65), [Scaniverse: High-quality splats](https://community.scaniverse.com/t/how-do-i-create-high-quality-splats-in-scaniverse/62)
- Polycam interior guidance (via search summary):
  - Walk the perimeter first, then a center pass.
  - At least 75% overlap with the previous shot, plus extra shots at corners.
  - Keep the room static; even a moved cushion or curtain between passes confuses alignment.
  - To stitch sessions, start each new session at a recognizable feature from the last one (doorway, corner).

  — [Polycam: High-fidelity interior scans in Object Mode](https://learn.poly.cam/hc/en-us/articles/48339214285844), [Polycam: How to scan a building](https://poly.cam/blog/how-to-scan-a-building-interior-exterior-and-multi-story-workflows)
- For buildings, Polycam advises one pass down the centreline of corridors and moving "deliberately slower" on stairs. It gives no numbers. — [Polycam building blog](https://poly.cam/blog/how-to-scan-a-building-interior-exterior-and-multi-story-workflows)
- Yembo warns against pointing the camera straight at white walls or patternless light floors and recommends a wider view that includes other things. It suggests splitting rooms over 1200 sq ft (about 110 m²) into two scans. Realsee notes that highly similar spaces can cause stitching failures. — [Yembo best practices](https://docs.yembo.ai/en/articles/8532100-scanning-best-practices), [Realsee](https://home.realsee.ai/en/book/h9tioaij/SWA9BlEp)
- Giraffe360's GS guidance (360 camera):
  - Use more and closer positions than for standard tours, with each position visible from the previous one.
  - Capture each room from more than one angle, including corners and stairs top and bottom.
  - Don't place positions in doorways.
  - Keep doors in a fixed state and don't open or close them mid-capture.

  — [Giraffe360 capture guidelines](http://docs.giraffe360.com/en/articles/12356634-pro-camera-capture-guidelines)
- Windows and reflections:
  - Close blinds against bright patches. — [SketchUp: Gaussian splats best practices](https://help.sketchup.com/gaussian-splats-best-practices)
  - Avoid or cover mirrors and glass. — [Aholo](https://aholo.featurebase.app/help/articles/7830674-indoor-space-capture-guide)
  - Use a (cross-)polarizer. Flat mirrors reconstruct reasonably well; curved reflective surfaces do not. — [Magnopus](https://www.magnopus.com/blog/lessons-in-gaussian-splats-from-the-allee-willis-house)
  - Splats render view-dependent effects, so capture shiny surfaces from many angles. — [Scaniverse](https://community.scaniverse.com/t/top-10-scanning-tips/65)

### Inferences
- For the classroom, likely failure modes are a single walking pass with the camera facing walls head-on at short distance and auto exposure swinging with the windows. A better plan: two perimeter loops facing inward (cameras looking across the room so each frame contains wall, floor, ceiling and a corner), one center pass looking outward diagonally, and three heights (about 0.8, 1.5 and 2.0 m) with the phone tilted down to the floor and up to the ceiling junction. Close the loop by returning to the start corner.
- Corridors (convex/forward motion is the worst case for SfM): walk the centreline twice in each direction, with the camera yawed about 30–45° toward each wall rather than straight ahead. Add short lateral "zig-zag" side-steps at doors and junctions, and pause at features. Treat each corridor-classroom doorway as a stitching anchor captured from both sides.
- Stairs: move slower, capture from the top and bottom landings looking along the flight, and add side-on views of the treads.

### Gaps
- No source gives a validated optimal distance for white walls specifically, or a corridor-specific overlap number.
- No quantitative study comparing "lawnmower" with "orbit" patterns for indoor GS was found.

## 3. Adding texture (markers, projected patterns, coded targets, tape)

### Takeaway
On uniform walls, temporary markers (black dots or tape) and projected patterns create features for SfM and MVS. They are recommended by practitioners and supported by classic photogrammetry literature. The cost: markers appear in GS renders and must be removed in editing, and projected patterns violate GS's static-appearance assumption unless used only for a separate geometry/pose pass.

### Cited Findings
- Uniform walls and ceilings appear as blurry, cloudy areas because they lack feature points. In controlled settings, add temporary markers (black dots or tape) and remove them later during editing. Shoot many angles and plan manual cleanup. Depth sensors (LiDAR or structured light) help. — [Magnopus](https://www.magnopus.com/blog/lessons-in-gaussian-splats-from-the-allee-willis-house)
- Polycam's photo-mode guide lists featureless surfaces ("plain white, blank walls") as problem subjects. For photogrammetry of shiny surfaces it suggests covering them with paper and a scribble pattern. — [Polycam: Photo mode](https://learn.poly.cam/photo-mode)
- Projected texture literature:
  - Hafeez et al. (2018): a calibrated projector casting a pattern on textureless objects yields models with millimetre-level height error. Pattern shape, size, colour and arrangement strongly affect data quality. — [Hafeez et al. 2018](https://yadda.icm.edu.pl/baztech/element/bwmeta1.element.baztech-365cbf40-578e-494d-8a8c-9f272a7fa5d7/c/Hafeez_The-effect_MMS_4_2018.pdf)
  - Maas (1996) used a projected random dot pattern for close-range surfaces without texture. — [ISPRS 1996](https://WWW.ISPRS.org/proceedings/XXIX/congress/part5/709_XXIX-part5.pdf)
  - White-light projection reached agreement to 0.3–0.4 mm on a gearbox surface. Larger deviations occurred where image texture was lower. — [Remote Sensing 12(23):3886](https://mdpi-res.com/d_attachment/remotesensing/remotesensing-12-03886/article_deploy/remotesensing-12-03886.pdf)

### Inferences
- For building-scale GS where markers can't stay, a practical two-pass approach:
  - Pass A: add removable features (masking-tape crosses, printed AprilTag or ArUco sheets, a few posters, or a projector with a random-dot pattern) and capture for poses and geometry.
  - Pass B: remove them and capture again from the same trajectory, registering B to A's model (COLMAP `image_registrator` / `point_triangulator` against A's model).

  This is an engineering inference and was not tested in any cited source.
- Coded targets (AprilTag or ArUco, printed at known size) also give metric scale. Two targets a measured distance apart (tape-measured, e.g. 2.000 m) let you scale the COLMAP model. In GS renders they are visible but small and easy to crop.
- A cheaper "texture" source is the scene itself: framing that includes edges, furniture and floor seams (Aholo, Yembo) often fixes registration without any markers. The remaining blur on walls is then a GS densification problem (no multi-view photometric gradient), not purely capture.

### Gaps
- No 2022–2026 study was found that quantifies marker or projector effects on 3DGS quality (as opposed to photogrammetry). No study measured how visible markers degrade GS renders.

## 4. Lighting and flicker

### Takeaway
Use bright, even, steady light: turn all room lights on and close blinds against hot spots. Keep WB fixed. Avoid shutter or LED interactions that cause banding by using an app's anti-flicker option for 50 Hz mains (Turkey/Europe).

### Cited Findings
- Avoid direct sunlight and single hard lights. Prefer soft, diffused light from multiple sources. Keep colour temperature consistent with manual WB under mixed light. — [PlayCanvas](https://developer.playcanvas.com/user-manual/gaussian-splatting/creating/taking-photos/)
- Turn on all lights; bright and even illumination works best. — [Aholo](https://aholo.featurebase.app/help/articles/7830674-indoor-space-capture-guide)
- Bright, even light is best; dim scenes require slower movement. — [Scaniverse tips](https://community.scaniverse.com/t/top-10-scanning-tips/65)
- Close blinds to avoid bright patches. — [SketchUp](https://help.sketchup.com/gaussian-splats-best-practices)
- Blackmagic Camera offers a flicker-free shutter option based on 50 Hz or 60 Hz. — [Blackmagic Camera specs](https://www.blackmagicdesign.com/uk/products/blackmagiccamera/techspecs)

### Inferences
- Under 50 Hz mains, lamps modulate at 100 Hz. Shutter speeds that are integer multiples of 1/100 s (1/100, 1/50) average out flicker but are too slow against motion blur. Fast shutters (1/250–1/500 s) can show banding or brightness pumping under cheap LED or fluorescent drivers. Practical resolution: test a 10 s clip at 1/250 and 1/500 s under the classroom lights. If banding appears, try the app's flicker-free shutter setting or rely on daylight from the windows plus lights. This is physics reasoning, not sourced from a GS guide.
- Large windows mean a large dynamic range. Lock exposure for the interior (walls slightly bright but not clipped) and accept clipped windows rather than letting AE swing. Capture on an overcast day, or close blinds partially, to reduce the contrast.

### Gaps
- No GS-specific source quantified flicker effects or gave exact anti-flicker shutter values for phones.

## 5. Extra sensors (LiDAR/ARKit apps, 360 cameras, scale references)

### Takeaway
LiDAR/ARKit apps (Polycam, Record3D, Spectacular AI) give metric poses and depth that bypass COLMAP's failure on white walls, and nerfstudio ingests them directly. 360 cameras (Insta360) cover a whole room per frame, so every frame includes textured context, and nerfstudio supports equirectangular input.

### Cited Findings
- nerfstudio data importers:
  - Polycam: needs an iOS device with LiDAR, Developer mode enabled, and "raw data" export. It does not need COLMAP.
  - Record3D: iPhone 12 Pro or newer, EXR + JPG export, optional PLY point cloud; `--voxel-size` defaults to 0.8.
  - KIRI Engine: Developer Mode with the camera-pose option, on Android or iPhone without LiDAR.
  - Spectacular AI: records IMU on LiDAR iPhones or OAK-D/RealSense devices. `--key_frame_distance` 0.15 for room-sized scans, 0.05 for small scans.

  — [nerfstudio custom data docs](https://docs.nerf.studio/quickstart/custom_dataset.html)
- 360 cameras:
  - nerfstudio supports equirectangular 360 images and video (`--camera-type equirectangular`). `--images-per-equirect` defaults to 8; use 14 if detail or COLMAP alignment is poor.
  - Crop the operator out with `--crop-bottom` or `--crop-factor`.
  - For 360 video, hold the camera above your head.
  - Suggested frame target: about 3 × video length in seconds.

  — [nerfstudio](https://docs.nerf.studio/quickstart/custom_dataset.html)
- Niantic/Scaniverse documents a 360-camera workflow. — [Niantic Spatial: 360 camera docs](https://ardk-dev-documentation.eng.nianticspatial.com/docs/scaniverse/360camera/) (not fetched)
- Depth sensors (LiDAR, structured light) are recommended for white walls; add a scale reference. — [Magnopus](https://www.magnopus.com/blog/lessons-in-gaussian-splats-from-the-allee-willis-house)
- Using VIO/IMU velocities for blur and rolling-shutter compensation improved PSNR on phone data. — [Seiskari et al. 2024](https://arxiv.org/html/2403.13327v3)

### Inferences
- For the next capture, running Polycam or Record3D on a LiDAR iPhone in parallel with (or instead of) the 4K video gives ARKit poses plus depth. These can serve as a pose initialization or a depth prior (e.g. splatfacto with depth supervision, or DN-Splatter) to flatten white walls. A 360 pass is a cheap complement for corridors.

### Gaps
- No quantitative comparison was found of LiDAR-pose vs COLMAP-pose GS quality on textureless rooms.

## 6. Frame selection (blur detection, frame counts)

### Takeaway
Extract more frames than needed, then keep the sharpest per window, using Laplacian-variance-style scores or tools like Sharp Frames. Room-scale scenes typically use a few hundred to about 1000–2000 frames. SfM slows sharply beyond about 5000.

### Cited Findings
- From video, extract every 2nd–5th frame and check for blur. Sharp Frames is suggested for automatic selection. Large subjects need 200–500+ photos. — [PlayCanvas](https://developer.playcanvas.com/user-manual/gaussian-splatting/creating/taking-photos/)
- Magnopus photo-count tiers (by fidelity):

  | Fidelity | Photos |
  |---|---|
  | Very high | 3000–5000 |
  | High | 1000–2000 |
  | Medium | 500–900 |
  | Lower | 100–400 |

  SfM slows significantly and can exhaust memory beyond about 5000. — [Magnopus](https://www.magnopus.com/blog/lessons-in-gaussian-splats-from-the-allee-willis-house)
- Seiskari et al. picked keyframes at least 10 cm apart and took the least-blurry frame from each group of 8 consecutive keyframes. — [Seiskari et al. 2024](https://arxiv.org/html/2403.13327v3)
- Cull blurry frames prior to processing (strongly recommended). — [RadianceFields](https://radiancefields.com/what-are-the-best-camera-settings-to-take-a-nerf)
- RealityScan mobile auto-capture is limited to 300 images. — [RealityScan step-by-step guide](https://dev.epicgames.com/documentation/realityscan-mobile/realityscan-step-by-step-guide)

### Inferences
- For a classroom from 4K60 video: extract about 3–5 fps candidates, compute the variance of the Laplacian on a grayscale downscaled frame, and keep the sharpest frame in each 0.5 s window. Target 500–1000 frames per classroom (matching the project's planned 500–1000). Use a relative blur threshold (e.g. drop frames below about 50–60% of the local median score), not an absolute one, because white walls naturally have low Laplacian variance.

### Gaps
- No source validated a specific Laplacian threshold for indoor textureless scenes.
