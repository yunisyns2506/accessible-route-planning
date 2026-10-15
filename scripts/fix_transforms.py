"""transforms.json dosyasini COLMAP'in EN BUYUK modelinden yeniden uretir.

Neden gerekli: nerfstudio process_data, transforms.json dosyasini her zaman
`colmap/sparse/0` klasorunden uretir. COLMAP birden fazla model urettiginde
(sahne parcalandiginda) en buyuk model `sparse/0` olmak zorunda degildir --
kucuk, dejenere bir artik model `sparse/0` olabilir. Bu durumda egitim yanlislikla
2-3 goruntuyle calisir.

Bu script her kosu klasorundeki modelleri sayar, en cok goruntu kaydedeni secer ve
transforms.json dosyasini ondan yeniden yazar.

Kullanim:
    python scripts/fix_transforms.py data/sinif-01/sfm_exhaustive [...]
"""
import json
import shutil
import sys
from pathlib import Path

from nerfstudio.data.utils.colmap_parsing_utils import read_images_binary
from nerfstudio.process_data.colmap_utils import colmap_to_json


def main() -> None:
    for arg in sys.argv[1:]:
        out_dir = Path(arg)
        sparse = out_dir / "colmap" / "sparse"
        models = [d for d in sorted(sparse.iterdir())
                  if d.is_dir() and (d / "images.bin").exists()]
        counts = {d: len(read_images_binary(str(d / "images.bin")))
                  for d in models}
        best = max(counts, key=counts.get)

        tj = out_dir / "transforms.json"
        before = 0
        if tj.exists():
            before = len(json.loads(tj.read_text(encoding="utf-8"))["frames"])
            shutil.copyfile(tj, tj.with_suffix(".json.bak"))

        n = colmap_to_json(recon_dir=best, output_dir=out_dir)
        after = len(json.loads(tj.read_text(encoding="utf-8"))["frames"])

        print(f"{out_dir.name}:")
        print(f"  modeller      : "
              + ", ".join(f"{d.name}={c}" for d, c in counts.items()))
        print(f"  secilen model : {best.name} ({counts[best]} goruntu)")
        print(f"  transforms.json: {before} -> {after} kare "
              f"(colmap_to_json: {n})")


if __name__ == "__main__":
    main()
