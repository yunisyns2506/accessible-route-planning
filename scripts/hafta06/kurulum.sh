#!/bin/bash
# Hafta 6 Colab kurulumu (Ubuntu 24.04, sürücü CUDA 13, L4 / sm_89).
#   1) COLMAP 4.2.1: CUDA + ONNX, vocab_tree_builder yamalı (LoMa 256 boyut).
#      Drive'da hazır derleme (kurulum/colmap_4.2.1_u2404_cu128_l4.tgz) varsa açılır; yoksa
#      CUDA 12.8 araç takımıyla kaynaktan derlenip oraya yedeklenir. CUDA 12.8 seçildi çünkü
#      COLMAP'in indirdiği ONNX Runtime CUDA 12 içindir ve gsplat'ın JIT derlemesi torch cu124 ile
#      aynı ana sürümde nvcc ister. Sürücü 580 CUDA 12 programlarını çalıştırır.
#   2) 3DGS ortamı /content/ns: Python 3.11, torch 2.4.1 cu124, nerfstudio 1.1.5, gsplat 1.4.0.
# İki iş paralel koşar; günlükler: $LOGS/kurulum_colmap.log, kurulum_ns.log, kurulum.log
set -u
H6="/content/drive/MyDrive/Hafta 6 Çalışmaları"
LOGS="$H6/meetingroom/logs"
TGZ="$H6/kurulum/colmap_4.2.1_u2404_cu128_l4.tgz"
CUDA=/usr/local/cuda-12.8
LOG="$LOGS/kurulum.log"
say() { echo "$(date '+%F %T') $*" >> "$LOG"; }
T0=$(date +%s)
say "kurulum başladı"

# CUDA 12.8 araç takımı (yalnız derleyici + başlıklar + kütüphaneler; sürücüye dokunulmaz)
cuda128() {
  [ -x $CUDA/bin/nvcc ] && return 0
  if ! apt-cache policy cuda-toolkit-12-8 2>/dev/null | grep -q Candidate; then
    wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb -O /tmp/ck.deb
    dpkg -i /tmp/ck.deb && apt-get update -qq
  fi
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq cuda-toolkit-12-8 > /dev/null
}

(
  set -e
  T=$(date +%s)
  pip install -q nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cufft-cu12 nvidia-cuda-runtime-cu12 \
    nvidia-curand-cu12 nvidia-cusparse-cu12 nvidia-cusolver-cu12 nvidia-nvjitlink-cu12 pycolmap-cuda12==4.2.1 psutil
  if [ -f "$TGZ" ]; then
    tar xzf "$TGZ" -C /content
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libboost-program-options-dev libgoogle-glog-dev \
      libopenimageio-dev libmetis-dev libsqlite3-dev libceres-dev libcurl4-openssl-dev libcgal-dev libglew-dev > /dev/null
    cuda128
    LD_LIBRARY_PATH=$CUDA/lib64 /content/colmap/bin/colmap -h > /dev/null && echo "hazır derleme açıldı" && exit 0
  fi
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ninja-build cmake libboost-program-options-dev \
    libboost-graph-dev libboost-system-dev libeigen3-dev libopenimageio-dev openimageio-tools \
    libmetis-dev libgoogle-glog-dev libgtest-dev libgmock-dev libsqlite3-dev libglew-dev libcgal-dev \
    libceres-dev libsuitesparse-dev libcurl4-openssl-dev libssl-dev bc > /dev/null
  cuda128
  echo "bağımlılıklar + CUDA 12.8: $(( $(date +%s) - T )) sn"
  [ -d /content/colmap-src ] || git clone -q --depth 1 --branch 4.2.1 https://github.com/colmap/colmap.git /content/colmap-src
  cd /content/colmap-src
  # vocab_tree_builder tanımlayıcı boyutunu sabit 128 alıyordu; LoMa (256) için veritabanından al
  sed -i 's/auto visual_index = retrieval::VisualIndex::Create();/auto visual_index = retrieval::VisualIndex::Create(descriptors.data.cols());/' \
    src/colmap/exe/vocab_tree.cc
  grep -q "VisualIndex::Create(descriptors.data.cols())" src/colmap/exe/vocab_tree.cc
  mkdir -p /usr/include/opencv4 build && cd build
  cmake .. -GNinja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_COMPILER=$CUDA/bin/nvcc \
    -DCUDAToolkit_ROOT=$CUDA -DCMAKE_CUDA_ARCHITECTURES=89 -DGUI_ENABLED=OFF \
    -DOPENGL_ENABLED=OFF -DONNX_ENABLED=ON -DFETCH_ONNX=ON -DTESTS_ENABLED=OFF \
    -DCMAKE_EXE_LINKER_FLAGS="-Wl,--no-as-needed /usr/lib/x86_64-linux-gnu/libGLdispatch.so.0" \
    -DCMAKE_INSTALL_PREFIX=/content/colmap
  ninja -j$(nproc) && ninja install
  # ONNX Runtime paylaşımlı kütüphaneleri de pakete girsin
  find /content/colmap-src/build -name "libonnxruntime*.so*" -exec cp -P {} /content/colmap/lib/ \; 2>/dev/null || true
  LD_LIBRARY_PATH=$CUDA/lib64 /content/colmap/bin/colmap -h > /dev/null
  echo "derleme: $(( $(date +%s) - T )) sn"
  tar czf "$TGZ" -C /content colmap && echo "yedek: $TGZ"
) > "$LOGS/kurulum_colmap.log" 2>&1 &
BUILD=$!

(
  set -e
  T=$(date +%s)
  unset UV_SYSTEM_PYTHON
  pip install -q uv
  PY=/content/ns/bin/python
  [ -x $PY ] || uv venv /content/ns --python 3.11 -q
  uv pip install -q --python $PY torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu124
  uv pip install -q --python $PY nerfstudio==1.1.5 gsplat==1.4.0 psutil ninja plyfile torch==2.4.1 torchvision==0.19.1 \
    --extra-index-url https://download.pytorch.org/whl/cu124
  echo "pip: $(( $(date +%s) - T )) sn"
  # gsplat CUDA çekirdekleri ilk çağrıda derlenir; CUDA 12.8 nvcc'yi bekle (derleme işi apt ile kuruyor)
  for i in $(seq 1 240); do [ -x $CUDA/bin/nvcc ] && break; sleep 10; done
  export CUDA_HOME=$CUDA PATH=/content/ns/bin:$CUDA/bin:$PATH TORCH_CUDA_ARCH_LIST=8.9
  $PY -c "import torch; from gsplat import rasterization; m=torch.zeros(1,3,device='cuda'); q=torch.tensor([[1.,0,0,0]],device='cuda'); s=torch.ones(1,3,device='cuda')*0.1; o=torch.ones(1,device='cuda'); c=torch.ones(1,3,device='cuda'); v=torch.eye(4,device='cuda')[None]; v[0,2,3]=3; K=torch.tensor([[[100.,0,50],[0,100,50],[0,0,1]]],device='cuda'); r,_,_=rasterization(m,q,s,o,c,v,K,100,100); print('gsplat ok')"
  echo "ns toplam: $(( $(date +%s) - T )) sn"
) > "$LOGS/kurulum_ns.log" 2>&1 &
NS=$!

wait $BUILD; RB=$?
wait $NS; RN=$?
say "COLMAP rc=$RB, ns rc=$RN, süre $(( ($(date +%s) - T0) / 60 )) dk"
[ $RB -eq 0 ] && [ $RN -eq 0 ] && say "KURULUM BİTTİ" || say "KURULUM HATASI"
