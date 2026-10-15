@echo off
chcp 65001 >nul
set "PATH=C:\Users\sabod\tools\colmap;C:\Users\sabod\tools\ffmpeg;%PATH%"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

echo =====================================================================
echo  Run 3: 512 Fotograf COLMAP SfM Isleniyor (Exhaustive Matching)
echo =====================================================================
echo.

C:\Users\sabod\miniconda3\envs\nerfstudio\python.exe -m nerfstudio.scripts.process_data images --data data\oda-01_512foto\raw_images --output-dir data\oda-01_512foto\processed --camera-type perspective --matching-method exhaustive --num-downscales 3

echo.
echo Islem tamamlandi!
