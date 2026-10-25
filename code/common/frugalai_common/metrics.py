"""Host description and peak-RAM sampling for benchmarks."""

import platform
import subprocess
import threading
from typing import Iterable, Optional

import psutil

# Process-name fragments of the inference engines (lower case). The LM Studio desktop app itself is
# deliberately not matched: its window process is not the model, and counting it inflates RAM
# compared with a headless Ollama or llama-server run. The engine under LM Studio is llama-server.
DEFAULT_HINTS = ("ollama", "llama")


def detect_gpus(timeout_s: float = 5.0) -> str:
    """NVIDIA GPUs present on this machine (name and memory), joined by '; ', else 'none detected'.

    This says a GPU EXISTS, not that the inference engine used it: runtimes such as LM Studio offload model
    layers to a GPU by default. For a CPU-only claim, turn GPU offload off in the runtime and say so. Only
    NVIDIA GPUs are detected (through nvidia-smi); an AMD or Intel graphics chip would show 'none detected'.
    """
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=timeout_s, check=True,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return "none detected"
    names = [line.strip() for line in out.splitlines() if line.strip()]
    return "; ".join(names) or "none detected"


def os_label() -> str:
    """platform.platform(), except that Windows 11 is named as such.

    Python (before 3.12 at least) reports Windows 11 as "Windows-10-10.0.2xxxx" because the kernel version stays
    10.0. A build number of 22000 or more is Windows 11, so the label says so and keeps the build number.
    """
    label = platform.platform()
    if platform.system() == "Windows":
        try:
            build = int(platform.version().split(".")[-1])
        except ValueError:
            return label
        if build >= 22000 and label.startswith("Windows-10-"):
            label = "Windows-11-" + label[len("Windows-10-"):]
    return label


def host_info() -> dict:
    """Facts that make a benchmark row reproducible. Numbers only, no personal data."""
    freq = psutil.cpu_freq()
    return {
        "os": os_label(),
        "cpu": platform.processor() or platform.machine(),
        "cores_physical": psutil.cpu_count(logical=False),
        "cores_logical": psutil.cpu_count(logical=True),
        "cpu_max_mhz": round(freq.max) if freq and freq.max else None,
        "gpu": detect_gpus(),
        "ram_total_mb": round(psutil.virtual_memory().total / 1e6),
        "python": platform.python_version(),
    }


class PeakRam:
    """Context manager: peak resident memory of runtime processes while a block runs.

    Samples the summed RSS of processes whose name contains one of `hints`. This measures the
    runtime that holds the model, not our own Python process. If no process matches, peak_mb is None
    and the caller should say so instead of reporting zero.
    """

    def __init__(self, hints: Iterable[str] = DEFAULT_HINTS, interval_s: float = 0.2):
        self.hints = tuple(h.lower() for h in hints)
        self.interval_s = interval_s
        self.peak_mb: Optional[float] = None
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _sample(self) -> Optional[float]:
        total = 0
        found = False
        for proc in psutil.process_iter(["name", "memory_info"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if any(h in name for h in self.hints):
                    total += proc.info["memory_info"].rss
                    found = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return total / 1e6 if found else None

    def _run(self):
        while not self._stop.is_set():
            value = self._sample()
            if value is not None and (self.peak_mb is None or value > self.peak_mb):
                self.peak_mb = value
            self._stop.wait(self.interval_s)

    def __enter__(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        final = self._sample()
        if final is not None and (self.peak_mb is None or final > self.peak_mb):
            self.peak_mb = final
        return False
