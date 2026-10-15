@echo off
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

echo =====================================================================
echo  Engelli Bireyler Icin Akilli Erisilebilir Rota Planlama
echo  Faz A1: 3D Gaussian Splatting (Splatfacto) - 63 Fotograf Egitimi
echo =====================================================================
echo.
echo  Veri Seti: data\oda-01_79foto\processed (63 Kamera Karesi, 18.5k 3D Nokta)
echo  Hedef Iterasyon: 30,000
echo  VRAM Tasarrufu: CPU Image Caching aktif (RTX 2060 6GB optimize)
echo.
echo  >>> CANLI 3D GORUNTULEYICI: http://localhost:7007 <<<
echo  (Egitim basladiktan sonra tarayicinizdan bu adrese girerek
echo   odanin 3D olusumunu adim adim canli izleyebilirsiniz!)
echo.
echo  Egitimi durdurmak isterseniz: Ctrl + C
echo =====================================================================
echo.

C:\Users\sabod\miniconda3\envs\nerfstudio\python.exe -m nerfstudio.scripts.train splatfacto --data data\oda-01_79foto\processed --output-dir runs\oda-01_79foto --pipeline.datamanager.cache-images cpu --pipeline.model.cull-alpha-thresh 0.1 --max-num-iterations 30000

pause
