#!/usr/bin/env bash
# LoMa'nin sozluk agaci gerektiren uc stratejisi. Ilk denemede COLMAP'in
# vocab_tree_builder komutu 256 boyutlu LoMa tanimlayicilarinda coktugu icin
# N/A kalmislardi; agac artik pycolmap ile kuruluyor (build_vocab_tree.py,
# 8.192 gorsel sozcuk). Sira, sure sinirina gore onceliklendirilmistir:
#   1) sequential_loop SfM + 3DGS'in 6'li setindeki iki egitimi
#   2) vocab_tree_k7 (bina olcegi vekili, ucuz)
#   3) vocab_tree (en pahali; zaman yetmezse durdurulur)
#
# Kullanim (depo kokunden): bash scripts/hafta04/run_loma_vocab.sh
set -u
PY=/c/Users/sabod/miniconda3/envs/nerfstudio/python.exe
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
B=data/sinif-01/hafta-04/sfm/loma/r1

rm -f $B/vocab_build.log
for m in sequential_loop vocab_tree vocab_tree_k7; do rm -f $B/$m/match.json; done

$PY -u scripts/hafta04/colmap_bench.py loma --only sequential_loop
for mapper in incremental global; do
  if $PY -u scripts/hafta04/make_ns_data.py loma sequential_loop $mapper; then
    $PY -u scripts/hafta04/train_eval.py loma_sequential_loop_$mapper
  fi
done
$PY -u scripts/hafta04/colmap_bench.py loma --only vocab_tree_k7
$PY -u scripts/hafta04/colmap_bench.py loma --only vocab_tree
echo "[loma_vocab] TAMAM $(date +%H:%M)"
