@echo off
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

echo =====================================================================
echo  Engelli Bireyler Icin Akilli Erisilebilir Rota Planlama
echo  Faz A2: 3D Gaussian Splat (.ply) Disa Aktarma (Export)
echo =====================================================================
echo.

C:\Users\sabod\miniconda3\envs\nerfstudio\python.exe export_ply.py

pause
