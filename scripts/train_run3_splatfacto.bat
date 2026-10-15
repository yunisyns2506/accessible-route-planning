@echo off
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True"

echo =====================================================================
echo  Run 3: 512 Fotograf 3D Gaussian Splatting (Splatfacto) Egitimi
echo  476 Kamera, 75.6k 3D Nokta, Antialiased + Scale Regularization
echo =====================================================================
echo.
echo  >>> CANLI 3D GORUNTULEYICI: http://localhost:7007 <<<
echo  (Tarayicinizdan bu adrese girerek odanin 3D olusumunu izleyebilirsiniz!)
echo.
echo  Egitimi durdurmak isterseniz: Ctrl + C
echo =====================================================================
echo.

C:\Users\sabod\miniconda3\envs\nerfstudio\python.exe -m nerfstudio.scripts.train splatfacto --data data\oda-01_512foto\processed --output-dir runs\oda-01_512foto --experiment-name oda_run3 --max-num-iterations 30000 --steps-per-eval-image 2000 --steps-per-save 5000 --pipeline.model.random-init False --pipeline.model.rasterize-mode antialiased --pipeline.model.use-scale-regularization True --pipeline.model.max-gauss-ratio 5.0 --pipeline.model.densify-grad-thresh 0.0007 --pipeline.model.stop-split-at 15000 --pipeline.model.cull-alpha-thresh 0.006 --pipeline.model.sh-degree 2 --pipeline.model.camera-optimizer.mode SO3xR3 --pipeline.model.num-downscales 2 --pipeline.model.resolution-schedule 3000 --pipeline.datamanager.cache-images cpu --pipeline.datamanager.cache-images-type uint8 --viewer.quit-on-train-completion True nerfstudio-data --downscale-factor 4

pause
