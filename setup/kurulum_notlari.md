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
