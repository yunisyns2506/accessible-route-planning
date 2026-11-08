"""Derslik 4 krokisi: hafta 5 dense bulutundan metre ölçekli üstten görünüm + hafta 5 kamera yolu.

Çerçeve analiz_dense.py ile aynı: kamera pozlarından yukarı yön ve uzun eksen, zemin düzlemi y = 0,
eksenler duvarlara hizalı (en keskin x/y histogramı), birim metre (207,2 cm / COLMAP birimi).
Çıktı: kroki_taban.npz (katman ızgaraları + kamera yolu, rota çizimi için) ve kroki_taban.png.

Kullanım: python kroki_derslik4.py <seyrek_model> <fused.ply> <cikti_klasoru>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hafta05"))
sys.path.insert(0, r"C:\Users\sabod\tools\pycolmap-4.2.1")
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pycolmap  # noqa: E402
from analiz_dense import ply_oku, ransac_duzlem, voksel_sec  # noqa: E402

CM = 207.2
RNG = np.random.default_rng(1)
H = 0.05  # m, ızgara hücresi


def main(model, ply, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    r = pycolmap.Reconstruction(str(model))
    ims = sorted([im for im in r.images.values() if im.has_pose], key=lambda i: i.name)
    C = np.array([im.projection_center() for im in ims]) * CM / 100
    up = -np.mean([im.cam_from_world().rotation.matrix()[1] for im in ims], axis=0); up /= np.linalg.norm(up)
    Ch = C - np.outer(C @ up, up)
    V = np.linalg.svd(Ch - Ch.mean(0), full_matrices=False)[2]
    ex = V[0] - (V[0] @ up) * up; ex /= np.linalg.norm(ex); ey = np.cross(up, ex)
    o = C.mean(0); R = np.stack([ex, ey, up]); Cx = (C - o) @ R.T
    bak = np.array([im.cam_from_world().rotation.matrix()[2] for im in ims]) @ R.T   # kamera bakış yönü

    v = ply_oku(Path(ply))
    P = np.c_[v["x"], v["y"], v["z"]].astype(np.float64) * CM / 100
    sec = voksel_sec(P, 0.03)
    X = (P[sec] - o) @ R.T
    renk = np.c_[v["red"], v["green"], v["blue"]][sec]
    del P, v
    zh = X[:, 2]; kz = np.median(Cx[:, 2])
    # zemin: kameraların altındaki en alt belirgin katman (en yoğun katman oturak üstleri olabiliyor)
    h, k = np.histogram(zh[zh < kz], 300)
    tepe = [i for i in range(1, len(h) - 1) if h[i] >= h[i - 1] and h[i] >= h[i + 1] and h[i] >= 0.25 * h.max()]
    z0 = k[min(tepe)]
    s = np.abs(zh - z0) < 0.05
    alt = X[s][RNG.choice(s.sum(), min(s.sum(), 200_000), replace=False)]
    n_z, m_z, _ = ransac_duzlem(alt, 0.01, kosul=lambda n: abs(n[2]) > np.cos(np.radians(10)))
    if n_z[2] < 0:
        n_z = -n_z
    yuk = (X - m_z) @ n_z
    B = X[(yuk > 1.0) & (yuk < 3.0)][:, :2]
    B = B[RNG.choice(len(B), min(len(B), 300_000), replace=False)]

    def keskinlik(th):
        c, s_ = np.cos(th), np.sin(th)
        U = B @ np.array([[c, -s_], [s_, c]])
        return sum((np.histogram(U[:, j], bins=np.arange(-15, 15, 0.02))[0].astype(float) ** 2).sum() for j in (0, 1))
    acilar = np.radians(np.arange(-10, 10.01, 0.05))
    th = float(acilar[np.argmax([keskinlik(a) for a in acilar])])
    c, s_ = np.cos(th), np.sin(th); Rz = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
    X = X @ Rz; Cx = Cx @ Rz; bak = bak @ Rz
    Cyuk = (Cx - m_z @ Rz) @ (n_z @ Rz)
    # salon kutusu: 1–3 m bandında duvarlar
    duv = X[(yuk > 1.0) & (yuk < 3.0)]
    cl, ch = Cx[:, :2].min(0) - 2.5, Cx[:, :2].max(0) + 2.5          # pencereden görünen dış noktaları at
    duv = duv[(duv[:, 0] > cl[0]) & (duv[:, 0] < ch[0]) & (duv[:, 1] > cl[1]) & (duv[:, 1] < ch[1])]
    x0, x1 = np.percentile(duv[:, 0], [0.5, 99.5]); y0, y1 = np.percentile(duv[:, 1], [0.5, 99.5])
    pay = 1.0
    ext = (x0 - pay, x1 + pay, y0 - pay, y1 + pay)
    nx, ny = int((ext[1] - ext[0]) / H) + 1, int((ext[3] - ext[2]) / H) + 1

    def izgara(maske):
        Q = X[maske]
        ix = ((Q[:, 0] - ext[0]) / H).astype(int); iy = ((Q[:, 1] - ext[2]) / H).astype(int)
        ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
        g = np.zeros((ny, nx)); np.add.at(g, (iy[ok], ix[ok]), 1)
        return g
    katman = {"zemin": izgara(np.abs(yuk) < 0.05), "esya": izgara((yuk > 0.25) & (yuk < 1.1)),
              "duvar": izgara((yuk > 1.2) & (yuk < 2.6)), "kot": izgara((yuk > 0.3) & (yuk < 0.6))}
    # zemin rengi (üstten fotoğraf benzeri): en alçak 1,2 m'deki noktaların ortalama rengi
    m = yuk < 1.2
    Q = X[m]; ix = ((Q[:, 0] - ext[0]) / H).astype(int); iy = ((Q[:, 1] - ext[2]) / H).astype(int)
    ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
    rgb = np.zeros((ny, nx, 3)); say = np.zeros((ny, nx))
    np.add.at(rgb, (iy[ok], ix[ok]), renk[m][ok].astype(float)); np.add.at(say, (iy[ok], ix[ok]), 1)
    rgb = np.where(say[..., None] > 0, rgb / np.maximum(say, 1)[..., None] / 255, 1.0)
    np.savez_compressed(out / "kroki_taban.npz", ext=np.array(ext), kutu=np.array([x0, x1, y0, y1]), rgb=rgb,
                        kamera=Cx[:, :2], kamera_yuk=Cyuk, bak=bak, **katman)
    fig, ax = plt.subplots(1, 2, figsize=(22, 9))
    ax[0].imshow(rgb, origin="lower", extent=ext)
    ax[1].imshow(np.log1p(katman["duvar"]), origin="lower", extent=ext, cmap="Greys")
    ax[1].imshow(np.ma.masked_less(np.log1p(katman["esya"]), 0.5), origin="lower", extent=ext, cmap="Oranges", alpha=.6)
    for a in ax:
        a.plot(Cx[:, 0], Cx[:, 1], "-", c="C0", lw=.8)
        a.plot(*Cx[0, :2], "go"); a.plot(*Cx[-1, :2], "rs")
        a.set_xticks(np.arange(np.floor(ext[0]), ext[1], 1)); a.set_yticks(np.arange(np.floor(ext[2]), ext[3], 1))
        a.grid(alpha=.3); a.set_aspect("equal")
    ax[0].set_title("üstten renk (zemin + eşya)"); ax[1].set_title("duvar (1,2–2,6 m) + eşya (0,25–1,1 m)")
    fig.suptitle(f"Derslik 4 · salon {x1 - x0:.2f} × {y1 - y0:.2f} m · hafta 5 kamera yolu (yeşil başlangıç, kırmızı son) · "
                 f"kamera yüksekliği medyan {np.median(Cyuk):.2f} m, %5–95 {np.percentile(Cyuk, 5):.2f}–{np.percentile(Cyuk, 95):.2f} m")
    fig.tight_layout(); fig.savefig(out / "kroki_taban.png", dpi=110)
    yuk_kam = np.degrees(np.arcsin(np.clip(-bak[:, 2], -1, 1)))
    print(f"salon {x1 - x0:.2f} x {y1 - y0:.2f} m; x {x0:.2f}..{x1:.2f}, y {y0:.2f}..{y1:.2f}; "
          f"kamera yük. medyan {np.median(Cyuk):.2f} (%5-95 {np.percentile(Cyuk, 5):.2f}-{np.percentile(Cyuk, 95):.2f}); "
          f"aşağı bakış açısı medyan {np.median(yuk_kam):.1f}° (%5-95 {np.percentile(yuk_kam, 5):.1f}..{np.percentile(yuk_kam, 95):.1f})")


if __name__ == "__main__":
    main(*sys.argv[1:4])
