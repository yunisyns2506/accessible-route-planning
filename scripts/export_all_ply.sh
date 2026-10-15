#!/usr/bin/env bash
# Tum egitim kosularini PLY olarak disa aktarir.
PY="C:/Users/sabod/miniconda3/envs/nerfstudio/python.exe"
for d in runs/sinif-01/*/; do
  name=$(basename "$d")
  out="exports/sinif-01/$name"
  if [ -f "$out/splat.ply" ]; then echo ">>> $name zaten var, atlaniyor"; continue; fi
  cfg=$(ls -d "$d"*/splatfacto/*/config.yml 2>/dev/null | tail -1)
  if [ -z "$cfg" ]; then echo ">>> $name: config bulunamadi"; continue; fi
  echo ">>> $name disa aktariliyor ($(date +%H:%M))"
  mkdir -p "$out"
  "$PY" -m nerfstudio.scripts.exporter gaussian-splat --load-config "$cfg" --output-dir "$out" >"$out/export_log.txt" 2>&1
  echo ">>> $name bitti: $(ls -lh "$out/splat.ply" 2>/dev/null | awk '{print $5}')"
done
echo "=== TUM EXPORTLAR BITTI ($(date +%H:%M)) ==="
