"""What this machine is and what it serves, read locally. No UI code here: the Streamlit and Flet pages both use it.

- machine(): CPU, logical cores, RAM, GPUs with their memory. Read once per process.
- machine_lines(): the same as short lines for a side panel.
- wifi_state(): "connected", "disconnected" or "unknown" (Windows only; "unknown" elsewhere).
- lm_models(url): model ids an OpenAI-compatible server on this machine reports, or None when it is not running.
"""

import json
import os
import platform
import re
import subprocess
import urllib.request
from typing import List, Optional

from . import config


def _ps(command: str, timeout: float = 15.0) -> str:
    try:
        return subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True,
                              timeout=timeout).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


_MACHINE: Optional[dict] = None


def machine() -> dict:
    """CPU, logical cores, RAM in GB, GPUs with their memory in GB. Read once per process, locally."""
    global _MACHINE
    if _MACHINE is not None:
        return _MACHINE
    info = {"os": platform.system() + " " + platform.release(), "cpu": platform.processor(), "cores": os.cpu_count(),
            "ram_gb": None, "gpus": []}
    try:
        import psutil

        info["ram_gb"] = round(psutil.virtual_memory().total / 2 ** 30, 1)
    except ImportError:
        pass
    if platform.system() == "Windows":
        out = _ps("$c=(Get-CimInstance Win32_Processor).Name; $g=Get-CimInstance Win32_VideoController | "
                  "Select-Object Name,AdapterRAM; @{cpu=$c; gpus=$g} | ConvertTo-Json -Compress")
        try:
            data = json.loads(out)
            info["cpu"] = (data.get("cpu") or info["cpu"]).strip()
            gpus = data.get("gpus") or []
            gpus = gpus if isinstance(gpus, list) else [gpus]
            info["gpus"] = [{"name": g.get("Name", "").strip(),
                             "memory_gb": round((g.get("AdapterRAM") or 0) / 2 ** 30, 1)} for g in gpus]
        except ValueError:
            pass
    _MACHINE = info
    return info


def machine_lines(info: dict) -> List[str]:
    """The machine panel as plain lines (also used by the tests)."""
    lines = ["%s, %s logical cores" % (info.get("cpu") or "CPU", info.get("cores") or "?")]
    if info.get("ram_gb"):
        lines.append("%s GB RAM" % info["ram_gb"])
    for g in info.get("gpus") or []:
        mem = " (%s GB)" % g["memory_gb"] if g.get("memory_gb") else ""
        lines.append("GPU: %s%s" % (g["name"], mem))
    return lines


def wifi_state() -> str:
    """connected, disconnected or unknown. Local command only; works with the Wi-Fi switched off."""
    if platform.system() != "Windows":
        return "unknown"
    try:
        out = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    states = re.findall(r"^\s*State\s*:\s*(\w+)", out, flags=re.M)
    if not states:
        return "unknown"
    return "connected" if any(s.lower() == "connected" for s in states) else "disconnected"


def lm_models(url: str = config.LLM_URL) -> Optional[List[str]]:
    """Model ids an OpenAI-compatible server on this machine serves, or None when it is not running."""
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/models", timeout=3) as r:
            return [m["id"] for m in json.load(r).get("data", [])]
    except Exception:
        return None
