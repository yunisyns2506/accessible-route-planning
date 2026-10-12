import os
import sys
from pathlib import Path
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

def convert_heic_to_jpg(input_dir, output_dir):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    heic_files = sorted(list(input_path.glob("*.heic")) + list(input_path.glob("*.HEIC")))
    print(f"Toplam {len(heic_files)} HEIC dosya bulundu: {input_path}")

    for idx, f in enumerate(heic_files, start=1):
        try:
            img = Image.open(f)
            # EXIF Orientation duzeltmesi
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
            
            target_name = f"frame_{idx:05d}.jpg"
            target_file = output_path / target_name
            img.save(target_file, "JPEG", quality=95)
            print(f"[{idx}/{len(heic_files)}] {f.name} -> {target_name} ({img.size})")
        except Exception as e:
            print(f"HATA: {f.name} dönüştürülemedi: {e}")

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "yeni_fotograflar"
    dst = sys.argv[2] if len(sys.argv) > 2 else "data/room-01-photos/raw_images"
    convert_heic_to_jpg(src, dst)
