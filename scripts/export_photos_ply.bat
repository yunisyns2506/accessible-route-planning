@echo off
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

echo =====================================================================
echo  Fotoğraf Modeli 3D Gaussian Splatting (.ply) Dışa Aktarma
echo =====================================================================
echo.

C:\Users\sabod\miniconda3\envs\nerfstudio\python.exe export_photos_ply.py

echo.
pause
