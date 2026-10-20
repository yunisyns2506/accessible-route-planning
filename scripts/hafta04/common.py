"""Hafta 4 betiklerinin ortak ayarlari: yollar, ortam ve kaynak olcumu.

Tum koşular ayni araclari ve ayni ortam degiskenlerini buradan alir; boylece
SIFT / ALIKED / LoMa bloklari ayni kosullarda calisir.
"""
import json
import os
import subprocess
import threading
import time
from pathlib import Path

import psutil

REPO = Path(__file__).resolve().parents[2]
PYTHON = r"C:\Users\sabod\miniconda3\envs\nerfstudio\python.exe"

COLMAP_DIR = Path(r"C:\Users\sabod\tools\colmap-4.2.1")
COLMAP = str(COLMAP_DIR / "bin" / "colmap.exe")
MODELS = COLMAP_DIR / "models"
# ONNX Runtime (ALIKED, LightGlue, LoMa) CUDA 12 + cuDNN 9.10 ister; sistemdeki
# CUDA 11.8'e dokunmamak icin ayri klasorde tutulur. cuDNN 9.27 Turing'de
# (SM 7.5) evrisim motoru bulamadigi icin 9.10 kullanilir.
CUDA12 = Path(r"C:\Users\sabod\tools\cuda12-runtime\nvidia")

# pycolmap 4.2.1 (yalnizca LoMa sozluk agaci icin), nerfstudio ortamindan ayri
PYCOLMAP = r"C:\Users\sabod\tools\pycolmap-4.2.1"

FRAMES = REPO / "data" / "sinif-01" / "frames_1fps"
WORK = REPO / "data" / "sinif-01" / "hafta-04"
RUNS = REPO / "runs" / "sinif-01" / "hafta-04"
EXP = REPO / "experiments" / "hafta-04_sinif-01"


def tool_env() -> dict:
    env = dict(os.environ)
    dll_dirs = [str(COLMAP_DIR / "bin")] + [str(d / "bin") for d in sorted(CUDA12.iterdir())
                                            if (d / "bin").is_dir()]
    env["PATH"] = os.pathsep.join(dll_dirs + [env.get("PATH", "")])
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def gpu_mem_used() -> int | None:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used",
                              "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10)
        return int(out.stdout.strip().split("\n")[0])
    except Exception:
        return None


class ResourceMonitor:
    """Bir surec agacinin tepe RAM'ini ve GPU'nun tepe VRAM'ini orneklemeyle olcer.

    VRAM, nvidia-smi'nin tum GPU icin verdigi degerdir; koşu oncesi taban deger
    (masaustu vb.) ayrica kaydedilir, net kullanim = tepe - taban.
    """

    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.vram_base = gpu_mem_used()
        self.vram_peak = 0
        self.rss_peak = 0
        self.samples = 0
        self._stop = threading.Event()
        self._pid = None

    def _tree_rss(self) -> int:
        try:
            p = psutil.Process(self._pid)
            procs = [p] + p.children(recursive=True)
        except psutil.Error:
            return 0
        total = 0
        for q in procs:
            try:
                total += q.memory_info().rss
            except psutil.Error:
                pass
        return total

    def _loop(self):
        while not self._stop.is_set():
            v = gpu_mem_used()
            if v is not None:
                self.vram_peak = max(self.vram_peak, v)
            if self._pid:
                self.rss_peak = max(self.rss_peak, self._tree_rss())
            self.samples += 1
            self._stop.wait(self.interval)

    def run(self, cmd: list, log_path: Path, env: dict | None = None) -> tuple[int, float]:
        """Komutu calistirir, ciktiyi log'a yazar; (donus kodu, sure sn) dondurur."""
        log_path.parent.mkdir(parents=True, exist_ok=True)
        th = threading.Thread(target=self._loop, daemon=True)
        t0 = time.time()
        with open(log_path, "w", encoding="utf-8", errors="replace") as log:
            log.write(" ".join(map(str, cmd)) + "\n\n")
            log.flush()
            proc = subprocess.Popen(cmd, env=env or tool_env(), stdout=log,
                                    stderr=subprocess.STDOUT, text=True)
            self._pid = proc.pid
            th.start()
            rc = proc.wait()
        elapsed = time.time() - t0
        self._stop.set()
        th.join(timeout=15)
        return rc, elapsed

    def summary(self) -> dict:
        return {
            "peak_ram_mib": round(self.rss_peak / 2**20),
            "peak_vram_mib": self.vram_peak or None,
            "vram_base_mib": self.vram_base,
            "net_vram_mib": (self.vram_peak - self.vram_base
                             if self.vram_peak and self.vram_base is not None else None),
            "samples": self.samples,
        }


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def read_json(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
