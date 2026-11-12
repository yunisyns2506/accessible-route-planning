"""Mezura ölçüleriyle ölçek kalibrasyonu ve bağımsız doğrulama (hafta 6). Uç noktalar olcum_hesap.py çıktısından.
Kalibrasyon: en küçük kareler (cm/birim). Hata = model - mezura. Çıktı: olcum/olcum_tablo.csv, olcum_sonuc.json"""
import csv, json, sys
from pathlib import Path
import numpy as np
d = Path(sys.argv[1]); N = json.loads((d / 'noktalar.json').read_text())
C_KOR = 0.9281513659824707; K_ESKI = 210.0
Z_U, PLAT_U = 14.582027725079842 / 2.1, (0.445 + 0.015) / 2.1
def L(a, b):
    v = np.linalg.norm(np.array(N[a]['X']) - np.array(N[b]['X']))
    return float(v * (C_KOR if N[a]['model'] == 'koridor' else 1))
# Kalibrasyon: kimliği net (tek tip pencere ve kapı), en az 3 karede 1 px altı tutan ölçüler. Şüpheli: aynı nesne olduğu doğrulanamayanlar.
olc = [('K1', 'Büyük pencere genişliği', L('pen_b_sol', 'pen_b_sag'), 217.5, 'kalibrasyon'), ('K2', 'Çift kanat kapı, kasa içi (sınıf)', L('kapi_ic_sol', 'kapi_ic_sag'), 152.5, 'kalibrasyon'),
       ('K3', 'Küçük pencere genişliği', L('pen_k_sol', 'pen_k_sag'), 115.7, 'kalibrasyon'),
       ('D1', 'Sınıf kısa kenarı (duvar düzlemleri)', Z_U, 1480.0, 'doğrulama'), ('D2', 'Sahne yüksekliği (düzlemler)', PLAT_U, 46.0, 'doğrulama'),
       ('D3', 'K3 kapısı, kasa içi (koridor modeli)', L('kor_kapi_sol', 'kor_kapi_sag'), 152.5, 'doğrulama'), ('D4', 'K3 tek kanat net açıklık (koridor modeli)', L('kor_kapi_sol', 'kor_kanat_sol'), 74.5, 'doğrulama'),
       ('D5', 'Öğretmen masası genişliği', L('masa_sol', 'masa_sag'), 130.0, 'doğrulama'), ('D6', 'Askı yüksekliği', L('aski_P_alt', 'aski_P_ust'), 34.0, 'doğrulama'),
       ('D7', 'Kürsü üst levha, ön kenar genişliği', L('kursu_sol', 'kursu_sag'), 69.0, 'doğrulama'),
       ('D8', 'Askı genişliği (K3 yanındaki uzun askı, alt kenar)', L('aski_uzun_sol', 'aski_uzun_sag'), 200.0, 'doğrulama'), ('D9', 'Radyatör genişliği (pencere altı, üst kenar)', L('rad_sol', 'rad_sag'), 100.0, 'doğrulama')]
c = [o for o in olc if o[4] == 'kalibrasyon']; u = np.array([o[2] for o in c]); m = np.array([o[3] for o in c]); s = float(u @ m / (u @ u))
print(f'ölçek {s:.2f} cm/birim (önceki tahmin {K_ESKI}; fark {100 * (s - K_ESKI) / K_ESKI:+.2f}%)')
rows = []
for k, ad, un, tp, t in olc:
    md = un * s; rows.append({'kod': k, 'olcu': ad, 'tur': t, 'mezura_cm': tp, 'model_cm': round(md, 1), 'hata_cm': round(md - tp, 1), 'hata_yuzde': round(100 * (md - tp) / tp, 1)})
    print(f'{k:3s} {ad:42s} {tp:7.1f} {md:7.1f} {md - tp:+6.1f} cm {100 * (md - tp) / tp:+5.1f}%  [{t}]')
def ozet(R): e = np.array([r['hata_cm'] for r in R]); return dict(n=len(R), MAE_cm=round(float(np.abs(e).mean()), 2), RMSE_cm=round(float(np.sqrt((e ** 2).mean())), 2), ort_cm=round(float(e.mean()), 2), en_buyuk_cm=round(float(np.abs(e).max()), 2))
kal, dog, sup = [[r for r in rows if r['tur'] == t] for t in ('kalibrasyon', 'doğrulama', 'şüpheli')]
print('kalibrasyon', ozet(kal)); print('doğrulama', ozet(dog))
for n, R in (('kisa kenar haric', [r for r in dog if r['kod'] != 'D1']),): print(n, ozet(R))
with open(d / 'olcum_tablo.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
(d / 'olcum_sonuc.json').write_text(json.dumps({'olcek_cm_birim': s, 'kalibrasyon': ozet(kal), 'dogrulama': ozet(dog), 'satirlar': rows}, ensure_ascii=False, indent=1), encoding='utf-8')
