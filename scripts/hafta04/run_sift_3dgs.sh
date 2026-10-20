#!/usr/bin/env bash
# SIFT blogunun kalan isleri: vocab_tree bina olcegi vekili (k=7) ve secilen
# 6 SfM ciktisiyla 3DGS egitimleri (duz splatfacto, 30.000 iterasyon).
#
# Secim gerekcesi (SfM tablosuna gore):
#   exhaustive + incremental      referans, hoca listesi
#   exhaustive + global           ust sinirda global vs incremental
#   sequential + incremental      hoca listesi (parcali, 148 kare)
#   sequential + global           hoca listesi; referanstan 9,2 derece sapma
#   sequential_loop + incremental bina adayi
#   sequential_loop + global      bina adayi
# vocab_tree ciktilari referansla neredeyse ayni (<0,1 derece), hierarchical
# (leaf=100) ciktilari parcali oldugu icin egitilmez.
#
# Kullanim (depo kokunden): bash scripts/hafta04/run_sift_3dgs.sh
set -u
PY=/c/Users/sabod/miniconda3/envs/nerfstudio/python.exe
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8

$PY -u scripts/hafta04/colmap_bench.py sift --only vocab_tree_k7

for c in "exhaustive incremental" "exhaustive global" "sequential incremental" \
         "sequential global" "sequential_loop incremental" "sequential_loop global"; do
  set -- $c
  $PY -u scripts/hafta04/make_ns_data.py sift "$1" "$2"
  $PY -u scripts/hafta04/train_eval.py "sift_$1_$2"
done

$PY -u scripts/hafta04/collect.py
