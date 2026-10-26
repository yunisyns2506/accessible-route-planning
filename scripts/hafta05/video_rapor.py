"""video_analiz.py çıktısından grafik, bölüm özeti ve küçük resim paftası üretir.

Kullanım: python video_rapor.py <video> <analiz_klasoru>
"""
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FFMPEG = r"C:\Users\sabod\tools\ffmpeg\ffmpeg.exe"
FPS = 30000 / 1001


def rolling(x, k):
    pad = np.pad(x, (k // 2, k - 1 - k // 2), mode="edge")
    return np.convolve(pad, np.ones(k) / k, mode="valid")


def main(video: Path, d: Path) -> None:
    z = np.load(d / "video_olcutleri.npz")
    sharp, motion, bright = z["sharp"], z["motion"], z["bright"]
    t = np.arange(len(sharp)) / FPS
    # keskinlik göreli: 3 sn'lik kayan medyana oranla değil, tüm videonun dağılımına göre
    s_norm = sharp / np.median(sharp)
    m1 = rolling(motion, 15)

    fig, ax = plt.subplots(3, 1, figsize=(14, 8), sharex=True)
    ax[0].plot(t / 60, s_norm, lw=0.3, color="0.6")
    ax[0].plot(t / 60, rolling(s_norm, 31), lw=1, color="C0")
    ax[0].axhline(0.5, color="C3", ls="--", lw=0.8)
    ax[0].set_ylabel("Keskinlik\n(medyana oran)")
    ax[1].plot(t / 60, m1, lw=0.6, color="C1")
    ax[1].set_ylabel("Hareket\n(4K px/kare)")
    ax[2].plot(t / 60, bright, lw=0.6, color="C2")
    ax[2].set_ylabel("Parlaklık")
    ax[2].set_xlabel("Dakika")
    for a in ax:
        a.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(d / "video_olcutleri.png", dpi=110)

    # 10 sn'lik bölüm özeti
    seg = int(round(10 * FPS))
    rows = []
    for i in range(0, len(sharp), seg):
        sl = slice(i, i + seg)
        rows.append((i / FPS, np.median(s_norm[sl]), np.mean(s_norm[sl] < 0.5) * 100,
                     np.median(motion[sl]), np.percentile(motion[sl], 90)))
    with open(d / "bolum_ozeti.txt", "w", encoding="utf-8") as f:
        f.write("bas_sn  keskinlik_medyan  bulanik_%  hareket_medyan  hareket_p90\n")
        for r in rows:
            f.write(f"{r[0]:6.0f}  {r[1]:16.2f}  {r[2]:9.0f}  {r[3]:14.1f}  {r[4]:11.1f}\n")
        f.write(f"\nkare: {len(sharp)}  sure_sn: {len(sharp) / FPS:.0f}\n")
        f.write(f"bulanik kare (keskinlik < medyanin %50'si): {np.mean(s_norm < 0.5) * 100:.1f}%\n")
        f.write(f"hareket medyan {np.median(motion):.1f} px/kare, p90 {np.percentile(motion, 90):.1f}\n")

    # 10 sn'de bir küçük resim paftası
    thumbs = d / "pafta.jpg"
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(video),
                    "-vf", "fps=1/10,scale=384:216,tile=8x8", "-frames:v", "1",
                    "-q:v", "3", str(thumbs)], check=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
