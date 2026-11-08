"""Kesilirse kaldığı yerden süren 3DGS eğitimi (colab_gs.train'in sürdürmeli karşılığı).

07.11'de 1440p eğitim %46'dayken Colab sanal makinesi değişti ve her şey kayboldu: koşu Drive'a yalnız
sonda kopyalanıyordu. Burada kontrol noktası her 1000 adımda yerelde yazılır, 10 dakikada bir Drive'a
kopyalanır (yalnız en sonuncusu tutulur). Yeniden çalıştırılınca Drive'daki son kontrol noktasından sürer.
Sürdürmede nerfstudio'nun eğitim döngüsü (trainer.py) yamalıdır: kontrol noktası yüklenince Gaussian sayısı
değiştiği için iyileştiriciler yeni parametrelerle yeniden kurulur (hat_koridor.py yamalar, sürdürme testiyle denetler).

Kullanım (/content/ns/bin/python):
    egit_surdur.py <res> <yontem> <etiket> <drive_kok> [--extra "..."] [--bitir N] [--kayit 1000]
--bitir N: bu oturumda N. adımda dur (yalnız sürdürme testi için). Çıktı: runs/<koşu>/train_metrics.json,
summary.json, export/splat.ply; kontrol noktası <drive_kok>/ckpt/<koşu>/, durum <drive_kok>/ckpt/<koşu>/durum.json
"""
import argparse
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, "/content/work")
import colab_gs as g  # noqa: E402
from colab_sfm import ResourceMonitor, read_json, write_json  # noqa: E402

ITERS = 30000


def adim(p: Path) -> int:
    return int(re.search(r"step-(\d+)\.ckpt", p.name).group(1))


def son_ckpt(d: Path):
    c = sorted(d.rglob("step-*.ckpt"), key=adim)
    return c[-1] if c else None


def esitle(out: Path, ck: Path, dur: threading.Event, aralik: int = 600) -> None:
    """Yerel son kontrol noktasını ve eğitim günlüğünü Drive'a kopyalar; Drive'da yalnız son kontrol noktası kalır."""
    while True:
        p = son_ckpt(out)
        if p is not None and not (ck / p.name).exists():
            subprocess.run(["rsync", "-a", str(p), f"{ck}/"], check=False)
            if (ck / p.name).exists():
                for q in ck.glob("step-*.ckpt"):
                    if q.name != p.name:
                        q.unlink()
                d = read_json(ck / "durum.json") or {}
                write_json(ck / "durum.json", {**d, "son_adim": adim(p), "zaman": time.strftime("%F %T")})
        if (out / "train_log.txt").exists():
            shutil.copy(out / "train_log.txt", ck / "train_log_son.txt")
        if dur.wait(aralik):
            return


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("res")
    ap.add_argument("yontem")
    ap.add_argument("etiket")
    ap.add_argument("drive_kok", type=Path)
    ap.add_argument("--extra", default="")
    ap.add_argument("--bitir", type=int, default=ITERS)
    ap.add_argument("--kayit", type=int, default=1000)
    ap.add_argument("--aralik", type=int, default=600)
    a = ap.parse_args()
    run = g.make_data("loma", "sequential_loop", "incremental", a.res, a.yontem, a.etiket)
    out = g.RUNS / run
    ck = a.drive_kok / "ckpt" / run
    ck.mkdir(parents=True, exist_ok=True)
    tm = read_json(out / "train_metrics.json")
    if not (tm and tm.get("return_code") == 0 and tm.get("son_adim", ITERS - 1) >= ITERS - 1):
        durum = read_json(ck / "durum.json") or {}
        yukle, bas = [], 0
        p = son_ckpt(ck)
        if p is not None:
            yd = g.WORK / "ckpt_yukle" / run
            shutil.rmtree(yd, ignore_errors=True)
            yd.mkdir(parents=True)
            shutil.copy(p, yd / p.name)
            yukle, bas = ["--load-dir", str(yd)], adim(p) + 1
        n = min(ITERS, a.bitir) - bas
        if n <= 0:
            print(f"[{run}] yapılacak adım yok (son {bas - 1})", flush=True)
            return 0
        extra = a.extra.split()
        cmd = [g.PY, "-m", "nerfstudio.scripts.train", a.yontem,
               "--data", str(g.NS / run), "--output-dir", str(out), "--experiment-name", run,
               "--max-num-iterations", str(n), *yukle,
               "--steps-per-eval-image", "2000", "--steps-per-save", str(a.kayit),
               "--save-only-latest-checkpoint", "True",
               "--viewer.quit-on-train-completion", "True", "--vis", "tensorboard",
               "--pipeline.datamanager.cache-images", "cpu",
               *(["--pipeline.datamanager.cache-images-type", "uint8"] if a.res != "1080" else []),
               *extra, "nerfstudio-data", "--downscale-factor", "1"]
        print(f"[{run}] eğitim: adım {bas} → {bas + n - 1}" + (" (sürdürme)" if yukle else ""), flush=True)
        dur = threading.Event()
        t = threading.Thread(target=esitle, args=(out, ck, dur, a.aralik), daemon=True)
        t.start()
        mon = ResourceMonitor(interval=2.0)
        rc, sec = mon.run(cmd, out / "train_log.txt")
        dur.set()
        t.join()
        p = son_ckpt(out)
        if p is not None:  # son kontrol noktası hemen Drive'a
            subprocess.run(["rsync", "-a", str(p), f"{ck}/"], check=False)
            for q in ck.glob("step-*.ckpt"):
                if q.name != p.name:
                    q.unlink()
        s = mon.summary()
        oturumlar = durum.get("oturumlar", []) + [{"bas": bas, "son": bas + n - 1, "rc": rc, "dk": round(sec / 60, 2),
                                                   "peak_vram_mib": s["peak_vram_mib"], "peak_ram_mib": s["peak_ram_mib"]}]
        write_json(ck / "durum.json", {**durum, "son_adim": adim(p) if p else None, "oturumlar": oturumlar,
                                       "zaman": time.strftime("%F %T")})
        res = {"run": run, "method": a.yontem, "extra": extra, "iterations": ITERS, "return_code": rc,
               "son_adim": adim(p) if p else None, "oturumlar": oturumlar,
               "train_minutes": round(sum(o["dk"] for o in oturumlar), 2),
               "peak_vram_mib": max(o["peak_vram_mib"] or 0 for o in oturumlar),
               "peak_ram_mib": max(o["peak_ram_mib"] or 0 for o in oturumlar),
               "split": read_json(g.NS / run / "split.json")}
        write_json(out / "train_metrics.json", res)
        print(f"[{run}] oturum rc={rc} {sec / 60:.1f} dk, son adım {res['son_adim']}", flush=True)
        g.sync_drive(run)
        if rc != 0 or a.bitir < ITERS:
            return rc
    g.evaluate(run)
    g.export_ply(run)
    g.sync_drive(run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
