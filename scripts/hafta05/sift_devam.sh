#!/bin/bash
# SIFT exhaustive'i ikinci makinede (Untitled1, DN'den sonra) Drive yedeğinden sürdürür.
# Hafta_5 çalışma zamanı ~23:10-23:40 TR arasında koptu; son yedek database.db (eşleşmiş çiftler korunur,
# COLMAP yalnız eksik çiftleri eşler). COLMAP kurulumu Drive'daki derlenmiş paketten açılır.
set -u
export PATH=/usr/local/nvidia/bin:/usr/local/cuda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
W=/content/work; D=/content/drive/MyDrive/hafta5_derslik4
LOG=$W/sift.log; say() { echo "$(date '+%H:%M') $*" >> $LOG; }
cd $W; say "SIFT devam: kurulum (ikinci makine)"
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libboost-program-options-dev libboost-graph-dev \
  libboost-system-dev libeigen3-dev libopenimageio-dev openimageio-tools libmetis-dev libgoogle-glog-dev \
  libsqlite3-dev libglew-dev libcgal-dev libceres-dev libsuitesparse-dev libcurl4-openssl-dev > $W/apt_sift.log 2>&1
python3 -m pip install -q nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cufft-cu12 nvidia-cuda-runtime-cu12 \
  nvidia-curand-cu12 pycolmap-cuda12==4.2.1 psutil >> $W/apt_sift.log 2>&1
[ -x /content/colmap/bin/colmap ] || tar xzf $D/kurulum/colmap_4.2.1_l4.tgz -C /content
/content/colmap/bin/colmap -h > /dev/null 2>&1 || { say "SIFT DEVAM: COLMAP HATASI (apt_sift.log)"; exit 1; }
[ "$(ls $W/frames_1080 | wc -l)" -ge 1000 ] || { say "SIFT DEVAM: KARE HATASI"; exit 1; }
cp -f $D/betikler/sift_kuyruk.sh $D/betikler/colab_sfm.py $W/
say "SIFT devam: kurulum tamam, yedekten sürdürülüyor"
bash $W/sift_kuyruk.sh > $W/sift_ana.log 2>&1
say "SIFT DEVAM BİTTİ"
