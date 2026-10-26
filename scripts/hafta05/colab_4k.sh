#!/bin/bash
# 4K son model (A100, yüksek RAM): LoMa incremental pozları + 3840x2160 kareler, splatfacto-big.
# COLMAP gerekmez (SfM Drive'dan geri yüklenir). nerfstudio'nun pin_memory kopyası kapatılır
# (1440p'de RAM'i ikiye katlıyordu). Bellek bekçisi: kullanılabilir RAM 6 GB altına inerse durdurur.
set -u
W=/content/work
D=/content/drive/MyDrive/hafta5_derslik4
VIDEO="/content/drive/MyDrive/3dgs videoları/Merkezi Derslik_Derslik4/IMG_0299.MOV"
LOG=$W/kuyruk.log
say() { echo "$(date '+%H:%M') $*" >> $LOG; }
cd $W
say "4K kurulum başladı"

# 3DGS ortamı (arka planda)
(
  unset UV_SYSTEM_PYTHON
  pip install -q uv
  PY=/content/ns/bin/python
  [ -x $PY ] || uv venv /content/ns --python 3.11 -q
  uv pip install -q --python $PY torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu124
  uv pip install -q --python $PY nerfstudio==1.1.5 gsplat==1.4.0 psutil ninja torch==2.4.1 torchvision==0.19.1 \
    --extra-index-url https://download.pytorch.org/whl/cu124
  export PATH=/content/ns/bin:$PATH
  $PY -c "import torch; from gsplat import rasterization; m=torch.zeros(1,3,device='cuda'); q=torch.tensor([[1.,0,0,0]],device='cuda'); s=torch.ones(1,3,device='cuda')*0.1; o=torch.ones(1,device='cuda'); c=torch.ones(1,3,device='cuda'); v=torch.eye(4,device='cuda')[None]; v[0,2,3]=3; K=torch.tensor([[[100.,0,50],[0,100,50],[0,0,1]]],device='cuda'); r,_,_=rasterization(m,q,s,o,c,v,K,100,100); print('gsplat ok')"
  F=/content/ns/lib/python3.11/site-packages/nerfstudio/data/datamanagers/full_images_datamanager.py
  sed -i 's/cache\["image"\] = cache\["image"\].pin_memory()/cache["image"] = cache["image"].contiguous()  # pin_memory kapalı (RAM)/' $F
  grep -q "pin_memory kapalı" $F && echo "pin_memory kapalı"
) > $W/setup_ns.log 2>&1 &
NS=$!

# Kareler: aynı 1000 kare, 4K ve 1080p (1080p yalnız colab_gs'in kare listesi için)
if [ "$(ls $W/frames_4k 2>/dev/null | wc -l)" -lt 1000 ]; then
  cp "$VIDEO" $W/derslik4.MOV
  python - << 'EOF'
frames = open('/content/work/frame_list.txt').read().split()
sel = '+'.join(f'eq(n\\,{n})' for n in frames)
open('/content/work/select4k.txt', 'w').write(
    f"[0:v]select='{sel}',split=2[a][b];[b]scale=1920:1080:flags=lanczos[c]")
EOF
  mkdir -p frames_4k frames_1080
  ffmpeg -v error -y -threads 0 -i derslik4.MOV -filter_complex_script select4k.txt \
    -map "[a]" -fps_mode passthrough -q:v 2 frames_4k/%04d.jpg \
    -map "[c]" -fps_mode passthrough -q:v 2 frames_1080/%04d.jpg > extract.log 2>&1
fi
say "kareler: $(ls frames_4k | wc -l) x 4K"

# SfM ve önceki koşular Drive'dan
rsync -a --exclude 'sift/' $D/sfm/ $W/sfm/
rsync -a $D/runs/ $W/runs/

wait $NS
grep -q "gsplat ok" setup_ns.log && grep -q "pin_memory kapalı" setup_ns.log || { say "KURULUM HATASI (setup_ns.log)"; exit 1; }
say "4K kurulum bitti, eğitim başladı (splatfacto-big, 30k)"
# gsplat'ın derlenmiş çekirdeğini yüklemek için torch ninja ister; ninja ortamın bin klasöründe
export PATH=/content/ns/bin:$PATH

/content/ns/bin/python -u colab_gs.py loma sequential_loop incremental --res 4k --method splatfacto-big > blok4k.log 2>&1 &
GS=$!
while kill -0 $GS 2> /dev/null; do
  AVAIL=$(free -m | awk 'NR==2{print $7}')
  if [ "$AVAIL" -lt 6000 ]; then
    pkill -f nerfstudio.scripts.train
    say "BELLEK BEKÇİSİ: kullanılabilir RAM ${AVAIL} MiB, eğitim durduruldu"
  fi
  sleep 3
done
say "KUYRUK BİTTİ"
