# COLMAP 4.2.1 Kurulumu (Hafta 4 yöntem karşılaştırması)

Hafta 4'te SIFT, ALIKED ve LoMa özellik çıkarıcıları; exhaustive, sequential ve
vocab_tree eşleştirmesi; incremental, global ve hierarchical SfM aynı ortamda
karşılaştırılır. ALIKED, LightGlue, LoMa ve dahili global mapper COLMAP 3.9.1'de
olmadığı için COLMAP **4.2.1** ayrı bir klasöre kurulmuştur. Hafta 3 sonuçlarının
tekrarlanabilmesi için 3.9.1 (`tools\colmap`) olduğu gibi bırakılmıştır.

## Klasör düzeni

```text
C:\Users\<user>\tools\
  colmap\                 COLMAP 3.9.1 CUDA (hafta 3, dokunulmadı)
  colmap-4.2.1\           COLMAP 4.2.1 CUDA (hafta 4)
    bin\colmap.exe
    models\               ONNX modelleri ve sözlük ağaçları (SHA256 doğrulandı)
  cuda12-runtime\         ONNX Runtime için CUDA 12 + cuDNN 9.10 DLL'leri
    nvidia\<paket>\bin\
```

Betikler (`scripts/hafta04/common.py`) PATH'i yalnızca kendi süreçleri için
ayarlar; sistem PATH'i ve CUDA 11.8 kurulumu değiştirilmez.

## Adımlar

### 1. COLMAP 4.2.1 CUDA

```bash
curl -L -o colmap-x64-windows-cuda.zip https://github.com/colmap/colmap/releases/download/4.2.1/colmap-x64-windows-cuda.zip
```

Zip, `tools\colmap-4.2.1` klasörüne açılır. Doğrulama:

```bash
C:\Users\<user>\tools\colmap-4.2.1\bin\colmap.exe version
# COLMAP 4.2.1 (Commit bd1fcf6 on 2026-09-29 with CUDA, boost hash maps)
```

### 2. CUDA 12 çalışma kütüphaneleri (ALIKED / LightGlue / LoMa için)

COLMAP'in öğrenme tabanlı yöntemleri ONNX Runtime 1.30 ile çalışır ve CUDA 12
kütüphanelerini ister (`cublasLt64_12.dll` vb.). Sistemde CUDA 11.8 olduğu için
bunlar pip tekerleklerinden ayrı bir klasöre kurulur:

```bash
python -m pip install --target C:/Users/<user>/tools/cuda12-runtime --only-binary=:all: "nvidia-cublas-cu12==12.*" "nvidia-cuda-runtime-cu12==12.*" "nvidia-cufft-cu12==11.*" "nvidia-curand-cu12==10.*" "nvidia-cuda-nvrtc-cu12==12.*" "nvidia-cudnn-cu12==9.10.*"
```

> **cuDNN sürümü önemlidir.** cuDNN 9.27 ile ALIKED, RTX 2060'ta (Turing, SM 7.5)
> `CUDNN_FE failure 8: HEURISTIC_QUERY_FAILED` hatasıyla durdu. cuDNN **9.10.2**
> ile sorunsuz çalıştı.

Kurulan sürümler: cuBLAS 12.9.2, CUDA runtime 12.9.79, cuFFT 11.4.1, cuRAND
10.3.10, NVRTC 12.9.86, cuDNN 9.10.2.

### 3. ONNX modelleri ve sözlük ağaçları

COLMAP bu modelleri ilk kullanımda kendisi indirebilir. Tekrarlanabilirlik için
`tools\colmap-4.2.1\models\` klasörüne önceden indirilmiş ve COLMAP'in kendi
varsayılan ayarlarında yazan SHA256 değerleriyle doğrulanmıştır:

| Dosya | Kullanım | Kaynak |
| :--- | :--- | :--- |
| `aliked-n16rot.onnx` | ALIKED çıkarıcı | colmap/colmap 3.13.0 sürümü |
| `aliked-lightglue.onnx` | ALIKED + LightGlue eşleştirici | colmap/colmap 3.13.0 |
| `loma_detector.onnx` | LoMa anahtar nokta | davnords/storage (COLMAP varsayılanı) |
| `loma_descriptor_dedode_g.onnx` | LoMa tanımlayıcı (LOMA_B, 1,3 GB) | davnords/storage |
| `loma_matcher_B.onnx` | LoMa eşleştirici (LOMA_B) | davnords/storage |
| `vocab_tree_faiss_flickr100K_words32K.bin` | SIFT vocab_tree | colmap/colmap 3.11.1 |
| `vocab_tree_faiss_flickr100K_words64K_aliked_n16rot.bin` | ALIKED vocab_tree | colmap/colmap 3.13.0 |

LoMa için resmi sözlük ağacı yoktur. COLMAP 4.2.1'in `vocab_tree_builder`
komutu dizini sabit olarak 128 boyutlu tanımlayıcı için kurar; LoMa (LOMA_B) 256
boyutlu olduğundan komut çöker (0xC0000409). `scripts/hafta04/build_vocab_tree.py`
aynı dizini pycolmap 4.2.1 ile doğru boyutta kurar (pycolmap, nerfstudio
ortamını bozmamak için `tools\pycolmap-4.2.1` klasörüne `pip install --target`
ile kuruldu). Ancak k-ortalamalar bu kurulumda tek çekirdekte çalıştı ve 714.752
tanımlayıcı için 65.536 sözcükle 13 dk, 8.192 sözcükle 67 dk içinde
tamamlanmadı; hafta 4'te süre sınırı nedeniyle durduruldu.

## Bilinen sınırlar (RTX 2060, 6 GB)

* LoMa (LOMA_B) çıkarma: kare başına ~18 sn, tepe VRAM ~5,8 GB.
* ALIKED çıkarma: tepe VRAM ~5,7 GB, tepe RAM ~5,3 GB.
* `hierarchical_mapper` varsayılan `leaf_max_num_images = 500` olduğundan 349
  karelik veri kümesinde sahneyi bölmez; incremental ile aynı işi yapar.
