#!/bin/bash
# Hafta 5 · Çalıştırılabilir COLMAP yapılandırması (Derslik 4 ile aynı ayarlar)
# Önerilen hat: LoMa + sequential + loop + incremental
# İsteğe bağlı: LoMa + sequential + loop + hierarchical, SIFT + exhaustive + incremental
#
# Gerekenler: COLMAP 4.2.1, CUDA + ONNX ile derlenmiş ve vocab_tree_builder yamalı
#   (Drive: kurulum/colmap_4.2.1_l4.tgz, L4 GPU; yama: src/colmap/exe/vocab_tree.cc,
#    VisualIndex::Create(descriptors.data.cols()) — LoMa'nın 256 boyutlu tanımlayıcıları için)
#   Not (Kasım 2026): hazır derleme eski Colab görüntüsü (Ubuntu 22.04, CUDA 12) içindir. Colab
#   Ubuntu 24.04 / CUDA 13'e geçti; orada kaynaktan yeniden derlemek gerekir. Yalnız dense için
#   pip'teki pycolmap-cuda12==4.2.1 yeterlidir (colab_dense.py); o paket LoMa'yı çalıştırmaz (ONNX yok).
#
# Kullanım: bash colmap_yapilandirma.sh <kareler_klasoru> <cikti_klasoru> [loma|hier|sift|hepsi] [dense]
set -euo pipefail

# ---------- Yapılandırma (bütün ayarlar burada) ----------
COLMAP=${COLMAP:-/content/colmap/bin/colmap}
IMAGES=${1:?kareler klasörü (ör. frames_1080)}
OUT=${2:?çıktı klasörü}
MODE=${3:-loma}
DENSE=${4:-}                 # "dense": önerilen hattın modelinden tam çözünürlükte dense

SEED=1                       # tekrarlanabilirlik
CAMERA_MODEL=OPENCV          # tek kamera, bozulma katsayılı
SINGLE_CAMERA=1

LOMA_TYPE=LOMA_B             # LoMa özellik çıkarma + eşleştirme
VOCAB_WORDS=8192             # döngü tespiti için sözlük ağacı (bu çekimin LoMa tanımlayıcılarından)
VOCAB_MAX_DESC=400000
LOOP_PERIOD=10               # her 10 karede bir döngü araması
LOOP_NUM_IMAGES=50           # her aramada 50 aday kare
HIER_LEAF=250                # hierarchical: alt model başına en çok kare

SIFT_MATCH=SIFT_BRUTEFORCE   # SIFT exhaustive eşleştirme türü
# ---------------------------------------------------------

run() { echo ">> $*"; "$@"; }

loma_common() {
  local d=$OUT/loma; mkdir -p $d
  run $COLMAP feature_extractor --database_path $d/features.db --image_path $IMAGES \
    --ImageReader.single_camera $SINGLE_CAMERA --ImageReader.camera_model $CAMERA_MODEL \
    --FeatureExtraction.type $LOMA_TYPE --default_random_seed $SEED
  run $COLMAP vocab_tree_builder --database_path $d/features.db \
    --vocab_tree_path $d/vocab_tree_loma_$VOCAB_WORDS.bin \
    --num_visual_words $VOCAB_WORDS --max_num_descriptors $VOCAB_MAX_DESC --default_random_seed $SEED
  mkdir -p $d/sequential_loop
  cp $d/features.db $d/sequential_loop/database.db
  run $COLMAP sequential_matcher --database_path $d/sequential_loop/database.db \
    --FeatureMatching.type $LOMA_TYPE \
    --SequentialMatching.loop_detection 1 \
    --SequentialMatching.vocab_tree_path $d/vocab_tree_loma_$VOCAB_WORDS.bin \
    --SequentialMatching.loop_detection_period $LOOP_PERIOD \
    --SequentialMatching.loop_detection_num_images $LOOP_NUM_IMAGES \
    --default_random_seed $SEED
}

loma_incremental() {
  local d=$OUT/loma/sequential_loop; mkdir -p $d/incremental/sparse
  run $COLMAP mapper --database_path $d/database.db --image_path $IMAGES \
    --output_path $d/incremental/sparse --default_random_seed $SEED
}

loma_hierarchical() {
  local d=$OUT/loma/sequential_loop; mkdir -p $d/hierarchical_leaf$HIER_LEAF/sparse
  run $COLMAP hierarchical_mapper --database_path $d/database.db --image_path $IMAGES \
    --output_path $d/hierarchical_leaf$HIER_LEAF/sparse \
    --HierarchicalMapper.leaf_max_num_images $HIER_LEAF --default_random_seed $SEED
}

sift_exhaustive() {
  local d=$OUT/sift/exhaustive; mkdir -p $d/incremental/sparse
  run $COLMAP feature_extractor --database_path $d/database.db --image_path $IMAGES \
    --ImageReader.single_camera $SINGLE_CAMERA --ImageReader.camera_model $CAMERA_MODEL \
    --FeatureExtraction.type SIFT --default_random_seed $SEED
  run $COLMAP exhaustive_matcher --database_path $d/database.db \
    --FeatureMatching.type $SIFT_MATCH --default_random_seed $SEED
  run $COLMAP mapper --database_path $d/database.db --image_path $IMAGES \
    --output_path $d/incremental/sparse --default_random_seed $SEED
}

dense() {   # tam çözünürlük, geometrik tutarlılık; 1000 karede L4'te ~10 sa
  local d=$OUT/dense/loma_inc; mkdir -p $d
  run $COLMAP image_undistorter --image_path $IMAGES \
    --input_path $OUT/loma/sequential_loop/incremental/sparse/0 --output_path $d --output_type COLMAP
  run $COLMAP patch_match_stereo --workspace_path $d --workspace_format COLMAP \
    --PatchMatchStereo.geom_consistency true
  run $COLMAP stereo_fusion --workspace_path $d --workspace_format COLMAP --input_type geometric \
    --output_path $d/fused.ply
  run $COLMAP poisson_mesher --input_path $d/fused.ply --output_path $d/meshed-poisson.ply
}

case $MODE in
  loma)  loma_common; loma_incremental ;;
  hier)  loma_common; loma_hierarchical ;;
  sift)  sift_exhaustive ;;
  hepsi) loma_common; loma_incremental; loma_hierarchical; sift_exhaustive ;;
  *) echo "mod: loma | hier | sift | hepsi"; exit 1 ;;
esac
if [ "$DENSE" = dense ]; then dense; fi
echo "Bitti. En büyük model: <çıktı>/.../sparse/0 (birden çok model varsa en çok kareli olan)"
