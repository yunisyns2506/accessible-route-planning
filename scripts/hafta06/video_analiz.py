"""Videonun kare kare incelenmesi: keskinlik, hareket hızı ve parlaklık.

Eğitimden önce çekimin hangi bölümlerinin kullanılabilir olduğunu görmek için
her kare küçültülerek okunur (ffmpeg -> ham gri piksel) ve şu ölçütler çıkarılır:

* keskinlik : Laplace varyansı (960x540 gri); düşük = bulanık
* hareket   : ardışık iki kare arasındaki medyan optik akış, 4K genişliğinde piksel/kare
* parlaklık : ortalama gri düzey (pozlama sıçramaları için)

Kullanım: python video_analiz.py <video> <cikti_klasoru> [kaynak_genislik]
"""
import csv
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

FFMPEG = "ffmpeg"
W, H = 960, 540          # keskinlik çözünürlüğü
FW, FH = 320, 180        # optik akış çözünürlüğü
SRC_W = int(sys.argv[3]) if len(sys.argv) > 3 else 3840  # kaynak video genişliği (hareket bu ölçekte)


def main(video: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    cmd = [FFMPEG, "-v", "error", "-threads", "0", "-i", str(video),
           "-vf", f"scale={W}:{H}:flags=area,format=gray", "-f", "rawvideo", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 8)
    sharp, motion, bright = [], [], []
    prev = None
    t0 = time.time()
    n = 0
    while True:
        buf = proc.stdout.read(W * H)
        if len(buf) < W * H:
            break
        g = np.frombuffer(buf, np.uint8).reshape(H, W)
        sharp.append(cv2.Laplacian(g, cv2.CV_32F).var())
        bright.append(float(g.mean()))
        small = cv2.resize(g, (FW, FH), interpolation=cv2.INTER_AREA)
        if prev is None:
            motion.append(0.0)
        else:
            flow = cv2.calcOpticalFlowFarneback(prev, small, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            mag = np.linalg.norm(flow, axis=2)
            motion.append(float(np.median(mag)) * SRC_W / FW)
        prev = small
        n += 1
        if n % 1000 == 0:
            print(f"{n} kare, {time.time() - t0:.0f} sn", flush=True)
    proc.wait()

    sharp, motion, bright = map(np.asarray, (sharp, motion, bright))
    np.savez(out / "video_olcutleri.npz", sharp=sharp, motion=motion, bright=bright)
    with open(out / "video_olcutleri.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["frame", "sharpness", "motion_px", "brightness"])
        for i in range(n):
            w.writerow([i, f"{sharp[i]:.1f}", f"{motion[i]:.2f}", f"{bright[i]:.1f}"])
    print(f"bitti: {n} kare, {time.time() - t0:.0f} sn")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
