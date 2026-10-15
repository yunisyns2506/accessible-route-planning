#!/usr/bin/env bash
# Sinif-01 egitim kosulari kuyrugu.
# Hepsi ayni SfM ciktisini (tam eslestirme, 331 kare) kullanir; sadece tek bir
# ayar degisir. Boylece farkin kaynagi tek degiskene indirgenir.
#
# Kullanim: bash scripts/run_queue.sh
set -u

PY="C:/Users/sabod/miniconda3/envs/nerfstudio/python.exe"
DATA="data/sinif-01/sfm_exhaustive"
IT=15000

run() {
  local name="$1"; shift
  local method="$1"; shift
  if [ -f "runs/sinif-01/$name/run_metrics.json" ]; then
    echo ">>> $name zaten tamam, atlaniyor"
    return 0
  fi
  echo ">>> $name basliyor  ($(date +%H:%M))"
  "$PY" scripts/train_run.py "$name" "$method" "$DATA" "$IT" "$@"
  echo ">>> $name bitti     ($(date +%H:%M))"
}

# G2 - Makale [02] Mip-Splatting: kenar yumusatma / ornekleme hatasi
run G2_antialiased splatfacto --pipeline.model.rasterize-mode antialiased

# G3 - Makale [03] 2DGS gerekcesi: uzamis "igne" Gaussian'lari baskilama
run G3_scalereg splatfacto \
  --pipeline.model.use-scale-regularization True \
  --pipeline.model.max-gauss-ratio 5.0

# G4 - Tasarim raporu 4. bolum: COLMAP poz sapmalarini egitimde duzeltme
run G4_camopt splatfacto --pipeline.model.camera-optimizer.mode SO3xR3

# G5 - Arac raporu 5. bolum: daha yogun Gaussian butcesi
run G5_big splatfacto-big

# G6 - Tam cozunurluk (1080x1920); digerleri otomatik 540x960 kullaniyor
run G6_tamcozunurluk splatfacto nerfstudio-data --downscale-factor 1

# G7 - NeRF karsilastirmasi: 3DGS secimi icin olculmus gerekce
run G7_nerfacto nerfacto

echo "=== KUYRUK TAMAMLANDI ($(date +%H:%M)) ==="
