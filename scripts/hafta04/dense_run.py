"""Bir SfM ciktisindan COLMAP yogun rekonstruksiyonu (dense) uretir ve olcer.

Kullanim:
    python scripts/hafta04/dense_run.py <cikarici> <eslestirme> <mapper>

Ornek:
    python scripts/hafta04/dense_run.py sift exhaustive incremental

Adimlar (hepsi COLMAP 4.2.1 varsayilanlari):
    image_undistorter   kareleri bozulmadan arindirir; RTX 2060 6 GB'a sigmasi
                        icin uzun kenar 1000 piksele kucultulur
    patch_match_stereo  her kare icin derinlik ve normal haritasi (GPU)
    stereo_fusion       derinlik haritalarini yogun nokta bulutunda birlestirir
    poisson_mesher      yogun buluttan su gecirmez yuzey (Poisson)
    delaunay_mesher     gorunurluk tabanli yuzey (Delaunay)

Dense, SfM'in kamera pozlarini girdi alir; ayni pozlardan ayni sonuc cikacagi
icin her cikaricinin en iyi SfM ciktisinda bir kez kosulur.
Her asama icin sure, tepe RAM ve tepe VRAM kaydedilir.

Cikti: data/sinif-01/hafta-04/dense/<cikarici>_<eslestirme>_<mapper>/
       experiments/hafta-04_sinif-01/dense/<ad>.json
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import COLMAP, EXP, FRAMES, WORK, ResourceMonitor, read_json, write_json  # noqa: E402

MAX_IMAGE_SIZE = "1000"


def ply_counts(path: Path) -> dict:
    """PLY basligindan kose ve yuz sayisini okur."""
    out = {}
    if not path.exists():
        return out
    with open(path, "rb") as f:
        for raw in f:
            line = raw.decode("ascii", errors="replace").strip()
            if line.startswith("element vertex"):
                out["vertices"] = int(line.split()[-1])
            elif line.startswith("element face"):
                out["faces"] = int(line.split()[-1])
            elif line == "end_header":
                break
    out["size_mib"] = round(path.stat().st_size / 2**20, 1)
    return out


def main() -> int:
    ext, match, mapper = sys.argv[1:4]
    name = f"{ext}_{match}_{mapper}"
    pdir = WORK / "sfm" / ext / "r1" / match / mapper
    mp = read_json(pdir / "map.json")
    if not mp or mp.get("status") != "ok":
        print(f"SfM sonucu yok: {pdir}")
        return 1
    ws = WORK / "dense" / name
    res_path = EXP / "dense" / f"{name}.json"
    res = read_json(res_path) or {"run": name, "max_image_size": int(MAX_IMAGE_SIZE),
                                  "registered_images": mp["registered_main"]}
    stages = [
        ("undistort", [COLMAP, "image_undistorter", "--image_path", FRAMES,
                       "--input_path", pdir / "sparse" / mp["main_model"],
                       "--output_path", ws, "--output_type", "COLMAP",
                       "--max_image_size", MAX_IMAGE_SIZE]),
        ("patch_match", [COLMAP, "patch_match_stereo", "--workspace_path", ws,
                         "--workspace_format", "COLMAP",
                         "--PatchMatchStereo.geom_consistency", "true"]),
        ("fusion", [COLMAP, "stereo_fusion", "--workspace_path", ws,
                    "--workspace_format", "COLMAP", "--input_type", "geometric",
                    "--output_path", ws / "fused.ply"]),
        ("poisson", [COLMAP, "poisson_mesher", "--input_path", ws / "fused.ply",
                     "--output_path", ws / "meshed-poisson.ply"]),
        ("delaunay", [COLMAP, "delaunay_mesher", "--input_path", ws,
                      "--input_type", "dense", "--output_path", ws / "meshed-delaunay.ply"]),
    ]
    for stage, cmd in stages:
        if res.get(stage, {}).get("return_code") == 0:
            print(f"  atlandi (tamam): {stage}")
            continue
        if stage == "undistort" and ws.exists():
            shutil.rmtree(ws)
        mon = ResourceMonitor(interval=2.0)
        print(f"[{name}] {stage}")
        rc, sec = mon.run(cmd, ws.parent / f"{name}_{stage}.log")
        res[stage] = {"return_code": rc, "elapsed_min": round(sec / 60, 2), **mon.summary()}
        write_json(res_path, res)
        print(f"  rc={rc} {sec / 60:.1f} dk RAM {res[stage]['peak_ram_mib']} MiB "
              f"VRAM {res[stage]['peak_vram_mib']} MiB")
        if rc != 0:
            return 1
    res["fused"] = ply_counts(ws / "fused.ply")
    res["poisson"]["mesh"] = ply_counts(ws / "meshed-poisson.ply")
    res["delaunay"]["mesh"] = ply_counts(ws / "meshed-delaunay.ply")
    res["total_min"] = round(sum(res[s]["elapsed_min"] for s, _ in stages), 2)
    write_json(res_path, res)
    print(f"[{name}] yogun nokta {res['fused'].get('vertices')}, Poisson yuz "
          f"{res['poisson']['mesh'].get('faces')}, Delaunay yuz "
          f"{res['delaunay']['mesh'].get('faces')}, toplam {res['total_min']} dk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
