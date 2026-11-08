"""video_olcutleri.npz'den eğitim karelerini seçer.

Video N eşit pencereye bölünür; her pencereden hızlı dönüşe denk gelmeyen
(hareket < ESIK) en keskin kare alınır. Penceredeki tüm kareler hızlıysa en yavaş
olanı alınır. Her 10. seçilen kare test karesidir.

Kullanım: python kare_secimi.py <analiz_klasoru> <N>
Çıktı: secilen_kareler.csv (sira, frame, sharpness, motion, test)
"""
import csv
import sys
from pathlib import Path

import numpy as np

ESIK = 15.0  # 4K px/kare
TEST_ADIM = 10


def main(d: Path, n: int) -> None:
    z = np.load(d / "video_olcutleri.npz")
    sharp, motion = z["sharp"], z["motion"]
    edges = np.linspace(0, len(sharp), n + 1).astype(int)
    rows = []
    for k in range(n):
        a, b = edges[k], edges[k + 1]
        ok = np.where(motion[a:b] < ESIK)[0]
        j = a + (ok[np.argmax(sharp[a:b][ok])] if len(ok) else np.argmin(motion[a:b]))
        rows.append((k, int(j), float(sharp[j]), float(motion[j]), int(k % TEST_ADIM == TEST_ADIM - 1)))
    with open(d / f"secilen_kareler_{n}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sira", "frame", "sharpness", "motion_px", "test"])
        w.writerows(rows)
    s = np.array([r[2] for r in rows]) / np.median(sharp)
    m = np.array([r[3] for r in rows])
    print(f"{n} kare; test {sum(r[4] for r in rows)}; hareket>=esik {np.mean(m >= ESIK) * 100:.1f}%; "
          f"keskinlik<0.5 {np.mean(s < 0.5) * 100:.1f}%; ardışık aralık medyan "
          f"{np.median(np.diff([r[1] for r in rows])):.0f} kare")


if __name__ == "__main__":
    main(Path(sys.argv[1]), int(sys.argv[2]))
