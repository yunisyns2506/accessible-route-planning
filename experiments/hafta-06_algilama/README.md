# Hafta 6 – Kapı, merdiven ve asansör algılama

- Veri: sınıf ve koridor çekimlerinden 234 kare, CVAT'ta çokgenle etiketlendi (kapı 136, merdiven 31, asansör 13).
- Bölme: 15 karelik zaman blokları; eğitim 157, doğrulama 27, test 34 kare.
- Eğitim: Colab, NVIDIA L4 GPU; model başına 2,5–4,2 dk. Eşik doğrulamada seçildi, teste bir kez bakıldı (IoU ≥ 0,5).

| Model | Ort. F1 | mAP@0,5 | ms/kare (L4) |
|---|---|---|---|
| YOLO-World (eğitimsiz) | 0,06 | – | 9,4 |
| YOLOE-26s (eğitimsiz) | 0,25 | – | 11,9 |
| YOLO11n | 0,35 | 0,634 | 5,9 |
| YOLO26n-seg | 0,54 | 0,814 | 7,6 |
| YOLO26n | 0,69 | 0,835 | 5,6 |
| YOLOv8n | 0,72 | 0,823 | 5,7 |
| **YOLOv8n-seg** | **0,78** | **0,902** | 6,8 |

Ayrıntı: `sonuclar.csv`, `sonuclar.json`. Örnek tahmin: `tahmin_ornek.jpg`.

Modeller VR'da canlı çalıştırılmıyor: algılama bir kez çalıştırılıp sonuçlar (konum, genişlik) dosyaya yazılır, Unity bu dosyayı okur.

Eğitilen modeller ve etiketler Drive'da: [Hafta 6 Algılama](https://drive.google.com/drive/folders/1IO76-JB92Q5mGnD8MJS7cL-znsZ-HRJU?usp=drive_link)

Çalıştırma: `scripts/hafta06/algilama/Hafta6_Algilama.ipynb` (Colab).
