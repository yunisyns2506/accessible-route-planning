# Deney Ortami (Hafta 3 - sinif-01 kosulari)

Uc SfM ve yedi egitim kosusunun tamami ayni makinede, ayni ortamda calistirildi.

| Bilesen | Deger |
| :--- | :--- |
| Isletim sistemi | Windows 11 Pro 64-bit |
| GPU | NVIDIA GeForce RTX 2060, 6 GB GDDR6, CC 7.5 (Turing) |
| RAM | 16 GB DDR4 |
| Python | 3.10.13 (conda ortami: `nerfstudio`) |
| PyTorch | 2.1.2+cu118 |
| CUDA Toolkit | 11.8 (V11.8.89) |
| Nerfstudio | 1.0.3 |
| gsplat | 0.1.4 (yerel yamali derleme, bkz. `setup/kurulum_notlari.md`) |
| tiny-cuda-nn | kaynaktan derlendi, SM 75 (bkz. `setup/kurulum_notlari.md` B.4) |
| COLMAP | 3.9.1 (CUDA) |
| FFmpeg | 6.1+ |

Kurulum sirasinda cozulen derleyici/kodlama hatalari `setup/kurulum_notlari.md`
dosyasinda kayitlidir. `tiny-cuda-nn` nerfacto (NeRF) kosusu icin kurulmustur;
kurulmadan once adim suresi 1.470 ms, kurulduktan sonra 48 ms olculmustur.

Unity aktarimi (A2) bu hafta yapilmadi; Unity surumu
`environment/dependencies.md` dosyasinda planlanan surum olarak yazilidir,
dogrulanmis aktarim kaydi yoktur.
