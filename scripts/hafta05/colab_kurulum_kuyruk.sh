#!/bin/bash
# Hafta 5 Colab: sıfırdan kurulum + kalan kuyruk, kendi başına çalışır.
#   kurulum: kareler (1080p + 1440p), COLMAP 4.2.1 (CUDA + ONNX, yamalı), 3DGS ortamı,
#            A/B sonuçlarının Drive'dan geri yüklenmesi
#   C: SIFT + exhaustive + incremental SfM, ardından 1080p 3DGS (LoMa ile aynı ayar)
#   D: LoMa incremental ile SIFT'ten PSNR'ı yüksek olan, 1440p + splatfacto-big
#      (bellek bekçisiyle: kullanılabilir RAM 5 GB'ın altına inerse eğitim durdurulur)
# Önkoşul: Drive bağlı; /content/work/{colab_sfm.py,colab_gs.py,frame_list.txt} yerinde.
set -u
W=/content/work
D=/content/drive/MyDrive/hafta5_derslik4
VIDEO="/content/drive/MyDrive/3dgs videoları/Merkezi Derslik_Derslik4/IMG_0299.MOV"
LOG=$W/kuyruk.log
say() { echo "$(date '+%H:%M') $*" >> $LOG; }
cd $W
say "kurulum başladı"

# COLMAP derlemesi (arka planda)
(
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ninja-build libboost-program-options-dev \
    libboost-graph-dev libboost-system-dev libeigen3-dev libopenimageio-dev openimageio-tools \
    libmetis-dev libgoogle-glog-dev libgtest-dev libgmock-dev libsqlite3-dev libglew-dev libcgal-dev \
    libceres-dev libsuitesparse-dev libcurl4-openssl-dev libssl-dev bc > /dev/null
  pip install -q nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cufft-cu12 nvidia-cuda-runtime-cu12 \
    nvidia-curand-cu12 pycolmap-cuda12==4.2.1
  # Önceki kurulumun yedeği varsa derlemeyi atla (aynı yamalı derleme, L4 / sm_89)
  if [ -f $D/kurulum/colmap_4.2.1_l4.tgz ]; then
    tar xzf $D/kurulum/colmap_4.2.1_l4.tgz -C /content && /content/colmap/bin/colmap -h > /dev/null && exit 0
  fi
  [ -d /content/colmap-src ] || git clone -q --depth 1 --branch 4.2.1 \
    https://github.com/colmap/colmap.git /content/colmap-src
  cd /content/colmap-src
  # vocab_tree_builder tanımlayıcı boyutunu sabit 128 alıyordu; LoMa (256) için veritabanından al
  sed -i 's/auto visual_index = retrieval::VisualIndex::Create();/auto visual_index = retrieval::VisualIndex::Create(descriptors.data.cols());/' \
    src/colmap/exe/vocab_tree.cc
  # OpenImageIO paketi var olmayan bir OpenCV başlık klasörünü istiyor
  mkdir -p /usr/include/opencv4 build && cd build
  cmake .. -GNinja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_ARCHITECTURES=89 -DGUI_ENABLED=OFF \
    -DOPENGL_ENABLED=OFF -DONNX_ENABLED=ON -DFETCH_ONNX=ON -DTESTS_ENABLED=OFF \
    -DCMAKE_EXE_LINKER_FLAGS="-Wl,--no-as-needed /usr/lib/x86_64-linux-gnu/libGLdispatch.so.0" \
    -DCMAKE_INSTALL_PREFIX=/content/colmap && ninja -j10 && ninja install
) > $W/build.log 2>&1 &
BUILD=$!

# 3DGS ortamı (arka planda); Colab UV_SYSTEM_PYTHON=true ile gelir, ortam açıkça verilir
(
  unset UV_SYSTEM_PYTHON
  pip install -q uv
  PY=/content/ns/bin/python
  [ -x $PY ] || uv venv /content/ns --python 3.11 -q
  uv pip install -q --python $PY torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu124
  uv pip install -q --python $PY nerfstudio==1.1.5 gsplat==1.4.0 psutil ninja torch==2.4.1 torchvision==0.19.1 \
    --extra-index-url https://download.pytorch.org/whl/cu124
  # gsplat CUDA çekirdeklerini derle (ilk çağrıda; ninja ortamdan)
  export PATH=/content/ns/bin:$PATH
  $PY -c "import torch; from gsplat import rasterization; m=torch.zeros(1,3,device='cuda'); q=torch.tensor([[1.,0,0,0]],device='cuda'); s=torch.ones(1,3,device='cuda')*0.1; o=torch.ones(1,device='cuda'); c=torch.ones(1,3,device='cuda'); v=torch.eye(4,device='cuda')[None]; v[0,2,3]=3; K=torch.tensor([[[100.,0,50],[0,100,50],[0,0,1]]],device='cuda'); r,_,_=rasterization(m,q,s,o,c,v,K,100,100); print('gsplat ok')"
) > $W/setup_ns.log 2>&1 &
NS=$!

# Kareler: aynı 1000 kare, 1080p (SfM + karşılaştırma) ve 1440p (D bloğu)
if [ "$(ls $W/frames_1440 2>/dev/null | wc -l)" -lt 1000 ]; then
cp "$VIDEO" $W/derslik4.MOV
python - << 'EOF'
frames = open('/content/work/frame_list.txt').read().split()
sel = '+'.join(f'eq(n\\,{n})' for n in frames)
open('/content/work/select.txt', 'w').write(
    f"[0:v]select='{sel}',split=2[a][b];[a]scale=1920:1080:flags=lanczos[c];[b]scale=2560:1440:flags=lanczos[d]")
EOF
mkdir -p frames_1080 frames_1440
ffmpeg -v error -y -threads 0 -i derslik4.MOV -filter_complex_script select.txt \
  -map "[c]" -fps_mode passthrough -q:v 2 frames_1080/%04d.jpg \
  -map "[d]" -fps_mode passthrough -q:v 2 frames_1440/%04d.jpg > extract.log 2>&1
fi
say "kareler: $(ls frames_1080 | wc -l) x 1080p, $(ls frames_1440 | wc -l) x 1440p"

# A/B sonuçlarını geri yükle (SIFT'in yarım kalan koşusu hariç)
rsync -a --exclude 'sift/' $D/sfm/ $W/sfm/
rsync -a $D/runs/ $W/runs/

wait $BUILD; wait $NS
if [ ! -x /content/colmap/bin/colmap ] || ! grep -q "gsplat ok" setup_ns.log; then
  say "KURULUM HATASI (build.log / setup_ns.log)"; exit 1
fi
say "kurulum bitti"
# Hızlı geri dönüş için kurulumu Drive'a yedekle (yoksa)
[ -f $D/kurulum/colmap_4.2.1_l4.tgz ] || { mkdir -p $D/kurulum && tar czf $D/kurulum/colmap_4.2.1_l4.tgz -C /content colmap & }

say "C başladı"
python -u colab_sfm.py C > blokC.log 2>&1
/content/ns/bin/python -u colab_gs.py sift exhaustive incremental > blokC_gs.log 2>&1
say "C bitti"

BEST=$(python - << 'EOF'
import json
from pathlib import Path
c = {}
for run, args in (("loma_sequential_loop_incremental", "loma sequential_loop incremental"),
                  ("sift_exhaustive_incremental", "sift exhaustive incremental")):
    p = Path(f"/content/work/runs/{run}/summary.json")
    if p.exists():
        c[args] = json.loads(p.read_text())["psnr"]
print(max(c, key=c.get))
EOF
)
say "D başladı: $BEST (1440p, splatfacto-big)"
/content/ns/bin/python -u colab_gs.py $BEST --res 1440 --method splatfacto-big > blokD.log 2>&1 &
GS=$!
while kill -0 $GS 2> /dev/null; do
  AVAIL=$(free -m | awk 'NR==2{print $7}')
  if [ "$AVAIL" -lt 5000 ]; then
    pkill -f nerfstudio.scripts.train
    say "BELLEK BEKÇİSİ: kullanılabilir RAM ${AVAIL} MiB, eğitim durduruldu"
  fi
  sleep 5
done
say "KUYRUK BİTTİ"
