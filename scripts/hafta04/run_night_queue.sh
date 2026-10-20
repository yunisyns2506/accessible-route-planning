#!/usr/bin/env bash
# Gece kuyrugu (2026-10-20): ALIKED blogu (ayri baslatildi) bittikten sonra
# sirayla LoMa blogu ve dense reconstruction'lar. GPU'da ayni anda tek is
# calissin diye once ALIKED kuyrugunun bitmesi beklenir: COLMAP ve Python
# surecleri 2 kez ust uste (60 sn arayla) gorulmezse kuyruk bitmis sayilir.
#
# Kullanim (depo kokunden): bash scripts/hafta04/run_night_queue.sh
set -u
busy() { tasklist 2>/dev/null | grep -qiE "^(colmap|python)\.exe"; }
idle=0
while [ $idle -lt 2 ]; do
  if busy; then idle=0; else idle=$((idle + 1)); fi
  sleep 60
done
echo "[kuyruk] ALIKED blogu bitti: $(date +%H:%M)"

# LoMa blogu; sonunda ALIKED'in referans SfM ciktisi icin dense
bash scripts/hafta04/run_block.sh loma aliked exhaustive incremental
echo "[kuyruk] LoMa blogu + ALIKED dense bitti: $(date +%H:%M)"

PY=/c/Users/sabod/miniconda3/envs/nerfstudio/python.exe
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
$PY -u scripts/hafta04/dense_run.py loma exhaustive incremental
echo "[kuyruk] LoMa dense bitti: $(date +%H:%M)"
$PY -u scripts/hafta04/collect.py
echo "[kuyruk] TAMAM: $(date +%H:%M)"
