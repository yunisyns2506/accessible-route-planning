"""Dense (yoğun) nokta bulutuyla duvar kayması, eksik geometri ve oda boyutları.

Seyrek modeldeki analizlerin (analiz_duvar.py, analiz_eksik.py) dense karşılığı. Seyrek bulutta
beyaz duvarlarda az nokta olduğu için duvar açıları kesin değildi; burada aynı ölçütler
stereo_fusion çıktısı (fused.ply + fused.ply.vis) üzerinde, metre ölçeğinde hesaplanır.

  * eksen çerçevesi: seyrek modelin kamera pozlarından (yukarı yön, salonun uzun ekseni)
  * seyreltme: VOKSEL_CM'lik vokselde tek nokta (ölçütler nokta yoğunluğundan bağımsız olsun)
  * duvarlar: kamera yolunun ötesindeki noktalara düşey RANSAC düzlemi; paralellik, diklik,
    düşeylik, düzlemden RMS sapma, duvar boyunca kayma (10 dilim medyanı), kapsam
  * zemin: düzlem, uzun/kısa eksende eğilme; tavan: yükseklik
  * oda boyutları: karşılıklı duvar düzlemleri arası uzaklık (en, boy), zemin–tavan (yükseklik)
  * eksik geometri: kat planı ızgarasında boş hücre oranı ve noktaları gören kamera sayısı
    (fused.ply.vis), katman katman; seyrek modeldeki sonuçla karşılaştırma

Kullanım: python analiz_dense.py <seyrek_model> <fused.ply> <cikti_klasoru> <cm_per_birim> <baslik>
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pycolmap  # noqa: E402

RNG = np.random.default_rng(1)
VOKSEL_CM = 1.0
HUCRE = 0.025      # kat planı hücresi: salon uzunluğunun oranı (seyrek analizle aynı)
PLY_TIP = {"float": "f4", "float32": "f4", "double": "f8", "uchar": "u1", "uint8": "u1",
           "int": "i4", "int32": "i4", "uint": "u4", "uint32": "u4", "short": "i2", "ushort": "u2"}


def ply_oku(yol: Path) -> np.ndarray:
    """İkili (little endian) PLY'nin vertex öğesini yapılandırılmış dizi olarak okur."""
    with open(yol, "rb") as f:
        alanlar, n, bas = [], 0, 0
        while True:
            satir = f.readline().decode("ascii").strip()
            if satir.startswith("element vertex"):
                n = int(satir.split()[-1])
            elif satir.startswith("property") and n and "list" not in satir:
                _, tip, ad = satir.split()
                alanlar.append((ad, "<" + PLY_TIP[tip]))
            elif satir == "end_header":
                bas = f.tell()
                break
    return np.fromfile(yol, dtype=np.dtype(alanlar), count=n, offset=bas)


def vis_oku(yol: Path, n: int) -> np.ndarray:
    """fused.ply.vis: her nokta için onu gören kamera sayısı."""
    a = np.fromfile(yol, dtype="<u4")
    assert int(a[0]) + (int(a[1]) << 32) == n, "vis dosyası nokta sayısıyla uyuşmuyor"
    say = np.empty(n, dtype=np.int32)
    i = 2
    for k in range(n):
        m = a[i]
        say[k] = m
        i += 1 + m
    return say


def voksel_sec(P: np.ndarray, boy: float) -> np.ndarray:
    """Her vokselden ilk noktanın indeksi."""
    anahtar = np.floor((P - P.min(0)) / boy).astype(np.int64)
    k = (anahtar[:, 0] << 42) | (anahtar[:, 1] << 21) | anahtar[:, 2]
    _, idx = np.unique(k, return_index=True)
    return np.sort(idx)


def ransac_duzlem(P, esik, n_iter=2000, kosul=None):
    en_iyi = None
    for _ in range(n_iter):
        a, b, c = P[RNG.choice(len(P), 3, replace=False)]
        n = np.cross(b - a, c - a)
        if np.linalg.norm(n) < 1e-12:
            continue
        n /= np.linalg.norm(n)
        if kosul is not None and not kosul(n):
            continue
        ic = np.abs((P - a) @ n) < esik
        if en_iyi is None or ic.sum() > en_iyi.sum():
            en_iyi = ic
    Q = P[en_iyi]; m = Q.mean(0)
    return np.linalg.svd(Q - m, full_matrices=False)[2][-1], m, en_iyi


def aci2(u, v):
    return float(np.degrees(np.arccos(np.clip(abs(u @ v), 0, 1))))


def main(model: Path, ply: Path, out: Path, cm_birim: float, baslik: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    r = pycolmap.Reconstruction(str(model))
    ims = sorted([im for im in r.images.values() if im.has_pose], key=lambda i: i.name)
    C = np.array([im.projection_center() for im in ims]) * cm_birim / 100      # metre
    up = -np.mean([im.cam_from_world().rotation.matrix()[1] for im in ims], axis=0); up /= np.linalg.norm(up)
    Ch = C - np.outer(C @ up, up)
    V = np.linalg.svd(Ch - Ch.mean(0), full_matrices=False)[2]
    ex = V[0] - (V[0] @ up) * up; ex /= np.linalg.norm(ex); ey = np.cross(up, ex)
    o = C.mean(0)
    R = np.stack([ex, ey, up])
    Cx = (C - o) @ R.T

    v = ply_oku(ply)
    n_ham = len(v)
    P = np.c_[v["x"], v["y"], v["z"]].astype(np.float64) * cm_birim / 100
    gor = vis_oku(Path(str(ply) + ".vis"), n_ham) if Path(str(ply) + ".vis").exists() else None
    sec = voksel_sec(P, VOKSEL_CM / 100)
    X = (P[sec] - o) @ R.T
    renk = np.c_[v["red"], v["green"], v["blue"]][sec] / 255.0
    gor = gor[sec] if gor is not None else None
    del P, v
    print(f"dense nokta {n_ham:,}, {VOKSEL_CM:g} cm voksel sonrası {len(X):,}", flush=True)

    # zemin ve tavan: kameraların altındaki / üstündeki en yoğun yatay katman
    zh = X[:, 2]; kz = np.median(Cx[:, 2])
    h, k = np.histogram(zh[zh < kz], 300); z0 = k[np.argmax(h)]
    s = np.abs(zh - z0) < 0.05
    yatay = lambda n: abs(n[2]) > np.cos(np.radians(10))  # noqa: E731
    alt = X[s][RNG.choice(s.sum(), min(s.sum(), 300_000), replace=False)]
    n_z, m_z, _ = ransac_duzlem(alt, 0.01, kosul=yatay)
    if n_z[2] < 0:
        n_z = -n_z
    yuk = (X - m_z) @ n_z
    # tavanda iki katman olabilir (asma aydınlatma ve tavan ızgarası): yükseklik histogramında
    # en yoğun katmanın %30'unu geçen en üst katman tavan sayılır, en yoğunu ayrıca raporlanır
    h, k = np.histogram(yuk[yuk > 1.5], 200)
    kc = 0.5 * (k[:-1] + k[1:])
    tepe = [i for i in range(1, len(h) - 1) if h[i] >= h[i - 1] and h[i] >= h[i + 1] and h[i] >= 0.3 * h.max()]
    tavan = float(kc[max(tepe)]); asma = float(kc[np.argmax(h)])
    zem = X[np.abs(yuk) < 0.02]

    # Eksenleri duvarlara hizala: kamera yolunun uzun ekseni salonla aynı yönde olmayabilir.
    # 1–3 m bandındaki noktaların x ve y histogramlarını en keskin yapan dönme açısı aranır.
    B = X[(yuk > 1.0) & (yuk < 3.0)][:, :2]
    B = B[RNG.choice(len(B), min(len(B), 400_000), replace=False)]
    def keskinlik(th):
        c, s_ = np.cos(th), np.sin(th)
        U = B @ np.array([[c, -s_], [s_, c]])
        return sum((np.histogram(U[:, j], bins=np.arange(-15, 15, 0.02))[0].astype(float) ** 2).sum() for j in (0, 1))
    acilar = np.radians(np.arange(-10, 10.01, 0.05))
    th = float(acilar[np.argmax([keskinlik(a_) for a_ in acilar])])
    c, s_ = np.cos(th), np.sin(th); Rz = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
    X = X @ Rz; Cx = Cx @ Rz; zem = zem @ Rz; m_z = m_z @ Rz; n_z = n_z @ Rz
    print(f"eksen hizalama: {np.degrees(th):.2f}°", flush=True)

    x0, x1 = np.percentile(Cx[:, 0], [0.5, 99.5]); y0, y1 = np.percentile(Cx[:, 1], [0.5, 99.5])
    L = x1 - x0
    govde = (yuk > 0.15) & (yuk < tavan - 0.25)        # zemin, sıra/oturak üstleri ve tavan dışı
    bant = (yuk > 1.0) & (yuk < 3.0)                   # duvar düzlemi: sıra, radyatör ve lambaların arası
    pay = 0.20                                         # kamera yolu duvara ~0,5 m yaklaşıyor; duvar bu payın ötesinde
    # Her duvar, kamera yolunun sınırından dışarı doğru (pay .. 2 m) ve 1–3 m yükseklik bandında
    # aranır. Duvar boyunca 25 cm'lik her dilimde en yoğun derinlik (1 cm histogram tepesi) o dilimin
    # duvar yüzüdür; bu yüz noktalarına 3 cm toleranslı RANSAC ile doğru oturtulur. Böylece düzlem,
    # en çok noktalı küçük bir yüzeye (radyatör, pano, pencere kenarı) değil, duvarın boyuna oturur.
    yonler = {"sol kısa duvar": (0, -1), "sağ kısa duvar": (0, 1), "alt uzun duvar": (1, -1), "üst uzun duvar": (1, 1)}
    esik = 0.03
    duvar = {}
    for ad, (eks, isaret) in yonler.items():
        a = 1 - eks
        sinir = ((x0, x1) if eks == 0 else (y0, y1))[isaret > 0]
        boyun = (y0, y1) if eks == 0 else (x0, x1)
        dis = isaret * (X[:, eks] - sinir)
        s_ = bant & (dis > pay) & (dis < 2.0) & (X[:, a] > boyun[0]) & (X[:, a] < boyun[1])
        Q = X[s_]; t = Q[:, a]; dq = Q[:, eks]
        be = np.arange(boyun[0], boyun[1] + 0.25, 0.25)
        yuz = []
        for i in range(len(be) - 1):
            w = (t >= be[i]) & (t < be[i + 1])
            if w.sum() < 30:
                continue
            hh, kk = np.histogram(dq[w], bins=np.arange(dq[w].min(), dq[w].max() + 0.02, 0.01))
            if not len(hh):
                continue
            # duvar yüzü: dilimin en dışındaki yoğun katman (tepe yüksekliğinin %30'unu geçen en dış
            # 1 cm'lik kutu); duvar önündeki eşya ve iç yüzeyler daha içeride kalır
            dolu_k = np.where(hh >= 0.3 * hh.max())[0]
            j = dolu_k.max() if isaret > 0 else dolu_k.min()
            u = dq[w][np.abs(dq[w] - (kk[j] + 0.005)) < 0.02]
            yuz.append((0.5 * (be[i] + be[i + 1]), float(np.median(u))))
        F = np.array(yuz)
        en_iyi = None
        for _ in range(3000):
            i, j = RNG.choice(len(F), 2, replace=False)
            if abs(F[j, 0] - F[i, 0]) < 1.0:
                continue
            eg = (F[j, 1] - F[i, 1]) / (F[j, 0] - F[i, 0])
            if abs(eg) > np.tan(np.radians(10)):
                continue
            ic = np.abs(F[:, 1] - (F[i, 1] + eg * (F[:, 0] - F[i, 0]))) < esik
            if en_iyi is None or ic.sum() > en_iyi.sum():
                en_iyi = ic
        eg, c = np.polyfit(F[en_iyi, 0], F[en_iyi, 1], 1)
        S = Q[np.abs(dq - (c + eg * t)) < esik]
        m = S.mean(0)
        n3 = np.linalg.svd(S[RNG.choice(len(S), min(len(S), 200_000), replace=False)] - m, full_matrices=False)[2][-1]
        n = np.zeros(3); n[eks] = 1.0; n[a] = -eg; n /= np.linalg.norm(n)          # kat planında duvar normali
        ts = S[:, a]
        art = F[en_iyi, 1] - (c + eg * F[en_iyi, 0])                               # dilim yüzünün doğrudan sapması
        dil = np.linspace(F[en_iyi, 0].min(), F[en_iyi, 0].max(), 11)
        prof = np.array([(0.5 * (dil[i] + dil[i + 1]), np.median(art[(F[en_iyi, 0] >= dil[i]) & (F[en_iyi, 0] <= dil[i + 1])]))
                         for i in range(10) if ((F[en_iyi, 0] >= dil[i]) & (F[en_iyi, 0] <= dil[i + 1])).sum() >= 2])
        g = 0.10
        dolu, _, _ = np.histogram2d(ts, (S - m_z) @ n_z, [np.arange(boyun[0], boyun[1] + g, g), np.arange(1.0, 3.0 + g, g)])
        duvar[ad] = {"n": n, "m": np.r_[m[:2], m[2]], "S": S, "profil": prof, "nokta": int(len(S)), "aday": int(len(Q)),
                     "cizgi": (eks, a, eg, c), "uzunluk_m": float(boyun[1] - boyun[0]),
                     "boy_kapsam_yuzde": float(en_iyi.sum() / (len(be) - 1) * 100),
                     "yuzey_kapsam_yuzde": float((dolu > 0).mean() * 100),
                     "rms_cm": float(np.sqrt(np.mean(art ** 2)) * 100),
                     "kayma_cm": float(np.ptp(prof[:, 1]) * 100) if len(prof) > 2 else float("nan"),
                     "duseylik_sapma_derece": float(np.degrees(np.arcsin(min(1, abs(n3 @ n_z)))))}
    d = duvar
    dik = {f"{a} – {b}": float(abs(90 - aci2(d[a]["n"], d[b]["n"])))
           for a in ("sol kısa duvar", "sağ kısa duvar") for b in ("alt uzun duvar", "üst uzun duvar")}
    dz = (zem - m_z) @ n_z
    egilme = {}
    for eks, ad in ((0, "uzun"), (1, "kısa")):
        t = zem[:, eks]; dil = np.linspace(np.percentile(t, 2), np.percentile(t, 98), 11)
        pr = [np.median(dz[(t >= dil[i]) & (t < dil[i + 1])]) for i in range(10) if ((t >= dil[i]) & (t < dil[i + 1])).sum() > 50]
        egilme[ad] = float(np.ptp(pr) * 100)
    def cizgi_deger(w, tt):
        _, _, eg, c = w["cizgi"]; return c + eg * tt
    ym, xm = 0.5 * (y0 + y1), 0.5 * (x0 + x1)
    boy = cizgi_deger(d["sağ kısa duvar"], ym) - cizgi_deger(d["sol kısa duvar"], ym)
    en = cizgi_deger(d["üst uzun duvar"], xm) - cizgi_deger(d["alt uzun duvar"], xm)

    # eksik geometri: kat planı ızgarası, katman katman
    yH = tavan
    katman = {"zemin ve oturaklar": yuk < 0.14 * yH,
              # orta katman asma aydınlatmanın altında kesilir; lambalar salon içi hücreleri doldurup
              # duvar katmanının kapsamını olduğundan iyi göstermesin
              "orta (duvarlar, kapı, pencere)": (yuk >= 0.14 * yH) & (yuk < min(0.92 * yH, asma - 0.3)),
              "tavan": yuk >= 0.92 * yH}
    cpay = 0.08 * L; hs = HUCRE * L
    xe = np.arange(x0 - cpay, x1 + cpay + hs, hs); ye = np.arange(y0 - cpay, y1 + cpay + hs, hs)
    xc = 0.5 * (xe[:-1] + xe[1:]); yc = 0.5 * (ye[:-1] + ye[1:])
    salon = (xc[:, None] > x0) & (xc[:, None] < x1) & (yc[None, :] > y0) & (yc[None, :] < y1)
    eksik = {}
    fig, axs = plt.subplots(2, 3, figsize=(21, 11))
    for j, (ad, ms) in enumerate(katman.items()):
        yog, _, _ = np.histogram2d(X[ms, 0], X[ms, 1], [xe, ye])
        if gor is not None:
            top, _, _ = np.histogram2d(X[ms, 0], X[ms, 1], [xe, ye], weights=gor[ms])
            gm = np.where(yog > 0, top / np.maximum(yog, 1), np.nan)       # hücrede ortalama görüş
        else:
            gm = np.full_like(yog, np.nan)
        eksik[ad] = {"nokta_voksel": int(ms.sum()),
                     "salon_ici_bos_hucre_yuzde": round(float((yog[salon] == 0).mean() * 100), 1),
                     "salon_ici_az_gorus_hucre_yuzde (ort. <5 kamera)": round(float((gm[salon & (yog > 0)] < 5).mean() * 100), 1),
                     "medyan_gorus": round(float(np.nanmedian(gm)), 1)}
        ext = [xe[0], xe[-1], ye[0], ye[-1]]
        a1 = axs[0, j].imshow(np.log10(yog.T + 1), origin="lower", extent=ext, cmap="magma")
        axs[0, j].plot(Cx[:, 0], Cx[:, 1], c="c", lw=0.3); axs[0, j].set_title(f"{ad}: nokta yoğunluğu (log10)")
        fig.colorbar(a1, ax=axs[0, j], shrink=0.7)
        a2 = axs[1, j].imshow(gm.T, origin="lower", extent=ext, cmap="viridis", vmax=np.nanpercentile(gm, 95))
        axs[1, j].plot(Cx[:, 0], Cx[:, 1], c="w", lw=0.3); axs[1, j].set_title(f"{ad}: noktaları gören ort. kamera sayısı")
        fig.colorbar(a2, ax=axs[1, j], shrink=0.7)
        for ax in (axs[0, j], axs[1, j]):
            ax.set_xlabel("m"); ax.set_aspect("equal")
    fig.suptitle(f"{baslik}: dense kat planı kapsamı (hücre {hs * 100:.0f} cm; siyah = nokta yok)")
    fig.tight_layout(); fig.savefig(out / "dense_eksik_geometri.png", dpi=100); plt.close(fig)

    sonuc = {
        "dense_nokta": n_ham, "voksel_cm": VOKSEL_CM, "analiz_noktasi": int(len(X)), "cm_per_birim": cm_birim,
        "eksen_hizalama_derece": round(float(np.degrees(th)), 2),
        "oda_m": {"boy (kısa duvarlar arası)": round(float(boy), 3), "en (uzun duvarlar arası)": round(float(en), 3),
                  "yukseklik (zemin–tavan)": round(tavan, 3), "asma katman (en yoğun)": round(asma, 3)},
        "paralellik_uzun_duvarlar_derece": round(aci2(d["alt uzun duvar"]["n"], d["üst uzun duvar"]["n"]), 2),
        "paralellik_kisa_duvarlar_derece": round(aci2(d["sol kısa duvar"]["n"], d["sağ kısa duvar"]["n"]), 2),
        "diklik_sapmasi_derece": {k: round(x, 2) for k, x in dik.items()},
        "duvarlar": {k: {"nokta": w["nokta"], "aday": w["aday"], "incelenen_uzunluk_m": round(w["uzunluk_m"], 2),
                         "boy_kapsam_yuzde": round(w["boy_kapsam_yuzde"], 1), "yuzey_kapsam_yuzde": round(w["yuzey_kapsam_yuzde"], 1), "rms_cm": round(w["rms_cm"], 2),
                         "kayma_cm": round(w["kayma_cm"], 2), "duseylik_sapma_derece": round(w["duseylik_sapma_derece"], 2)}
                     for k, w in d.items()},
        "zemin_egilme_cm": {k: round(x, 2) for k, x in egilme.items()},
        "zemin_rms_cm": round(float(np.sqrt(np.mean(dz ** 2)) * 100), 2),
        "eksik_geometri": eksik,
    }
    (out / "dense_sonuc.json").write_text(json.dumps(sonuc, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(sonuc, indent=1, ensure_ascii=False), flush=True)

    # şekil: kat planı (renkli üstten görünüş) + duvar düzlemleri, duvar boyunca sapma
    fig = plt.figure(figsize=(17, 7.5))
    ax = fig.add_subplot(1, 2, 1)
    g = yuk < 2.5                                      # asma aydınlatma ve tavan ızgarası hariç
    i = np.where(g)[0]; i = i[np.argsort(X[i, 2])]
    i = i[RNG.choice(len(i), min(len(i), 1_500_000), replace=False)]; i = i[np.argsort(X[i, 2])]
    ax.scatter(X[i, 0], X[i, 1], s=0.03, c=renk[i], rasterized=True)
    ax.plot(Cx[:, 0], Cx[:, 1], c="k", lw=0.4, alpha=0.5)
    rk = dict(zip(d, ("C0", "C1", "C2", "C3")))
    for a, w in d.items():
        eks, al, eg, c = w["cizgi"]
        tt = np.array([w["S"][:, al].min(), w["S"][:, al].max()])
        u = np.zeros((2, 2)); u[:, al] = tt; u[:, eks] = c + eg * tt
        ax.plot(u[:, 0], u[:, 1], c=rk[a], lw=2, label=f"{a}: boyunca kapsam %{w['boy_kapsam_yuzde']:.0f}")
    ax.set_xlim(x0 - 0.15 * L, x1 + 0.15 * L); ax.set_ylim(y0 - 0.15 * L, y1 + 0.15 * L)   # uçuşan noktalar dışarıda
    ax.set_aspect("equal"); ax.set_xlabel("m"); ax.set_ylabel("m"); ax.legend(fontsize=8, loc="upper left")
    ax.set_title(f"Dense kat planı (2,5 m altı): {boy:.2f} × {en:.2f} m, tavan {tavan:.2f} m")
    ax2 = fig.add_subplot(1, 2, 2)
    for a, w in d.items():
        p = w["profil"]
        if len(p):
            ax2.plot(p[:, 0] - p[0, 0], p[:, 1] * 100, "-o", c=rk[a], ms=3,
                     label=f"{a}: kayma {w['kayma_cm']:.1f} cm, RMS {w['rms_cm']:.1f} cm, düşeylik {w['duseylik_sapma_derece']:.1f}°")
    ax2.axhline(0, c="k", lw=0.5); ax2.grid(alpha=0.3); ax2.legend(fontsize=8)
    ax2.set_xlabel("duvar boyunca konum (m)"); ax2.set_ylabel("düzlemden sapma (cm)")
    ax2.set_title("Duvar boyunca düzlemden sapma (10 dilim, medyan)")
    fig.suptitle(f"{baslik}: paralellik uzun {sonuc['paralellik_uzun_duvarlar_derece']:.2f}°, kısa "
                 f"{sonuc['paralellik_kisa_duvarlar_derece']:.2f}°; diklik sapması en çok {max(dik.values()):.2f}°")
    fig.tight_layout(); fig.savefig(out / "dense_duvar_analizi.png", dpi=110); plt.close(fig)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), float(sys.argv[4]), sys.argv[5])
