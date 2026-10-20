#!/usr/bin/env bash
# Bir ozellik cikarici blogunu bastan sona kosar:
#   1) 15 SfM kombinasyonu (5 eslestirme x 3 SfM yontemi)
#   2) SIFT blogunda secilen 6 SfM kombinasyonuyla 3DGS (karsilastirilabilirlik
#      icin her cikaricida ayni 6 kombinasyon; SfM'i basarisiz olan atlanir)
#   3) sonuc tablolari
#   4) istege bagli: verilen SfM ciktisi icin dense reconstruction
#
# Kullanim (depo kokunden):
#   bash scripts/hafta04/run_block.sh <sift|aliked|loma> [dense_cikarici dense_eslestirme dense_mapper]
#
# Ornek:
#   bash scripts/hafta04/run_block.sh aliked sift exhaustive incremental
set -u
PY=/c/Users/sabod/miniconda3/envs/nerfstudio/python.exe
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
EXT=$1
DENSE=("${@:2}")   # set -- asagida konum argumanlarini ezdigi icin saklanir

$PY -u scripts/hafta04/colmap_bench.py "$EXT"

for c in "exhaustive incremental" "exhaustive global" "sequential incremental" \
         "sequential global" "sequential_loop incremental" "sequential_loop global"; do
  set -- $c
  if $PY -u scripts/hafta04/make_ns_data.py "$EXT" "$1" "$2"; then
    $PY -u scripts/hafta04/train_eval.py "${EXT}_$1_$2"
  else
    echo "[${EXT}_$1_$2] 3DGS atlandi: SfM ciktisi yok"
  fi
done

$PY -u scripts/hafta04/collect.py

if [ "${#DENSE[@]}" -eq 3 ]; then
  $PY -u scripts/hafta04/dense_run.py "${DENSE[@]}"
fi
