@echo off
chcp 65001 >nul
set "PATH=C:\Users\sabod\tools\colmap;C:\Users\sabod\tools\ffmpeg;%PATH%"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

echo =====================================================================
echo  79 Oda Fotografi COLMAP ile Isleniyor (Exhaustive Matching)
echo =====================================================================
echo.

C:\Users\sabod\miniconda3\envs\nerfstudio\python.exe -m nerfstudio.scripts.process_data images --data data\oda-01_79foto\raw_images --output-dir data\oda-01_79foto\processed --matching-method exhaustive

echo.
echo Islem tamamlandi!
