#!/bin/bash
# DN-Splatter koşusu (ikinci L4, H2'den sonra): LoMa incremental pozları, 1080p, 30k iterasyon,
# Depth Anything V2 metrik derinliği (Pearson derinlik kaybı) + derinlikten normaller.
# Kamera pozu ince ayarı KAPALI; test kareleri tabanla aynı (dn_veri.py'deki yeniden adlandırma).
# Her aşama doğrulanır; bir aşama başarısızsa log'a yazılır ve durulur.
set -u
W=/content/work; D=$W/dn/derslik4; DR=/content/drive/MyDrive/hafta5_derslik4
RUN=$W/runs/loma_DN; PY=/content/dn/bin/python
LOG=$W/dn.log; say() { echo "$(date '+%H:%M') $*" >> $LOG; }
cd $W; say "DN başladı"

# 1) Ortam: nerfstudio 1.1.3 + gsplat 1.0.0 (dn-splatter'ın sabitlediği sürümler), Python 3.10
(
  unset UV_SYSTEM_PYTHON
  [ -x $PY ] || uv venv /content/dn --python 3.10 -q
  uv pip install -q --python $PY torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu124
  # PyMCubes 0.1.2 (dn-splatter sabiti) numpy 2 ile derlenmiyor: tekerleği olan sürüm ve numpy<2 zorlanır
  printf 'PyMCubes>=0.1.4\nnumpy<2\n' > $W/dn_override.txt
  uv pip install -q --python $PY "dn-splatter @ git+https://github.com/maturk/dn-splatter" ninja setuptools==69.5.1 \
      torch==2.4.1 torchvision==0.19.1 --extra-index-url https://download.pytorch.org/whl/cu124 \
      --index-strategy unsafe-best-match --override $W/dn_override.txt
  export PATH=/content/dn/bin:$PATH
  $PY -c "import torch; from gsplat import rasterization; m=torch.zeros(1,3,device='cuda'); q=torch.tensor([[1.,0,0,0]],device='cuda'); s=torch.ones(1,3,device='cuda')*0.1; o=torch.ones(1,device='cuda'); c=torch.ones(1,3,device='cuda'); v=torch.eye(4,device='cuda')[None]; v[0,2,3]=3; K=torch.tensor([[[100.,0,50],[0,100,50],[0,0,1]]],device='cuda'); r,_,_=rasterization(m,q,s,o,c,v,K,100,100); print('gsplat ok')"
  f=$(ls /content/dn/lib/python3.10/site-packages/nerfstudio/data/datamanagers/full_images_datamanager.py)
  sed -i 's/cache\["image"\] = cache\["image"\].pin_memory()/cache["image"] = cache["image"].contiguous()/' $f
) > $W/setup_dn.log 2>&1 &
ENV=$!

# 2) Veri: yeniden adlandırma + COLMAP + hizalı metrik derinlik (sistem Python'u, ortam kurulurken)
/usr/bin/python3 -m pip install -q pycolmap-cuda12==4.2.1 > $W/pip_pycolmap.log 2>&1
/usr/bin/python3 -u $W/dn_veri.py > $W/dn_veri.log 2>&1 || { say "VERİ HATASI (dn_veri.log)"; exit 1; }
say "veri: $(grep -h 'kare\|derinlik' $W/dn_veri.log | tr '\n' ' ')"
wait $ENV
grep -q "gsplat ok" $W/setup_dn.log || { say "ORTAM HATASI (setup_dn.log)"; exit 1; }
export PATH=/content/dn/bin:$PATH
say "ortam hazır: $($PY -c 'import nerfstudio, gsplat; print(nerfstudio.__version__ if hasattr(nerfstudio, "__version__") else "ns", gsplat.__version__)' 2>&1 | tail -1)"

# 3) Bölünme denetimi: test listesi tam olarak 0000, 0010, ..., 0990 (= eski 0010 ... 1000) olmalı
$PY - > $W/dn_bolunme.log 2>&1 << 'PYEOF' || { say "BÖLÜNME HATASI (dn_bolunme.log)"; exit 1; }
from pathlib import Path
from dn_splatter.data.coolermap_dataparser import CoolerMapDataParserConfig
c = CoolerMapDataParserConfig(data=Path('/content/work/dn/derslik4'), eval_interval=10, load_depths=False,
                              load_normals=False, load_pcd_normals=False)
o = c.setup().get_dataparser_outputs('test')
names = [p.name for p in o.image_filenames]
assert names == [f'{i:04d}.jpg' for i in range(0, 1000, 10)], names[:5]
print('bölünme tamam', len(names))
PYEOF
say "bölünme tamam: 100 test karesi tabanla aynı"

# 4) Eğitim. float32 kare önbelleği (~25 GB) + derinlikler 52 GB RAM'i doldurdu; bu yüzden kareler 8 bit önbellekte
#    tutulur ve GPU'ya alınırken float'a çevrilir (dn-splatter'ın SSIM kaybı 8 bit kareyi doğrudan kabul etmiyor).
#    Normaller: coolermap derinlikten normal üretimini COLMAP verisinde desteklemiyor (transforms.json'da derinlik
#    yolu arıyor), bu yüzden yalnız derinlik kaybı kullanılır.
#    dn-splatter kendi datamanager'ında next_train/next_eval_image'ı yeniden tanımlıyor; iki dosya da yamalanır.
: > $W/dn_u8_yama.txt
for F in /content/dn/lib/python3.10/site-packages/nerfstudio/data/datamanagers/full_images_datamanager.py \
         /content/dn/lib/python3.10/site-packages/dn_splatter/dn_datamanager.py; do
  grep -q "hafta5_u8" $F || sed -i 's/^\( *\)data\["image"\] = data\["image"\].to(self.device)$/&\n\1if data["image"].dtype == torch.uint8: data["image"] = data["image"].float() \/ 255.0  # hafta5_u8/' $F
  echo "$(basename $F) $(grep -c hafta5_u8 $F)" >> $W/dn_u8_yama.txt
done
U8="--pipeline.datamanager.cache-images-type uint8"
egit() {   # $1: normaller (True/False)
  rm -rf $RUN
  ns-train dn-splatter --output-dir $RUN --experiment-name loma_DN --max-num-iterations 30000 \
    --steps-per-eval-image 2000 --steps-per-eval-batch 5000 --steps-per-save 30000 --viewer.quit-on-train-completion True --vis tensorboard \
    --pipeline.datamanager.cache-images cpu $U8 \
    --pipeline.model.camera-optimizer.mode off --pipeline.model.use-depth-loss True --pipeline.model.depth-lambda 0.2 --pipeline.model.depth-loss-type PearsonDepth \
    --pipeline.model.use-normal-loss $1 --pipeline.model.use-normal-tv-loss $1 --pipeline.model.normal-supervision mono \
    coolermap --data $D --depth-mode mono --load-normals $1 --normals-from depth --load-pcd-normals False \
    --eval-interval 10 > $W/dn_train_$1.log 2>&1
}
T0=$(date +%s); say "eğitim başladı (yalnız derinlik kaybı, Pearson)"
egit False
ls $RUN/*/*/*/nerfstudio_models/step-000029999.ckpt > /dev/null 2>&1 || { say "EĞİTİM HATASI (dn_train_False.log)"; exit 1; }
say "eğitim bitti: $(( ($(date +%s) - T0) / 60 )) dk"

# 5) Değerlendirme (tabanla aynı renk düzeltmeli betik), dışa aktarma, Drive
sed -i "s/if row\['frame'\] in ('0250.jpg', '0500.jpg', '0750.jpg'):/if row['frame'] in ('0250.jpg', '0500.jpg', '0750.jpg', '0240.jpg', '0490.jpg', '0740.jpg'):/" $W/renk_degerlendir.py
$PY $W/renk_degerlendir.py loma_DN > $W/dn_eval.log 2>&1 && say "DN: $(tail -1 $W/dn_eval.log)" || say "DEĞERLENDİRME HATASI (dn_eval.log)"
CFG=$(ls $RUN/*/*/*/config.yml | tail -1)
ns-export gaussian-splat --load-config $CFG --output-dir $RUN/export > $W/dn_export.log 2>&1
say "dışa aktarma: $(ls -la $RUN/export/*.ply 2>&1 | tail -1)"
rsync -a $RUN/ $DR/runs/loma_DN/ && cp -f $D/derinlik_hizalama.json $DR/runs/loma_DN/ 2>/dev/null
say "DN KUYRUK BİTTİ"
