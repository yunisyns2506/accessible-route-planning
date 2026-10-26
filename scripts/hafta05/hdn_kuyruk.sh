#!/bin/bash
# Hafta 5 iyileştirme koşuları (ikinci Colab L4): LoMa incremental verisi, 1080p, 30k iterasyon.
#   H: splatfacto + pozlama düzeltme (bilateral grid) + kamera pozu ince ayarı (SO3xR3)
#      + MCMC yoğunlaştırma (en çok 2 M Gaussian). Kurulu nerfstudio'da olmayan ayar atlanır, loga yazılır.
#   DN (DN-Splatter) ayrı ortam gerektirdiği için H bittikten sonra elle kurulacak.
# Önkoşul: Drive bağlı; betikler /content/work'te (colab_sfm.py, colab_gs.py, frame_list.txt).
set -u
W=/content/work; D=/content/drive/MyDrive/hafta5_derslik4
VIDEO="/content/drive/MyDrive/3dgs videoları/Merkezi Derslik_Derslik4/IMG_0299.MOV"
LOG=$W/hdn.log; say() { echo "$(date '+%H:%M') $*" >> $LOG; }
cd $W; say "kurulum başladı"
(
  unset UV_SYSTEM_PYTHON; pip install -q uv; PY=/content/ns/bin/python
  [ -x $PY ] || uv venv /content/ns --python 3.11 -q
  uv pip install -q --python $PY torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu124
  uv pip install -q --python $PY nerfstudio==1.1.5 gsplat==1.4.0 psutil ninja torch==2.4.1 torchvision==0.19.1 \
    --extra-index-url https://download.pytorch.org/whl/cu124
  export PATH=/content/ns/bin:$PATH
  $PY -c "import torch; from gsplat import rasterization; m=torch.zeros(1,3,device='cuda'); q=torch.tensor([[1.,0,0,0]],device='cuda'); s=torch.ones(1,3,device='cuda')*0.1; o=torch.ones(1,device='cuda'); c=torch.ones(1,3,device='cuda'); v=torch.eye(4,device='cuda')[None]; v[0,2,3]=3; K=torch.tensor([[[100.,0,50],[0,100,50],[0,0,1]]],device='cuda'); r,_,_=rasterization(m,q,s,o,c,v,K,100,100); print('gsplat ok')"
  f=/content/ns/lib/python3.11/site-packages/nerfstudio/data/datamanagers/full_images_datamanager.py
  sed -i 's/cache\["image"\] = cache\["image"\].pin_memory()/cache["image"] = cache["image"].contiguous()/' $f
) > $W/setup_ns.log 2>&1 &
NSP=$!
# 1000 kare 1080p (SfM ile aynı seçim ve ölçekleme)
if [ "$(ls $W/frames_1080 2>/dev/null | wc -l)" -lt 1000 ]; then
  cp "$VIDEO" $W/derslik4.MOV
  python - << 'PYEOF'
frames = open('/content/work/frame_list.txt').read().split()
sel = '+'.join(f'eq(n\,{n})' for n in frames)
open('/content/work/select.txt', 'w').write(f"[0:v]select='{sel}',scale=1920:1080:flags=lanczos[c]")
PYEOF
  mkdir -p frames_1080
  ffmpeg -v error -y -threads 0 -i derslik4.MOV -filter_complex_script select.txt \
    -map "[c]" -fps_mode passthrough -q:v 2 frames_1080/%04d.jpg > extract.log 2>&1
fi
say "kareler: $(ls frames_1080 | wc -l) x 1080p"
mkdir -p sfm && rsync -a --exclude '*.db' $D/sfm/loma $W/sfm/
say "SfM modeli: $(ls sfm/loma/sequential_loop/incremental/sparse 2>/dev/null | tr '\n' ' ')"
wait $NSP; say "3DGS ortamı: $(tail -1 setup_ns.log)"
export PATH=/content/ns/bin:$PATH
# Ayar adlarını kurulu nerfstudio'nun yardımından doğrula; olmayanı atla
HELP=$(/content/ns/bin/ns-train splatfacto --help 2>&1)
EXTRA=""
for kv in "use-bilateral-grid True" "camera-optimizer.mode SO3xR3" "strategy mcmc" "max-gs-num 2000000"; do
  k=${kv%% *}
  if echo "$HELP" | grep -q -- "--pipeline.model.$k"; then EXTRA="$EXTRA --pipeline.model.$kv"; else say "ayar yok, atlandı: $k"; fi
done
say "H ayarları:$EXTRA"
/content/ns/bin/python -u colab_gs.py loma sequential_loop incremental --tag H --extra "$EXTRA" > blokH.log 2>&1
say "H: $(tail -1 blokH.log | cut -c1-300)"
say "KUYRUK BİTTİ"
