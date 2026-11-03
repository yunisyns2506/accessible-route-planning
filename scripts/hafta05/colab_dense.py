"""Derslik 4, LoMa + sequential + döngü + incremental modelinden COLMAP yoğun rekonstrüksiyonu.

Kullanım (Colab, L4):
    python -u colab_dense.py            # kaldığı yerden sürdürür

Adımlar (pycolmap-cuda12 4.2.1, COLMAP CLI varsayılanları; kareler küçültülmez, 1920x1080):
    undistort      kareleri bozulmadan arındırır
    patch_match    her kare için derinlik + normal haritası; geom_consistency açık
                   (önce bütün karelerde fotometrik geçiş, sonra geometrik geçiş)
    fusion         geometrik derinlikleri yoğun nokta bulutunda birleştirir
    poisson        yoğun buluttan su geçirmez yüzey
Delaunay yüzeyi yok: pip'teki pycolmap CGAL'siz derlendiği için delaunay_mesher içermiyor.
Colab'ın Ubuntu 24.04 / CUDA 13 ortamında Drive'daki eski COLMAP derlemesi yerine pycolmap kullanılır.

Her aşama için süre, tepe RAM ve tepe VRAM kaydedilir. PatchMatch sırasında
ilerleme.json dakikada bir güncellenir (biten harita sayısı, hız, tahmini bitiş).
Colab koparsa: derinlik/normal haritaları 10 dakikada bir Drive'a yedeklenir
(YEDEK=1); yeniden çalıştırınca geri yüklenir ve COLMAP var olan haritaları atlar.

Çıktı: /content/work/dense/loma_inc  →  Drive hafta5_derslik4/dense/loma_inc
"""
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import psutil

WORK = Path("/content/work")
FRAMES = WORK / "frames_1080"
SPARSE = WORK / "sfm" / "loma" / "sequential_loop" / "incremental" / "sparse" / "0"
WS = WORK / "dense" / "loma_inc"
DRIVE = Path("/content/drive/MyDrive/hafta5_derslik4/dense/loma_inc")
RES = WS / "dense.json"
PROGRESS = WS / "ilerleme.json"
BACKUP_MAPS = os.environ.get("YEDEK", "1") == "1"
SYNC_PERIOD_S = 600
MIN_FREE_RAM_MIB = 3000

# Her aşama ayrı bir Python sürecinde koşar (tepe RAM'i aşama başına ölçmek ve
# bellek bekçisinin yalnız o süreci durdurabilmesi için). Ayarlar COLMAP CLI
# varsayılanlarıyla aynı; num_patch_match_src_images CLI'deki gibi 20.
_IMPORT = f"import pycolmap; from pathlib import Path; WS = Path('{WS}'); "
PY_STAGES = {
    "undistort": _IMPORT + (
        f"pycolmap.undistort_images(WS, '{SPARSE}', '{FRAMES}', output_type='COLMAP', "
        "num_patch_match_src_images=20)"),
    "patch_match": _IMPORT + (
        "o = pycolmap.PatchMatchOptions(); o.geom_consistency = True; print(o, flush=True); "
        "pycolmap.patch_match_stereo(WS, workspace_format='COLMAP', options=o)"),
    "fusion": _IMPORT + (
        "o = pycolmap.StereoFusionOptions(); print(o, flush=True); "
        "pycolmap.stereo_fusion(WS / 'fused.ply', WS, workspace_format='COLMAP', "
        "input_type='geometric', options=o, output_type='ply')"),
    "poisson": _IMPORT + (
        "pycolmap.poisson_meshing(WS / 'fused.ply', WS / 'meshed-poisson.ply')"),
}


def tool_env() -> dict:
    """ONNX Runtime (CUDA 12) için pip'teki nvidia-*-cu12 kütüphanelerini yola ekler."""
    env = dict(os.environ)
    import site
    libs = []
    for sp in site.getsitepackages():
        nv = Path(sp) / "nvidia"
        if nv.is_dir():
            libs += [str(d / "lib") for d in sorted(nv.iterdir()) if (d / "lib").is_dir()]
    env["LD_LIBRARY_PATH"] = ":".join(libs + [env.get("LD_LIBRARY_PATH", "")])
    return env


def gpu_mem_used():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used",
                              "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10)
        return int(out.stdout.strip().split("\n")[0])
    except Exception:
        return None


class ResourceMonitor:
    """Süreç ağacının tepe RAM'ini ve GPU'nun tepe VRAM'ini örnekler.

    guard=True ise kullanılabilir RAM MIN_FREE_RAM_MIB altına inince süreci durdurur
    (Colab VM'nin bellek taşmasıyla çökmesini önler).
    """

    def __init__(self, interval: float = 2.0, guard: bool = False):
        self.interval, self.guard, self.vram_base = interval, guard, gpu_mem_used()
        self.vram_peak = self.rss_peak = 0
        self.killed_for_ram = False
        self._stop, self._pid = threading.Event(), None

    def _loop(self):
        while not self._stop.is_set():
            v = gpu_mem_used()
            if v is not None:
                self.vram_peak = max(self.vram_peak, v)
            try:
                p = psutil.Process(self._pid)
                rss = sum(q.memory_info().rss for q in [p] + p.children(recursive=True))
                self.rss_peak = max(self.rss_peak, rss)
                if self.guard and psutil.virtual_memory().available < MIN_FREE_RAM_MIB * 2**20:
                    self.killed_for_ram = True
                    p.kill()
            except psutil.Error:
                pass
            self._stop.wait(self.interval)

    def run(self, cmd: list, log: Path) -> tuple[int, float]:
        log.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        with open(log, "a") as f:
            f.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')}\n" + " ".join(map(str, cmd)) + "\n\n")
            f.flush()
            proc = subprocess.Popen(list(map(str, cmd)), env=tool_env(), stdout=f,
                                    stderr=subprocess.STDOUT)
            self._pid = proc.pid
            th = threading.Thread(target=self._loop, daemon=True)
            th.start()
            rc = proc.wait()
        sec = time.time() - t0
        self._stop.set()
        th.join(timeout=15)
        return rc, sec

    def summary(self) -> dict:
        return {"peak_ram_mib": round(self.rss_peak / 2**20),
                "peak_vram_mib": self.vram_peak or None, "vram_base_mib": self.vram_base}


def read_json(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def write_json(p: Path, d: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def ply_counts(path: Path) -> dict:
    """PLY başlığından köşe ve yüz sayısını okur."""
    out = {}
    if not path.exists():
        return out
    with open(path, "rb") as f:
        for raw in f:
            line = raw.decode("ascii", errors="replace").strip()
            if line.startswith("element vertex"):
                out["vertices"] = int(line.split()[-1])
            elif line.startswith("element face"):
                out["faces"] = int(line.split()[-1])
            elif line == "end_header":
                break
    out["size_mib"] = round(path.stat().st_size / 2**20, 1)
    return out


def sync_drive(maps: bool) -> None:
    """Sonuçları (json, log, ply) ve istenirse derinlik/normal haritalarını Drive'a kopyalar.

    Haritalardan yalnız 1 dakikadır değişmeyenler kopyalanır; yazılmakta olan
    yarım bir dosya yedeğe girmez.
    """
    if not Path("/content/drive/MyDrive").is_dir():
        return
    DRIVE.mkdir(parents=True, exist_ok=True)
    subprocess.run(["rsync", "-a", "--include", "*.json", "--include", "*.log",
                    "--include", "*.ply", "--include", "*.vis", "--exclude", "*",
                    f"{WS}/", f"{DRIVE}/"], check=False)
    if maps and (WS / "stereo").is_dir():
        found = subprocess.run(
            ["find", "depth_maps", "normal_maps", "-type", "f", "-mmin", "+1"],
            cwd=WS / "stereo", capture_output=True, text=True).stdout
        lst = WS / "yedek_liste.txt"
        lst.write_text(found)
        subprocess.run(["rsync", "-a", "--files-from", lst, f"{WS}/stereo/",
                        f"{DRIVE}/stereo/"], check=False)


def restore_drive() -> None:
    """Önceki koşunun yedeğini (sonuçlar + haritalar) yerel çalışma alanına geri yükler."""
    if DRIVE.is_dir():
        print("Drive yedeği geri yükleniyor ...", flush=True)
        subprocess.run(["rsync", "-a", "--exclude", "yedek_liste.txt", f"{DRIVE}/", f"{WS}/"],
                       check=False)


def count_maps() -> tuple[int, int]:
    d = WS / "stereo" / "depth_maps"
    if not d.is_dir():
        return 0, 0
    names = os.listdir(d)
    return (sum(n.endswith(".photometric.bin") for n in names),
            sum(n.endswith(".geometric.bin") for n in names))


def progress_loop(stop: threading.Event, n_images: int) -> None:
    """PatchMatch ilerlemesini dakikada bir yazar, 10 dakikada bir Drive'a yedekler."""
    total = 2 * n_images
    p0, g0 = count_maps()
    t0, last_sync = time.time(), time.time()
    while not stop.wait(60):
        p, g = count_maps()
        done, elapsed = p + g, time.time() - t0
        rate = (done - p0 - g0) / elapsed if elapsed > 0 else 0  # harita / sn, bu oturumda
        left_s = (total - done) / rate if rate > 0 else None
        write_json(PROGRESS, {
            "zaman": time.strftime("%H:%M:%S"),
            "fotometrik": f"{p} / {n_images}", "geometrik": f"{g} / {n_images}",
            "yuzde": round(100 * done / total, 1),
            "sn_per_harita": round(1 / rate, 1) if rate > 0 else None,
            "kalan_sa": round(left_s / 3600, 2) if left_s else None,
            "tahmini_bitis_tr": time.strftime("%d.%m %H:%M", time.gmtime(time.time() + left_s + 3 * 3600))
            if left_s else None,
        })
        if time.time() - last_sync >= SYNC_PERIOD_S:
            sync_drive(BACKUP_MAPS)
            last_sync = time.time()


def main() -> int:
    restore_drive()
    n_images = sum(1 for _ in FRAMES.glob("*.jpg"))
    res = read_json(RES) or {"run": "loma_sequential_loop_incremental",
                             "max_image_size": "tam (1920x1080)", "arac": "pycolmap-cuda12 4.2.1",
                             "geom_consistency": True, "input_images": n_images}
    stages = [(s, [sys.executable, "-u", "-c", PY_STAGES[s]]) for s in PY_STAGES]
    # Yeni bir VM'de bozulmadan arındırılmış kareler yoktur (Drive'a yedeklenmez);
    # undistort hızlı ve deterministik olduğu için yeniden koşulur, haritalara dokunmaz.
    if sum(1 for _ in (WS / "images").glob("*.jpg")) < n_images:
        res.pop("undistort", None)
    for stage, cmd in stages:
        if res.get(stage, {}).get("return_code") == 0:
            print(f"  atlandı (tamam): {stage}", flush=True)
            continue
        print(f"[{time.strftime('%H:%M:%S')}] {stage} başladı", flush=True)
        stop = threading.Event()
        if stage == "patch_match":
            threading.Thread(target=progress_loop, args=(stop, n_images), daemon=True).start()
        mon = ResourceMonitor(guard=stage in ("fusion", "poisson"))
        rc, sec = mon.run(cmd, WS / f"{stage}.log")
        stop.set()
        prev = res.get(stage, {})
        res[stage] = {"return_code": rc,
                      # sürdürülen koşuda önceki oturumların süresi de eklenir
                      "elapsed_min": round(prev.get("elapsed_min", 0) + sec / 60, 2),
                      "sessions": prev.get("sessions", 0) + 1, **mon.summary()}
        if mon.killed_for_ram:
            res[stage]["note"] = f"kullanılabilir RAM {MIN_FREE_RAM_MIB} MiB altına indi, durduruldu"
        write_json(RES, res)
        print(f"  rc={rc} {sec / 60:.1f} dk  RAM {res[stage]['peak_ram_mib']} MiB  "
              f"VRAM {res[stage]['peak_vram_mib']} MiB", flush=True)
        if stage == "patch_match":
            sync_drive(BACKUP_MAPS)
        else:
            sync_drive(False)
        if rc != 0:
            print(f"AŞAMA BAŞARISIZ: {stage}, log: {WS / (stage + '.log')}", flush=True)
            return 1
    res["fused"] = ply_counts(WS / "fused.ply")
    res.setdefault("poisson", {})["mesh"] = ply_counts(WS / "meshed-poisson.ply")
    res["total_min"] = round(sum(res[s].get("elapsed_min", 0) for s, _ in stages), 2)
    write_json(RES, res)
    sync_drive(False)
    print(f"BİTTİ: yoğun nokta {res['fused'].get('vertices')}, Poisson yüz "
          f"{res['poisson']['mesh'].get('faces')}, toplam {res['total_min']} dk", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
