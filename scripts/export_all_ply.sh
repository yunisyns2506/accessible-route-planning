#!/usr/bin/env bash
# Egitilmis kosulari PLY olarak models/ altina disa aktarir.
#
# models/ tek konumdur: PLY dosyalari dogrudan oraya yazilir ve Git LFS ile
# surumlenir. Ayri bir exports/ klasoru tutulmaz.
#
# Kullanim:
#   bash scripts/export_all_ply.sh                  # runs/sinif-01/* icin
#   bash scripts/export_all_ply.sh runs/oda-01_video   # tek kosu
set -u

PY="C:/Users/sabod/miniconda3/envs/nerfstudio/python.exe"
TARGETS=("${@:-runs/sinif-01/*}")

for d in ${TARGETS[@]}; do
  [ -d "$d" ] || continue
  kosu=$(basename "$d")
  veri=$(basename "$(dirname "$d")")
  # runs/sinif-01/G2_... -> models/sinif-01_G2_...
  if [ "$veri" = "runs" ]; then
    out="models/$kosu"
  else
    out="models/${veri}_${kosu}"
  fi

  if [ -f "$out/splat.ply" ]; then
    echo ">>> $out zaten var, atlaniyor"
    continue
  fi

  cfg=$(ls -d "$d"/*/splatfacto/*/config.yml 2>/dev/null | tail -1)
  if [ -z "$cfg" ]; then
    echo ">>> $kosu: splatfacto config bulunamadi (NeRF kosulari PLY uretmez)"
    continue
  fi

  echo ">>> $kosu -> $out  ($(date +%H:%M))"
  mkdir -p "$out"
  "$PY" -m nerfstudio.scripts.exporter gaussian-splat \
    --load-config "$cfg" --output-dir "$out" > "$out/export_log.txt" 2>&1
  echo ">>> bitti: $(ls -lh "$out/splat.ply" 2>/dev/null | awk '{print $5}')"
done

echo "=== TAMAMLANDI ($(date +%H:%M)) ==="
