"""Bir COLMAP SfM cikti klasorunun istatistiklerini cikarir.

Kullanim:
    python scripts/colmap_stats.py data/sinif-01/sfm_sequential [...]

Her klasor icin kaydolan goruntu sayisi, 3B nokta sayisi, ortalama iz uzunlugu,
ortalama yeniden izdusum hatasi ve uretilen model sayisi yazdirilir.
Sonuc ayni zamanda <klasor>/sfm_stats.json dosyasina yazilir.
"""
import json
import sys
from pathlib import Path

import numpy as np
from nerfstudio.data.utils.colmap_parsing_utils import (
    read_images_binary,
    read_points3D_binary,
)


def model_stats(model_dir: Path) -> dict:
    images = read_images_binary(str(model_dir / "images.bin"))
    points = read_points3D_binary(str(model_dir / "points3D.bin"))
    track = [len(p.image_ids) for p in points.values()]
    error = [p.error for p in points.values()]
    return {
        "model": model_dir.name,
        "registered_images": len(images),
        "points3D": len(points),
        "mean_track_length": round(float(np.mean(track)), 2) if track else 0.0,
        "mean_reproj_error_px": round(float(np.mean(error)), 3) if error else 0.0,
    }


def run_stats(out_dir: Path) -> dict:
    sparse = out_dir / "colmap" / "sparse"
    models = sorted(d for d in sparse.iterdir()
                    if d.is_dir() and (d / "images.bin").exists())
    stats = [model_stats(d) for d in models]
    # Egitimde kullanilan model: en cok goruntu kaydeden
    main = max(stats, key=lambda s: s["registered_images"]) if stats else {}

    timing = {}
    tp = out_dir / "timing.json"
    if tp.exists():
        timing = json.loads(tp.read_text(encoding="utf-8"))

    n_input = timing.get("input_frames") or len(
        list((out_dir / "images").glob("*.jpg")))

    result = {
        "run": out_dir.name,
        "matching_method": timing.get("matching_method"),
        "elapsed_minutes": timing.get("elapsed_minutes"),
        "input_frames": n_input,
        "n_models": len(stats),
        "main_model": main,
        "registration_rate": (round(main["registered_images"] / n_input, 3)
                              if main and n_input else None),
        "all_models": stats,
    }
    (out_dir / "sfm_stats.json").write_text(json.dumps(result, indent=2),
                                           encoding="utf-8")
    return result


def main() -> None:
    rows = []
    for arg in sys.argv[1:]:
        r = run_stats(Path(arg))
        rows.append(r)
        m = r["main_model"]
        print(f"\n=== {r['run']}  ({r['matching_method']}) ===")
        print(f"  sure                : {r['elapsed_minutes']} dk")
        print(f"  girdi kare          : {r['input_frames']}")
        print(f"  uretilen model      : {r['n_models']}")
        print(f"  kaydolan goruntu    : {m['registered_images']} "
              f"(%{100 * r['registration_rate']:.1f})")
        print(f"  3B nokta            : {m['points3D']}")
        print(f"  ort. iz uzunlugu    : {m['mean_track_length']}")
        print(f"  ort. yeniden izdusum: {m['mean_reproj_error_px']} px")
        if r["n_models"] > 1:
            print("  diger modeller      : "
                  + ", ".join(f"{s['model']}={s['registered_images']}"
                              for s in r["all_models"] if s != m))

    if len(rows) > 1:
        print("\n--- KARSILASTIRMA ---")
        hdr = f"{'kosu':<22}{'sure dk':>9}{'kayit %':>9}{'nokta':>9}{'iz':>7}{'hata px':>9}{'model':>7}"
        print(hdr)
        for r in rows:
            m = r["main_model"]
            print(f"{r['matching_method'] or r['run']:<22}"
                  f"{r['elapsed_minutes']:>9}"
                  f"{100 * r['registration_rate']:>9.1f}"
                  f"{m['points3D']:>9}"
                  f"{m['mean_track_length']:>7}"
                  f"{m['mean_reproj_error_px']:>9}"
                  f"{r['n_models']:>7}")


if __name__ == "__main__":
    main()
