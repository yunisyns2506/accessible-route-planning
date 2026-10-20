"""Bir COLMAP veritabanindaki tanimlayicilardan sozluk agaci (vocab tree) kurar.

Kullanim:
    python scripts/hafta04/build_vocab_tree.py <features.db> <cikti.bin> [gorsel_sozcuk]

Neden: COLMAP 4.2.1'in `vocab_tree_builder` komutu dizini sabit olarak 128
boyutlu tanimlayicilar icin olusturur (`VisualIndex::Create()` varsayilanlari).
SIFT ve ALIKED 128 boyutludur; LoMa (LOMA_B) tanimlayicisi 256 boyutludur ve
komut bu durumda coker (0xC0000409). COLMAP'in ic kutuphanesi 256/64 boyutlu
dizini destekler; bu betik ayni dizini pycolmap uzerinden dogru boyutla kurar.
Kurma ayarlari `vocab_tree_builder` varsayilanlariyla aynidir (100 yineleme,
3 tur, tum tanimlayicilar); yalniz gorsel sozcuk sayisi varsayilan 65.536 yerine
8.192'dir: faiss k-ortalamalar sozcuk basina en az 39 ornek ister (65.536 icin
2,56 milyon), LoMa veritabaninda 714.752 tanimlayici vardir ve 65.536 sozcukle
kurulum tek cekirdekte 13 dakikada bitmeyip durdurulmustur.

pycolmap 4.2.1, nerfstudio ortamini bozmamak icin ayri klasorden yuklenir:
    PYTHONPATH=C:/Users/sabod/tools/pycolmap-4.2.1
"""
import sys
import time

import numpy as np
import pycolmap


def main() -> int:
    db_path, out_path = sys.argv[1], sys.argv[2]
    num_words = int(sys.argv[3]) if len(sys.argv) > 3 else 8192
    db = pycolmap.Database.open(db_path)
    blocks, ftype = [], None
    for im in db.read_all_images():
        d = db.read_descriptors(im.image_id)
        ftype = d.type
        blocks.append(np.asarray(d.to_float().data, dtype=np.float32))
    data = np.concatenate(blocks)
    print(f"{len(blocks)} kare, {data.shape[0]} tanimlayici, boyut {data.shape[1]}, tur {ftype}")
    index = pycolmap.VisualIndex.create(data.shape[1], 64)
    t0 = time.time()
    opts = pycolmap.VisualIndex.BuildOptions()
    opts.num_visual_words = num_words
    index.build(opts,
                pycolmap.FeatureDescriptorsFloat(ftype, data))
    index.write(out_path)
    print(f"{index.num_visual_words()} gorsel sozcuk, {time.time() - t0:.1f} sn -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
