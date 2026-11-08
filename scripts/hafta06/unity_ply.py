"""3DGS .ply'yi Unity'ye hazırlar: metre ölçeği, zemin yatay (Y yukarı), sol el koordinatı.

Zincir: nerfstudio dışa aktarımı p_dp = s * (T p_colmap + t) çerçevesindedir (dataparser_transforms.json).
transforms.json'daki applied_transform dışa aktarımda görünmez; seyrek COLMAP noktalarının Gaussian'lara
en yakın komşu uzaklığıyla doğrulandı (medyan ~5 cm; A eklenince ~1 m). Hedef çerçeve:
  * zemin düzlemi (sınıf zemini, RANSAC) y = 0, normali +Y,
  * X ve Z salonun duvarlarına paralel (zemin noktalarının en küçük alanlı dikdörtgeni),
  * orijin zemin dikdörtgeninin ortası,
  * birim metre (ölçek kalibrasyonu: 3 ölçünün en küçük kareler uydurması),
  * Unity'nin sol el sistemi için Z ekseni ters çevrilir.
Her Gaussian için konum, ölçek (log + ln k), yönelim (kuaterniyon, yansıma bir yerel eksenle
dengelenir) ve küresel harmonikler (1.-3. bant, yansıma dahil ortogonal dönüşüm) dönüştürülür.
Seyrek noktaların %1-%99 kutusunun 1 m dışındaki Gaussian'lar (uçuşan parçalar) atılır.

Kullanım: python unity_ply.py <splat.ply> <dataparser_transforms.json>
                              <colmap_model> <olcek_cm_birim> <cikti.ply>
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\sabod\tools\pycolmap-4.2.1")
import numpy as np  # noqa: E402
import pycolmap  # noqa: E402
from plyfile import PlyData, PlyElement  # noqa: E402
from scipy.spatial.transform import Rotation  # noqa: E402

PAY = 1.0  # m, salon kutusu dışında tutulan pay


def sh_taban(d):
    """3DGS'in eval_sh tabanı, 1.-3. bant (N x 15)."""
    x, y, z = d.T
    xx, yy, zz = x * x, y * y, z * z
    C1 = 0.4886025119029199
    C2 = [1.0925484305920792, -1.0925484305920792, 0.31539156525252005, -1.0925484305920792, 0.5462742152960396]
    C3 = [-0.5900435899266435, 2.890611442640554, -0.4570457994644658, 0.3731763325901154,
          -0.4570457994644658, 1.445305721320277, -0.5900435899266435]
    return np.stack([-C1 * y, C1 * z, -C1 * x,
                     C2[0] * x * y, C2[1] * y * z, C2[2] * (2 * zz - xx - yy), C2[3] * x * z, C2[4] * (xx - yy),
                     C3[0] * y * (3 * xx - yy), C3[1] * x * y * z, C3[2] * y * (4 * zz - xx - yy),
                     C3[3] * z * (2 * zz - 3 * xx - 3 * yy), C3[4] * x * (4 * zz - xx - yy),
                     C3[5] * z * (xx - yy), C3[6] * x * (xx - 3 * yy)], 1)


def sh_matrisi(Q):
    """Yön fonksiyonu f(d) -> f(Q^T d) için bant bazında katsayı matrisi (15x15)."""
    d = np.random.default_rng(0).normal(size=(4000, 3)); d /= np.linalg.norm(d, axis=1, keepdims=True)
    Y, Yq = sh_taban(d), sh_taban(d @ Q)
    M = np.zeros((15, 15))
    for a, b in ((0, 3), (3, 8), (8, 15)):
        M[a:b, a:b] = np.linalg.lstsq(Y[:, a:b], Yq[:, a:b], rcond=None)[0]
    return M


def hedef_cerceve(model, k):
    """COLMAP -> Unity (metre): p_u = k * M (p - o). Zemin, yön ve salon kutusu da döner."""
    r = pycolmap.Reconstruction(str(model))
    ims = [im for im in r.images.values() if im.has_pose]
    C = np.array([im.projection_center() for im in ims])
    # hafta 6: oda dışına düşen bozuk kameralar ve noktalar çerçeveyi kaydırmasın
    rc = np.linalg.norm(C - np.median(C, 0), axis=1); iyi = rc < 10 * np.median(rc)
    C = C[iyi]; ims = [im for im, t in zip(ims, iyi) if t]
    up = -np.mean([im.cam_from_world().rotation.matrix()[1] for im in ims], axis=0); up /= np.linalg.norm(up)
    P = np.array([p.xyz for p in r.points3D.values() if p.error < 2 and p.track.length() >= 3])
    P = P[np.linalg.norm(P - np.median(C, 0), axis=1) < 3 * rc[iyi].max()]
    z = (P - C.mean(0)) @ up
    # zemin: kameraların altındaki en alt belirgin katman (en yoğun katman oturak üstü olabiliyor)
    zk = np.median((C - C.mean(0)) @ up)
    hh, kk = np.histogram(z, bins=np.arange(zk - 1.5, zk, 0.02))
    hh = np.convolve(hh, np.ones(3) / 3, mode="same")
    tepe = [i for i in range(1, len(hh) - 1) if hh[i] >= hh[i - 1] and hh[i] >= hh[i + 1] and hh[i] >= 0.25 * hh.max()]
    taban = kk[min(tepe)] if tepe else kk[np.argmax(hh)]
    aday = P[np.abs(z - taban) < 0.06]
    rng = np.random.default_rng(0); en = None
    for _ in range(2000):
        a, b, c = aday[rng.choice(len(aday), 3, replace=False)]
        n = np.cross(b - a, c - a)
        if np.linalg.norm(n) < 1e-12:
            continue
        n /= np.linalg.norm(n)
        if abs(n @ up) < 0.97:
            continue
        say = (np.abs((aday - a) @ n) < 0.01).sum()
        if en is None or say > en[0]:
            en = (say, n, a)
    ic = aday[np.abs((aday - en[2]) @ en[1]) < 0.01]
    m = ic.mean(0); n = np.linalg.svd(ic - m)[2][2]; n *= np.sign(n @ up)
    e1 = np.cross(n, [1, 0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(n, e1)
    H = np.c_[(ic - m) @ e1, (ic - m) @ e2]
    en = None
    for a in np.radians(np.arange(0, 90, 0.25)):
        R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]]); Yp = H @ R
        lo, hi = np.percentile(Yp, [0.5, 99.5], axis=0)
        if en is None or np.prod(hi - lo) < en[0]:
            en = (np.prod(hi - lo), a, lo, hi)
    _, a, lo, hi = en
    ex = np.cos(a) * e1 + np.sin(a) * e2; ez_sag = np.cross(ex, n)      # sağ el: x, y=n, z = x × y
    if hi[0] - lo[0] < hi[1] - lo[1]:                                     # X uzun kenar boyunca
        ex, ez_sag = ez_sag, -ex
        lo, hi = lo[::-1], hi[::-1]
    Rsag = np.stack([ex, n, ez_sag])                                      # satırlar: hedef eksenler
    Hm = (ic - m) @ Rsag.T
    merkez = m + Rsag.T @ np.array([(Hm[:, 0].min() + Hm[:, 0].max()) / 2, 0, (Hm[:, 2].min() + Hm[:, 2].max()) / 2])
    Hp = (P - merkez) @ Rsag.T                                            # salon kutusu: zemin ve platform dahil tüm noktalar
    kutu = np.r_[np.percentile(Hp[:, [0, 2]], 1, axis=0), np.percentile(Hp[:, [0, 2]], 99, axis=0)] * k
    M = np.diag([1, 1, -1]) @ Rsag                                        # Unity: sol el, z ters
    tavan = np.percentile(((P - merkez) @ n), 99.5) * k
    return M, merkez, kutu, tavan


def main(ply, djson, model, olcek_cm, out):
    k = olcek_cm / 100.0
    dp = json.loads(Path(djson).read_text()); T = np.array(dp["transform"]); s = dp["scale"]
    M, o, kutu, tavan = hedef_cerceve(model, k)
    # p_u = k M (p_colmap - o), p_colmap = T3^T (p_dp / s - t)
    Q = M @ T[:, :3].T
    v = PlyData.read(str(ply))["vertex"]; ad = v.data.dtype.names
    X = np.c_[v["x"], v["y"], v["z"]].astype(np.float64)
    Xu = (k / s) * X @ Q.T - k * (M @ (T[:, :3].T @ T[:, 3] + o))
    tut = ((Xu[:, 0] > kutu[0] - PAY) & (Xu[:, 0] < kutu[2] + PAY) & (Xu[:, 2] > -kutu[3] - PAY) & (Xu[:, 2] < -kutu[1] + PAY)
           & (Xu[:, 1] > -PAY) & (Xu[:, 1] < tavan + PAY))
    d = v.data[tut].copy()
    d["x"], d["y"], d["z"] = Xu[tut].T.astype(np.float32)
    for i in range(3):
        d[f"scale_{i}"] = d[f"scale_{i}"] + np.float32(np.log(k / s))
    q = np.c_[d["rot_0"], d["rot_1"], d["rot_2"], d["rot_3"]].astype(np.float64)   # w, x, y, z
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    R = Rotation.from_quat(q[:, [1, 2, 3, 0]]).as_matrix()
    D = np.diag([1, 1, -1.0]) if np.linalg.det(Q) < 0 else np.eye(3)                # yansımayı yerel z ile dengele
    Rn = Q @ R @ D
    qn = Rotation.from_matrix(Rn).as_quat()[:, [3, 0, 1, 2]]
    for i in range(4):
        d[f"rot_{i}"] = qn[:, i].astype(np.float32)
    fr = sorted([a for a in ad if a.startswith("f_rest_")], key=lambda a: int(a[7:]))
    if len(fr) == 45:
        S = np.stack([d[a] for a in fr], 1).astype(np.float64).reshape(-1, 3, 15)
        S = S @ sh_matrisi(Q).T
        for j, a in enumerate(fr):
            d[a] = S.reshape(-1, 45)[:, j].astype(np.float32)
    PlyData([PlyElement.describe(d, "vertex")], byte_order="<").write(str(out))
    bilgi = {"gaussian_giris": int(len(X)), "gaussian_cikis": int(tut.sum()), "olcek_cm_birim": olcek_cm,
             "salon_kutusu_m": {"x": [kutu[0], kutu[2]], "z": [-kutu[3], -kutu[1]], "tavan_y": tavan},
             "Q": Q.tolist(), "det_Q": float(np.linalg.det(Q))}
    Path(out).with_suffix(".json").write_text(json.dumps(bilgi, indent=1), encoding="utf-8")
    print(json.dumps({k_: v_ for k_, v_ in bilgi.items() if k_ != "Q"}, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), float(sys.argv[4]), Path(sys.argv[5]))
