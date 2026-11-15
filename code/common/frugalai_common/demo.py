"""Shared pieces for the per-project Streamlit demo pages (code/<project>/app.py).

Nothing here imports Streamlit at module level, so the tests run without it.

- install_guard(): from then on, this Python process refuses every connection and name lookup that is not to this
  machine, and counts both kinds. Switching the Wi-Fi off is the visible proof; the counter is the second one.
- machine(): what this laptop is (CPU, cores, RAM, GPU and its memory), read locally once.
- wifi_state(): "connected", "disconnected" or "unknown", from `netsh wlan show interfaces` (Windows only).
- lm_models(): model ids LM Studio reports on localhost, or None when it is not running.
- sidebar(st, needs): the panel every page shows: machine, Wi-Fi, LM Studio models, connection counts.
"""

import ipaddress
import json
import os
import platform
import re
import socket
import subprocess
import threading
import urllib.request
from typing import Dict, List, Optional

from . import config

os.environ.setdefault("HF_HUB_OFFLINE", "1")                    # no Hugging Face lookups from any demo page
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

_LOCAL = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


# ------------------------------------------------------------------ offline guard (process-wide)
class Blocked(ConnectionError):
    pass


class Guard:
    def __init__(self):
        self.blocked: List[tuple] = []       # attempts to reach another machine (stopped)
        self.local = 0                       # connections to this machine (LM Studio, this page)
        self.active = False


GUARD = Guard()
_lock = threading.Lock()


def is_local(address) -> bool:
    host = str(address[0]) if isinstance(address, tuple) and address else str(address)
    return host in _LOCAL or host.startswith("127.")


def _is_ip_literal(host: str) -> bool:
    try:
        ipaddress.ip_address(str(host).split("%")[0])
        return True
    except ValueError:
        return False


def bind_problem(address) -> str:
    """Empty string when the Streamlit server is bound to this machine only, else the message to show."""
    return "" if str(address or "") in ("localhost", "127.0.0.1", "::1") else (
        "This page must be served on localhost only: streamlit run app.py --server.address localhost")


def install_guard(guard: Guard = GUARD) -> Guard:
    """Refuse every connect(), sendto() and name lookup to another machine for the rest of the process. Idempotent."""
    with _lock:
        if guard.active:
            return guard
        original, original_ex = socket.socket.connect, socket.socket.connect_ex
        original_sendto, original_getaddrinfo = socket.socket.sendto, socket.getaddrinfo

        def check(address) -> bool:
            if is_local(address):
                guard.local += 1
                return True
            guard.blocked.append((str(address[0]) if isinstance(address, tuple) else str(address),
                                  address[1] if isinstance(address, tuple) and len(address) > 1 else None))
            return False

        def connect(sock, address):
            if not check(address):
                raise Blocked("offline guard: blocked a connection to %s" % (address,))
            return original(sock, address)

        def connect_ex(sock, address):
            return original_ex(sock, address) if check(address) else 111

        def sendto(sock, data, *args):
            address = args[-1] if args else None   # sendto(data, address) or sendto(data, flags, address)
            if address is not None and not check(address):
                raise Blocked("offline guard: blocked a datagram to %s" % (address,))
            return original_sendto(sock, data, *args)

        def getaddrinfo(host, *args, **kwargs):
            name = host.decode("ascii", "replace") if isinstance(host, bytes) else host
            if name and not _is_ip_literal(name) and not is_local(name):   # literals are checked at connect
                guard.blocked.append((str(name), None))
                raise socket.gaierror("offline guard: blocked a name lookup for %s" % name)
            return original_getaddrinfo(host, *args, **kwargs)

        socket.socket.connect, socket.socket.connect_ex = connect, connect_ex
        socket.socket.sendto, socket.getaddrinfo = sendto, getaddrinfo
        guard.active = True
    return guard


# ------------------------------------------------------------------ this machine
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
    """Model ids LM Studio serves on this machine, or None when it is not running."""
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/models", timeout=3) as r:
            return [m["id"] for m in json.load(r).get("data", [])]
    except Exception:
        return None


def machine_lines(info: dict) -> List[str]:
    """The machine panel as plain lines (also used by the tests)."""
    lines = ["%s, %s logical cores" % (info.get("cpu") or "CPU", info.get("cores") or "?")]
    if info.get("ram_gb"):
        lines.append("%s GB RAM" % info["ram_gb"])
    for g in info.get("gpus") or []:
        mem = " (%s GB)" % g["memory_gb"] if g.get("memory_gb") else ""
        lines.append("GPU: %s%s" % (g["name"], mem))
    return lines


def sidebar(st, needs: Dict[str, str] = None, guard: Guard = GUARD, note: str = "") -> None:
    """The panel every demo page shows. `needs` maps a role (chat, embedding) to the model id the page uses."""
    sb = st.sidebar
    sb.markdown("### This machine")
    for line in machine_lines(machine()):
        sb.markdown("- " + line)
    wifi = wifi_state()
    sb.markdown("### Offline")
    sb.markdown("- Wi-Fi: **%s**" % wifi)
    sb.markdown("- Internet connections from this page: **%d blocked**, %d to this machine"
                % (len(guard.blocked), guard.local))
    models = lm_models()
    sb.markdown("### Models")
    if models is None:
        sb.markdown("- LM Studio: not running")
    else:
        for role, mid in (needs or {}).items():
            sb.markdown("- %s: `%s` %s" % (role, mid, "loaded" if mid in models else "**not loaded**"))
    if note:
        sb.caption(note)


PAGE_CSS = """<style>
#MainMenu, header, footer { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 1350px; }
html, body, [class*="css"] { font-size: 19px; }
.big { font-size: 1.5em; font-weight: 600; margin: 0.6rem 0 0.8rem 0; }
.h { font-size: 1.0em; font-weight: 600; color: #555; margin: 0.8rem 0 0.3rem 0; }
.a { font-size: 1.15em; line-height: 1.5; }
.note { color: #666; font-size: 0.8em; margin-top: 1.6rem; }
.ok { color: #1b7f3b; font-weight: 600; } .warn { color: #b26a00; font-weight: 600; } .bad { color: #b00020; font-weight: 600; }
</style>"""


def page(st, title: str, subtitle: str = "") -> None:
    """Page config, the shared style and the localhost check. Call first in every app.py."""
    st.set_page_config(page_title=title, layout="wide")
    bad = bind_problem(st.get_option("server.address"))
    if bad:
        st.error(bad)
        st.stop()
    st.markdown(PAGE_CSS, unsafe_allow_html=True)
    st.markdown("## " + title)
    if subtitle:
        st.caption(subtitle)
