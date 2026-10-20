"""Bir SfM koşusunun en buyuk modelinden nerfstudio veri klasoru hazirlar.

Kullanim:
    python scripts/hafta04/make_ns_data.py <cikarici> <eslestirme> <mapper>

Ornek:
    python scripts/hafta04/make_ns_data.py sift exhaustive incremental
    -> data/sinif-01/hafta-04/ns/sift_exhaustive_incremental/

Kareler (ve 2/4/8 kat kucultulmus kopyalari) tum koşular icin bir kez
`ns/_images` altina kopyalanir; her koşu klasoru bunlara NTFS junction ile
baglanir, boylece disk kopyasi olusmaz.

SABIT TEST LISTESI: orijinal 349 karenin her 10. karesi (frame_0010,
frame_0020, ..., frame_0340; 34 kare) hicbir egitime girmez. Bir koşu bu
karelerin bir kismini kaydedemediyse yalnizca kaydedilenler test edilir; ortak
kesisim karsilastirmasi sonuc toplama asamasinda yapilir.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import FRAMES, WORK, read_json, write_json  # noqa: E402
from nerfstudio.process_data.colmap_utils import colmap_to_json  # noqa: E402
from nerfstudio.process_data.process_data_utils import copy_images  # noqa: E402

NS = WORK / "ns"
SHARED = NS / "_images"
TEST_EVERY = 10


def test_frames() -> set[str]:
    names = sorted(p.name for p in FRAMES.glob("*.jpg"))
    return {n for n in names if int(n[len("frame_"):-4]) % TEST_EVERY == 0}


def ensure_shared_images() -> dict[str, str]:
    """Orijinal ad -> nerfstudio adi eslemesi (frame_0001.jpg -> frame_00001.jpg)."""
    map_json = SHARED / "rename_map.json"
    if not map_json.exists():
        mapping = copy_images(FRAMES, SHARED / "images", num_downscales=3, verbose=False)
        write_json(map_json, {Path(k).name: Path(v).name for k, v in mapping.items()})
    return read_json(map_json)


def outlier_cameras(frames: list[dict], k: int = 3, factor: float = 10.0) -> set[int]:
    """Sahneden kopuk (yanlis pozlanmis) kameralari bulur.

    Bir kameranin en yakin k kameraya ortalama uzakligi, tum kameralardaki
    medyanin `factor` katini asarsa aykiri sayilir. Gerekce: nerfstudio sahneyi
    en uzak kameraya gore olcekler; tek bir kopuk kamera tum odayi kucuk bir
    bolgeye sikistirir ve 3DGS yakin nesneleri ogrenemez. Kural tum koşulara
    ayni bicimde uygulanir; atilan kare sayisi split.json'a yazilir.
    """
    import numpy as np
    from scipy.spatial import cKDTree
    centers = np.array([f["transform_matrix"] for f in frames])[:, :3, 3]
    d, _ = cKDTree(centers).query(centers, k=k + 1)
    nn = d[:, 1:].mean(1)
    return set(np.where(nn > factor * np.median(nn))[0].tolist())


def junction(link: Path, target: Path) -> None:
    if link.exists():
        return
    subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                   check=True, capture_output=True)


def main() -> int:
    ext, match, mapper = sys.argv[1], sys.argv[2], sys.argv[3]
    pdir = WORK / "sfm" / ext / "r1" / match / mapper
    mp = read_json(pdir / "map.json")
    if not mp or mp.get("status") != "ok":
        print(f"SfM sonucu yok ya da N/A: {pdir}")
        return 1

    rename = ensure_shared_images()
    run = f"{ext}_{match}_{mapper}"
    out = NS / run
    out.mkdir(parents=True, exist_ok=True)
    for sub in ("images", "images_2", "images_4", "images_8"):
        junction(out / sub, SHARED / sub)

    recon = pdir / "sparse" / mp["main_model"]
    n = colmap_to_json(recon_dir=recon, output_dir=out, image_rename_map=rename)

    tf = read_json(out / "transforms.json")
    inv = {v: k for k, v in rename.items()}
    outliers = outlier_cameras(tf["frames"])
    outlier_names = sorted(inv[Path(f["file_path"]).name] for i, f in enumerate(tf["frames"])
                           if i in outliers)
    tf["frames"] = [f for i, f in enumerate(tf["frames"]) if i not in outliers]
    tests = test_frames()
    train, test = [], []
    for fr in tf["frames"]:
        orig = inv[Path(fr["file_path"]).name]
        (test if orig in tests else train).append(fr["file_path"])
    tf["train_filenames"] = sorted(train)
    tf["val_filenames"] = sorted(test)
    tf["test_filenames"] = sorted(test)
    write_json(out / "transforms.json", tf)

    info = {"run": run, "sfm_dir": str(pdir), "model": mp["main_model"],
            "registered": n, "outlier_cameras": len(outliers), "outlier_frames": outlier_names,
            "train": len(train), "test": len(test),
            "test_total": len(tests),
            "test_frames": sorted(inv[Path(f).name] for f in test)}
    write_json(out / "split.json", info)
    print(f"{run}: {n} poz, aykiri kamera {len(outliers)}, egitim {len(train)}, test {len(test)}/{len(tests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
