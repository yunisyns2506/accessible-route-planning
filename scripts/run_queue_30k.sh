#!/usr/bin/env bash
# 30.000 iterasyon dogrulama kosulari: onerilen yapilandirma (G2) ve yogun model (G5).
set -u
PY="C:/Users/sabod/miniconda3/envs/nerfstudio/python.exe"
DATA="data/sinif-01/sfm_exhaustive"
IT=30000

run() {
  local name="$1"; shift; local method="$1"; shift
  if [ -f "runs/sinif-01/$name/run_metrics.json" ]; then echo ">>> $name zaten tamam"; return 0; fi
  echo ">>> $name basliyor ($(date +%H:%M))"
  "$PY" scripts/train_run.py "$name" "$method" "$DATA" "$IT" "$@"
  echo ">>> $name bitti ($(date +%H:%M))"
}

run G2_antialiased_30k splatfacto --pipeline.model.rasterize-mode antialiased
run G5_big_30k splatfacto-big

echo "=== 30K KUYRUGU BITTI ($(date +%H:%M)) ==="
