"""Adım 1: kamera konumlarının hatalı olabileceği bölgeler.

Her kamera için dört gösterge hesaplanır:
  * yeniden izdüşüm hatası: kameranın gördüğü 3B noktaların bu kareye izdüşümünün
    gözlenen 2B noktaya ortalama uzaklığı (piksel)
  * gözlem sayısı: kareden 3B noktaya bağlanan nokta sayısı (az olursa poz zayıf dayanaklı)
  * yörünge sıçraması: çekim sırasında bir önceki ve sonraki kameraya uzaklığın, tipik
    adımın (medyan) kaç katı olduğu (video kesintisiz olduğundan ani sıçrama poz hatasıdır)
  * iki yöntem farkı: aynı karenin incremental ve hierarchical modellerdeki konumu, iki model
    benzerlik dönüşümüyle (Umeyama) hizalandıktan sonra; salon uzunluğunun yüzdesi olarak
Bir kamera, göstergelerden biri eşiği aşarsa "şüpheli" sayılır. Eşikler modelin kendi
dağılımına göredir: izdüşüm hatası medyanın 2 katından büyük, gözlem sayısı medyanın 1/4'ünden
az, sıçrama tipik adımın 3 katından büyük, yöntem farkı salon uzunluğunun %1'inden büyük. Ölçek henüz yok; uzunluklar
kamera yolunun uzun kenarına (salon uzunluğu vekili) oranlanır.

Kullanım: python analiz_kamera.py <incremental_model> <hierarchical_model> <cikti_klasoru>
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\sabod\tools\pycolmap-4.2.1")
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pycolmap  # noqa: E402

ESIK = {"reproj_kat": 2.0, "gozlem_oran": 0.25, "sicrama_kat": 3.0, "yontem_farki_yuzde": 1.0}


def kamera_olcutleri(r):
    rows = {}
    for im in r.images.values():
        if not im.has_pose:
            continue
        cam = r.cameras[im.camera_id]
        T = im.cam_from_world().matrix()
        uv, xyz = [], []
        for p in im.points2D:
            if p.has_point3D():
                uv.append(p.xy); xyz.append(r.points3D[p.point3D_id].xyz)
        uv, xyz = np.array(uv), np.array(xyz)
        pc = xyz @ T[:, :3].T + T[:, 3]
        proj = np.array([cam.img_from_cam(q) for q in pc])
        err = np.linalg.norm(proj - uv, axis=1)
        rows[im.name] = {"merkez": im.projection_center(), "reproj_px": float(np.mean(err)),
                         "gozlem": len(uv), "R": T[:, :3]}
    return rows


def umeyama(a, b):
    """b ≈ s R a + t (a, b: Nx3)."""
    ma, mb = a.mean(0), b.mean(0)
    A, B = a - ma, b - mb
    U, S, Vt = np.linalg.svd(B.T @ A / len(a))
    D = np.eye(3); D[2, 2] = np.sign(np.linalg.det(U @ Vt))
    R = U @ D @ Vt
    s = np.trace(np.diag(S) @ D) / A.var(0).sum()
    return s, R, mb - s * R @ ma


def main(inc_dir, hier_dir, out):
    out.mkdir(parents=True, exist_ok=True)
    inc = kamera_olcutleri(pycolmap.Reconstruction(str(inc_dir)))
    hier = kamera_olcutleri(pycolmap.Reconstruction(str(hier_dir)))
    adlar = sorted(inc)
    C = np.array([inc[n]["merkez"] for n in adlar])
    # yatay düzlem: kamera yolunun ilk iki ana bileşeni
    m = C.mean(0); _, _, V = np.linalg.svd(C - m); P = (C - m) @ V[:2].T
    uzunluk = np.ptp(P, axis=0).max()
    # yörünge sıçraması
    adim = np.linalg.norm(np.diff(C, axis=0), axis=1)
    med = np.median(adim)
    sicrama = np.zeros(len(C))
    sicrama[1:] = np.maximum(sicrama[1:], adim / med)
    sicrama[:-1] = np.maximum(sicrama[:-1], adim / med)
    # iki yöntem farkı
    ortak = [n for n in adlar if n in hier]
    a = np.array([hier[n]["merkez"] for n in ortak]); b = np.array([inc[n]["merkez"] for n in ortak])
    s, R, t = umeyama(a, b)
    fark = dict(zip(ortak, np.linalg.norm((s * a @ R.T + t) - b, axis=1) / uzunluk * 100))
    rp_med = np.median([inc[n]["reproj_px"] for n in adlar])
    go_med = np.median([inc[n]["gozlem"] for n in adlar])
    satirlar = []
    for i, n in enumerate(adlar):
        d = inc[n]
        f = fark.get(n, np.nan)
        neden = [k for k, kosul in (("reproj", d["reproj_px"] > ESIK["reproj_kat"] * rp_med),
                                    ("az_gozlem", d["gozlem"] < ESIK["gozlem_oran"] * go_med),
                                    ("sicrama", sicrama[i] > ESIK["sicrama_kat"]),
                                    ("yontem_farki", (f > ESIK["yontem_farki_yuzde"]) or np.isnan(f))) if kosul]
        satirlar.append({"kare": n, "x": P[i, 0], "y": P[i, 1], "reproj_px": d["reproj_px"],
                         "gozlem": d["gozlem"], "sicrama_kat": sicrama[i], "yontem_farki_yuzde": f,
                         "supheli": "+".join(neden)})
    with open(out / "kamera_guvenilirlik.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(satirlar[0])); w.writeheader(); w.writerows(satirlar)

    # özet
    sup = [r for r in satirlar if r["supheli"]]
    rp = np.array([r["reproj_px"] for r in satirlar]); go = np.array([r["gozlem"] for r in satirlar])
    fk = np.array([r["yontem_farki_yuzde"] for r in satirlar])
    ozet = [f"kamera: {len(satirlar)}, şüpheli: {len(sup)}",
            f"yeniden izdüşüm hatası (px): medyan {np.median(rp):.2f}, %95 {np.percentile(rp, 95):.2f}, en yüksek {rp.max():.2f}",
            f"gözlem sayısı: medyan {np.median(go):.0f}, en düşük {go.min()}",
            f"yörünge sıçraması: en yüksek {sicrama.max():.1f} kat (medyan adım = 1)",
            f"inc-hier konum farkı (salon uzunluğunun %'si): medyan {np.nanmedian(fk):.2f}, %95 {np.nanpercentile(fk, 95):.2f}, en yüksek {np.nanmax(fk):.2f}",
            "nedenlere göre: " + ", ".join(f"{k} {sum(k in r['supheli'] for r in sup)}" for k in ("reproj", "az_gozlem", "sicrama", "yontem_farki"))]
    (out / "kamera_ozet.txt").write_text("\n".join(ozet), encoding="utf-8")
    print("\n".join(ozet))

    # harita: üstten görünüş, dört panel
    pts = np.array([p.xyz for p in pycolmap.Reconstruction(str(inc_dir)).points3D.values()])
    Q = (pts - m) @ V[:2].T
    lim = np.percentile(Q, [1, 99], axis=0)
    fig, axs = plt.subplots(2, 2, figsize=(14, 11))
    paneller = [("Yeniden izdüşüm hatası (px)", rp, "viridis"), ("Gözlem sayısı", go, "viridis_r"),
                ("Yörünge sıçraması (medyan adımın katı)", sicrama, "magma"),
                ("Incremental–hierarchical konum farkı (salon uzunluğunun %'si)", fk, "magma")]
    for ax, (bas, v, cm) in zip(axs.flat, paneller):
        ax.scatter(Q[:, 0], Q[:, 1], s=0.05, c="0.75")
        sc = ax.scatter(P[:, 0], P[:, 1], c=v, s=10, cmap=cm)
        for r in sup:
            ax.scatter(r["x"], r["y"], s=70, facecolors="none", edgecolors="red", linewidths=1.2)
        ax.set_xlim(lim[:, 0]); ax.set_ylim(lim[:, 1]); ax.set_aspect("equal"); ax.set_title(bas)
        ax.set_xticks([]); ax.set_yticks([]); fig.colorbar(sc, ax=ax, shrink=0.75)
    fig.suptitle(f"LoMa + sequential + döngü + incremental: kamera güvenilirliği (kırmızı halka: şüpheli, {len(sup)}/{len(satirlar)})")
    fig.tight_layout(); fig.savefig(out / "kamera_guvenilirlik.png", dpi=110)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
