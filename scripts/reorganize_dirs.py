"""Dagnik outputs-* / exports-* / data klasorlerini duzenli bir yapiya tasir.

Hedef yapi:
    data/<veri-kumesi>/          ham kareler ve COLMAP ciktilari
    runs/<veri-kumesi>/<kosu>/   egitim ciktilari (kontrol noktalari)
    exports/<veri-kumesi>/<kosu>/splat.ply

Tasima sonrasi nerfstudio config.yml dosyalarindaki `output_dir` ve `data`
yollari yeni konuma gore yeniden yazilir; aksi halde ns-eval / ns-viewer
kontrol noktasini bulamaz.

Kullanim:
    python scripts/reorganize_dirs.py --dry-run
    python scripts/reorganize_dirs.py
"""
import shutil
import sys
from pathlib import Path

DRY = "--dry-run" in sys.argv

# eski yol -> yeni yol
DATA_MAP = {
    "data/room-01": "data/oda-01_video",
    "data/room-01-photos": "data/oda-01_79foto",
    "data/room-01-run3": "data/oda-01_512foto",
}
RUN_MAP = {
    "outputs": "runs/oda-01_video",
    "outputs-photos": "runs/oda-01_79foto",
    "outputs-run3": "runs/oda-01_512foto",
}
EXPORT_MAP = {
    "exports": "exports/oda-01_video",
    "exports-photos": "exports/oda-01_79foto",
    "exports-run3": "exports/oda-01_512foto",
}
# icerigi alt klasor olarak tasinacaklar
NESTED = {
    "outputs-sinif": "runs/sinif-01",
    "exports-sinif": "exports/sinif-01",
}


def move(src: Path, dst: Path) -> None:
    if not src.exists():
        print(f"  atlandi (yok): {src}")
        return
    if dst.exists():
        print(f"  atlandi (hedef var): {dst}")
        return
    print(f"  {src}  ->  {dst}")
    if not DRY:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))


def rewrite_path_block(lines: list[str], key: str, segments: list[str]) -> bool:
    """config.yml icindeki `<key>: ... WindowsPath` blogunu yeni segmentlerle yazar."""
    for i, line in enumerate(lines):
        if not line.startswith(f"{key}:") or "WindowsPath" not in line:
            continue
        j = i + 1
        while j < len(lines) and lines[j].startswith("- "):
            j += 1
        new = [f"- {s}\n" for s in segments]
        if lines[i + 1:j] == new:
            return False
        lines[i + 1:j] = new
        return True
    return False


def fix_configs() -> None:
    """Her config.yml icin output_dir'i kendi konumundan yeniden turetir."""
    for cfg in sorted(Path("runs").rglob("config.yml")):
        # <output_dir>/<experiment>/<method>/<timestamp>/config.yml
        out_dir = cfg.parent.parent.parent.parent
        lines = cfg.read_text(encoding="utf-8").splitlines(keepends=True)
        changed = rewrite_path_block(lines, "output_dir", list(out_dir.parts))
        for old, new in DATA_MAP.items():
            if any(Path(old).name in l for l in lines[:8]):
                changed |= rewrite_path_block(lines, "data", list(Path(new).parts))
                break
        if changed:
            if not DRY:
                cfg.write_text("".join(lines), encoding="utf-8")
            print(f"  config guncellendi: {cfg}")


def main() -> None:
    print("=== data/ ===")
    for a, b in DATA_MAP.items():
        move(Path(a), Path(b))

    print("=== egitim ciktilari -> runs/ ===")
    for a, b in RUN_MAP.items():
        move(Path(a), Path(b))
    for a, b in NESTED.items():
        if a.startswith("outputs") and Path(a).exists():
            for child in sorted(Path(a).iterdir()):
                move(child, Path(b) / child.name)
            if not DRY and not any(Path(a).iterdir()):
                Path(a).rmdir()

    print("=== PLY -> exports/ ===")
    # exports/ hedefin kendisi oldugu icin once gecici ada alinir
    if Path("exports").exists() and (Path("exports") / "splat.ply").exists():
        move(Path("exports"), Path("_exports_tmp"))
        EXPORT_MAP["_exports_tmp"] = "exports/oda-01_video"
        del EXPORT_MAP["exports"]
    for a, b in EXPORT_MAP.items():
        move(Path(a), Path(b))
    if Path("exports-sinif").exists():
        for child in sorted(Path("exports-sinif").iterdir()):
            move(child, Path("exports/sinif-01") / child.name)
        if not DRY and not any(Path("exports-sinif").iterdir()):
            Path("exports-sinif").rmdir()

    print("=== config.yml yollari ===")
    if not DRY:
        fix_configs()


if __name__ == "__main__":
    main()
