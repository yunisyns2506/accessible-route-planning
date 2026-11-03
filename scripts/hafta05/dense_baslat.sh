#!/bin/bash
# Hafta 5 Colab: Derslik 4 dense koşusunu hazırlar ve arka planda başlatır.
#   kurulum: pycolmap-cuda12 4.2.1 (Colab Ubuntu 24.04 / CUDA 13)
#   kareler: SfM'deki 1000 kare, videodan 1920x1080 (frame_list.txt)
#   model:   LoMa + sequential + döngü + incremental seyrek model, kare adları doğrulanır
#   başlat:  colab_dense.py, çekirdekten bağımsız (setsid); günlük dense/loma_inc/dense_run.log (Drive'a da yedeklenir)
# Önkoşul: Drive bağlı, çalışma zamanı L4. Tekrar çalıştırmak güvenli: biten adımlar atlanır.
set -euo pipefail
W=/content/work
D=/content/drive/MyDrive/hafta5_derslik4
VIDEO="/content/drive/MyDrive/3dgs videoları/Merkezi Derslik_Derslik4/IMG_0299.MOV"
M=sfm/loma/sequential_loop/incremental/sparse/0
mkdir -p $W && cd $W

GPU=$(nvidia-smi --query-gpu=name --format=csv,noheader)
[[ $GPU == *L4* ]] || { echo "HATA: GPU L4 değil ($GPU)"; exit 1; }
if pgrep -f colab_dense.py > /dev/null; then echo "Zaten çalışıyor"; exit 0; fi

pip install -q pycolmap-cuda12==4.2.1 psutil 2>&1 | grep -v -E 'cudf|cuml|torch|incompatible' || true
command -v rsync > /dev/null && command -v ffmpeg > /dev/null || \
  { apt-get update -qq && apt-get install -y -qq rsync ffmpeg > /dev/null; }
python -c "import pycolmap; assert pycolmap.has_cuda; print('pycolmap', pycolmap.__version__, 'CUDA tamam')"

cp $D/betikler/frame_list.txt $D/betikler/colab_dense.py $W/
if [ "$(ls $W/frames_1080 2>/dev/null | wc -l)" -lt 1000 ]; then
  echo "$(date '+%H:%M') video kopyalanıyor ve kareler çıkarılıyor ..."
  cp "$VIDEO" $W/derslik4.MOV
  python - << 'EOF'
frames = open('/content/work/frame_list.txt').read().split()
sel = '+'.join(f'eq(n\\,{n})' for n in frames)
open('/content/work/select_1080.txt', 'w').write(f"[0:v]select='{sel}',scale=1920:1080:flags=lanczos[c]")
EOF
  mkdir -p frames_1080
  ffmpeg -v error -y -threads 0 -i derslik4.MOV -filter_complex_script select_1080.txt \
    -map "[c]" -fps_mode passthrough -q:v 2 frames_1080/%04d.jpg
  rm -f derslik4.MOV
fi
echo "kareler: $(ls frames_1080 | wc -l)"

mkdir -p $M && rsync -a $D/$M/ $W/$M/
python - << 'EOF'
import os, pycolmap
rec = pycolmap.Reconstruction('/content/work/sfm/loma/sequential_loop/incremental/sparse/0')
names = [im.name for im in rec.images.values()]
missing = [n for n in names if n not in set(os.listdir('/content/work/frames_1080'))]
print(f'modelde {len(names)} kare, {len(rec.points3D)} nokta; klasörde eksik: {len(missing)}', missing[:5])
assert len(names) == 1000 and not missing, 'kare adları modelle uyuşmuyor'
EOF

# Drive'da 80 GB boş yer varsa derinlik/normal haritaları da yedeklenir
YEDEK=$(python -c "import shutil; print(1 if shutil.disk_usage('/content/drive/MyDrive').free > 80 * 2**30 else 0)")
echo "Drive harita yedeği: $([ $YEDEK = 1 ] && echo AÇIK || echo KAPALI) · yerel disk boş: $(df -h /content | awk 'NR==2{print $4}')"

mkdir -p $W/dense/loma_inc
YEDEK=$YEDEK setsid nohup python -u $W/colab_dense.py >> $W/dense/loma_inc/dense_run.log 2>&1 < /dev/null &
sleep 20
echo "BAŞLADI (pid $(pgrep -f colab_dense.py | head -1))"
tail -n 5 $W/dense/loma_inc/dense_run.log
