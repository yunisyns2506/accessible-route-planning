@echo off
chcp 65001 >nul
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
set "TCNN_CUDA_ARCHITECTURES=75"
set "CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8"
set "CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8"
set "DISTUTILS_USE_SDK=1"
set "TORCH_CUDA_ARCH_LIST=7.5"
set "NVCC_APPEND_FLAGS=-allow-unsupported-compiler"
set "MAX_JOBS=4"
REM MSVC 14.44 STL basliklari CUDA 12.4+ bekliyor; CUDA 11.8 ile derlemek icin
REM Microsoft'un kendi kacis makrosu kullanilir (STL1002 static_assert'i kapatir).
set "CL=/D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH /bigobj"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
C:\Users\sabod\miniconda3\envs\nerfstudio\python.exe -m pip install -v --no-build-isolation "git+https://github.com/NVlabs/tiny-cuda-nn/#subdirectory=bindings/torch"
echo === pip cikis kodu: %ERRORLEVEL% ===
