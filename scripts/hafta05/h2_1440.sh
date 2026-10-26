#!/bin/bash
# H2 ayarı (yalnız pozlama düzeltme, bilateral grid) ile 1440p splatfacto-big; ardından renk düzeltmeli
# değerlendirme ve H2 1080p + 1440p modellerinin Unity'ye hazır .ply'leri (Drive hafta5_derslik4/unity/).
set -u
W=/content/work; D=/content/drive/MyDrive/hafta5_derslik4
LOG=$W/h2b.log; say() { echo "$(date '+%H:%M') $*" >> $LOG; }
cd $W; say "H2 1440p big başladı"
if [ "$(ls $W/frames_1440 2>/dev/null | wc -l)" -lt 1000 ]; then
  [ -f $W/derslik4.MOV ] || cp "/content/drive/MyDrive/3dgs videoları/Merkezi Derslik_Derslik4/IMG_0299.MOV" $W/derslik4.MOV
  /usr/bin/python3 - << 'PYEOF'
frames = open('/content/work/frame_list.txt').read().split()
sel = '+'.join(f'eq(n\,{n})' for n in frames)
open('/content/work/select1440.txt', 'w').write(f"[0:v]select='{sel}',scale=2560:1440:flags=lanczos[c]")
PYEOF
  mkdir -p frames_1440
  ffmpeg -v error -y -threads 0 -i derslik4.MOV -filter_complex_script select1440.txt \
    -map "[c]" -fps_mode passthrough -q:v 2 frames_1440/%04d.jpg > extract1440.log 2>&1
fi
say "kareler: $(ls frames_1440 | wc -l) x 1440p"
[ "$(ls frames_1440 | wc -l)" -ge 1000 ] || { say "KARE HATASI (extract1440.log)"; exit 1; }
export PATH=/content/ns/bin:$PATH
RUN=loma_sequential_loop_incremental_1440_big_H2
/content/ns/bin/python -u colab_gs.py loma sequential_loop incremental --res 1440 --method splatfacto-big --tag H2 \
  --extra=' --pipeline.model.use-bilateral-grid True' > blokH2b.log 2>&1
grep -q '"psnr"' blokH2b.log || { say "EĞİTİM HATASI (blokH2b.log): $(tail -2 blokH2b.log | tr '\n' ' ' | cut -c1-200)"; exit 1; }
say "H2 1440p big: $(grep '"psnr"' blokH2b.log | tail -1 | cut -c1-250)"
/content/ns/bin/python renk_degerlendir.py $RUN > renk_H2b.log 2>&1 && say "renk düzeltmeli: $(tail -1 renk_H2b.log)"
rsync -a runs/$RUN/ $D/runs/$RUN/
# Unity'ye hazır .ply (sistem Python'u: pycolmap kurulu)
/usr/bin/python3 -m pip install -q plyfile scipy > /dev/null 2>&1
mkdir -p $D/unity
for R in loma_sequential_loop_incremental_H2 $RUN; do
  PLY=$(ls runs/$R/export/*.ply 2>/dev/null | head -1)
  [ -z "$PLY" ] && [ -f $D/runs/$R/export/splat.ply ] && PLY=$D/runs/$R/export/splat.ply
  DP=$(find runs/$R $D/runs/$R -name dataparser_transforms.json 2>/dev/null | head -1)
  /usr/bin/python3 unity_ply.py $PLY $DP sfm/loma/sequential_loop/incremental/sparse/0 207.2 $D/unity/derslik4_${R#loma_sequential_loop_incremental_}_unity.ply \
    > unity_$R.log 2>&1 && say "Unity ply: $R hazır" || say "UNITY HATASI $R (unity_$R.log)"
done
say "H2B KUYRUK BİTTİ"
