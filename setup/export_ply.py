import os
import sys
import subprocess
from pathlib import Path

def export_latest_ply(outputs_base="outputs-photos/processed/splatfacto", export_dir="exports-photos"):
    outputs_path = Path(outputs_base)
    if not outputs_path.exists():
        print(f"Hata: {outputs_path} klasörü bulunamadı.")
        return 1

    runs = sorted([d for d in outputs_path.iterdir() if d.is_dir()])
    if not runs:
        print("Kayıtlı model eğitimi bulunamadı.")
        return 1

    latest_config = runs[-1] / "config.yml"
    print(f"Kullanılan yapılandırma: {latest_config}")

    out_path = Path(export_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "nerfstudio.scripts.exporter",
        "gaussian-splat",
        "--load-config",
        str(latest_config),
        "--output-dir",
        str(out_path),
    ]

    print("Komut çalıştırılıyor:", " ".join(cmd))
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print(f"\n[BAŞARILI] PLY modeli oluşturuldu: {out_path / 'splat.ply'}")
    else:
        print(f"\n[HATA] Çıkış kodu: {res.returncode}")
    return res.returncode

if __name__ == "__main__":
    sys.exit(export_latest_ply())
