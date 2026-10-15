# Sistem Kurulum Notları ve Çözülen Kritik Hatalar

Bu belge, sistemin ilk kurulumunda karşılaşılan düşük seviyeli (low-level) derleyici ve ortam hatalarını, çözümlerini ve kalıcı yamalarını içerir.

---

## 1. Windows RPC `rpcndr.h` vs CUDA 11.8 CUB Çakışması

### Hata Tanımı:
`gsplat` C++ CUDA extension (`gsplat_cuda`) Windows üzerinde MSVC (Visual Studio 2022) ve CUDA 11.8 derleyicisi (nvcc) ile derlenirken şu hata ile derleme duruyordu:
```text
C:\Program Files (x86)\Windows Kits\10\Include\...\um\rpcndr.h(192): error: expected an identifier
#define small char
...
cub/device/dispatch/dispatch_segmented_sort.cuh(338): error C2059: syntax error: 'constant'
```

### Kök Neden:
Windows SDK başlık dosyası `rpcndr.h`, C-stili eski bir uyumluluk makrosu olarak `#define small char` tanımlamaktadır. Ancak NVIDIA CUB kütüphanesinde `small` ismi şablon ve değişken olarak kullanılmıştır. Windows makrosu CUB kodunu `char` olarak genişletip sözdizimi hatası oluşturmaktadır.

### Kalıcı Çözüm:
`gsplat/cuda/csrc` klasöründeki tüm 20 adet `.cu` ve `.cuh` dosyasının en üstüne şu koruma bloğu eklenmiştir:
```cpp
#ifdef small
#undef small
#endif
```
Ardından `gsplat_cuda.pyd` başarıyla derlenip `site-packages/` altına yerleştirilmiş ve `gsplat/cuda/_backend.py` doğrudan bu modülü import edecek şekilde yapılandırılmıştır.

---

## 2. Türkçe Windows Karakter Kodlaması (CP1254) Terminal Çökmesi

### Hata Tanımı:
Nerfstudio `train splatfacto` çalıştırıldığında `rich` kütüphanesi konsola durum tablosu çizerken:
```text
UnicodeEncodeError: 'charmap' codec can't encode characters in position ...: character maps to <undefined>
```

### Kök Neden:
Windows Türkçe bölge ayarlarında varsayılan konsol kodlaması `CP1254` (Windows-1254) olarak gelmekte ve Rich tablosundaki UTF-8 sınır çizgileri kodlanamamaktadır.

### Kalıcı Çözüm:
`nerfstudio/utils/rich_utils.py` modülü açılmış ve dosya başına şu satırlar eklenerek standart çıktı UTF-8'e zorlanmıştır:
```python
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
```

---

## 3. RTX 2060 (6 GB VRAM) Bellek Optimizasyonu

### Problem:
Gaussian Splatting eğitimi varsayılan ayarlarda tüm kareleri GPU belleğine (VRAM) yüklemeye çalışır. 12 MP (3024x4032) çözünürlükteki 63-79 fotoğraf 6 GB VRAM sınırını hızla aşarak `CUDA Out of Memory (OOM)` hatasına neden olur.

### Çözüm Parametreleri:
Eğitim komutuna şu optimize bayraklar eklenmiştir:
* `--pipeline.datamanager.cache-images cpu`: Görüntü tensörlerini sistem RAM'inde tutar, sadece o iterasyonda rasterize edilecek kareyi GPU'ya aktarır. VRAM kullanımını 6 GB altında tutar.
* `--pipeline.model.cull-alpha-thresh 0.1`: Opaklığı 0.1'in altına düşen gereksiz Gaussian'ları agresif biçimde temizler, böylece toplam Gaussian sayısı dengelenir.

---

## 4. tiny-cuda-nn Derlemesi (MSVC 14.44 + CUDA 11.8)

### Hata Tanımı:
`nerfacto` ve `instant-ngp` yöntemleri hash kodlaması için `tiny-cuda-nn`
kütüphanesini kullanır. Kurulu değilse nerfstudio yavaş PyTorch yedek yoluna
döner. Kaynaktan derleme iki ayrı hatayla durmaktadır:

```text
yvals_core.h(902): error: static assertion failed with
  "error STL1002: Unexpected compiler version, expected CUDA 12.4 or newer."

error C1128: bölüm sayısı nesne dosyası biçimi sınırını aştı: /bigobj ile derleyin
```

### Kök Neden:
1. **STL1002:** Visual Studio Build Tools 14.44'ün standart kütüphane başlıkları
   CUDA 12.4 veya üstünü şart koşar; projede CUDA 11.8 kullanılmaktadır. Reddeden,
   derleyicinin kendisi değil MSVC standart kütüphanesidir.
2. **C1128:** `tiny-cuda-nn` şablon yoğunluğu nedeniyle varsayılan COFF nesne
   dosyası bölüm sınırını aşmaktadır.

### Kalıcı Çözüm:
Derleme, `cl.exe`'nin her çağrısına bayrak ekleyen `CL` ortam değişkeniyle
yapılandırılır (tam betik: `scripts/install_tcnn.bat`):

```bat
call "...\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
set "TCNN_CUDA_ARCHITECTURES=75"
set "TORCH_CUDA_ARCH_LIST=7.5"
set "CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8"
set "DISTUTILS_USE_SDK=1"
set "CL=/D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH /bigobj"
python -m pip install --no-build-isolation ^
  "git+https://github.com/NVlabs/tiny-cuda-nn/#subdirectory=bindings/torch"
```

`_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH`, Microsoft'un kendi sağladığı kaçış
makrosudur ve STL1002 static_assert kontrolünü devre dışı bırakır.
`TCNN_CUDA_ARCHITECTURES=75`, RTX 2060'ın Turing mimarisine (compute capability
7.5) karşılık gelir.

### Ölçülen Etki (sinif-01, 331 kare, nerfacto):

| | tiny-cuda-nn yok | tiny-cuda-nn var |
| :--- | ---: | ---: |
| Adım süresi | 1.470 ms | **48 ms** |
| Tepe VRAM | 5.916 MB | **4.201 MB** |
| 15.000 iterasyon | 6 sa 7 dk (tahmini) | **~12 dk** |

Hızlanma yaklaşık **30 kattır**. Kütüphane kurulmadan NeRF tabanlı yöntemlerle
yapılan süre karşılaştırmaları geçerli sayılmamalıdır.
