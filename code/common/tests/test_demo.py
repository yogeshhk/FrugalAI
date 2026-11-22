"""Offline tests for the shared demo-page pieces: no LM Studio, no network, no Streamlit."""

import ast
import socket
import threading
from pathlib import Path

import pytest

from frugalai_common import demo as D

CODE = Path(__file__).resolve().parents[2]
APPS = sorted(CODE.glob("*/app.py"))


def test_pages_refuse_to_run_unless_bound_to_this_machine():
    assert D.bind_problem("localhost") == "" and D.bind_problem("127.0.0.1") == ""
    assert D.bind_problem(None) != "" and D.bind_problem("") != ""
    assert D.bind_problem("0.0.0.0") != ""


def test_guard_blocks_other_hosts_and_counts_local():
    g = D.Guard()
    original = (socket.socket.connect, socket.socket.connect_ex, socket.socket.sendto, socket.getaddrinfo)
    try:
        D.install_guard(g)
        s = socket.socket()
        with pytest.raises(D.Blocked):
            s.connect(("93.184.216.34", 80))                      # an internet address: refused before any packet is sent
        assert s.connect_ex(("93.184.216.34", 80)) == 111
        assert g.blocked and g.blocked[0][0] == "93.184.216.34"
        with pytest.raises(socket.gaierror):
            socket.getaddrinfo("example.org", 80)                 # a name lookup for another host is refused
        assert ("example.org", None) in g.blocked
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        with pytest.raises(D.Blocked):
            udp.sendto(b"x", ("93.184.216.34", 53))               # so is a UDP datagram
        udp.close()
        assert socket.getaddrinfo("localhost", 80)                # this machine still resolves
        server = socket.socket()
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        threading.Thread(target=server.accept, daemon=True).start()
        c = socket.socket()
        c.connect(("127.0.0.1", server.getsockname()[1]))
        assert g.local == 1
        c.close()
        server.close()
        s.close()
    finally:
        D.uninstall_guard(g)
    assert (socket.socket.connect, socket.socket.connect_ex, socket.socket.sendto, socket.getaddrinfo) == original


def test_machine_lines_name_cpu_ram_and_each_gpu():
    lines = D.machine_lines({"cpu": "Some CPU", "cores": 12, "ram_gb": 15.7,
                             "gpus": [{"name": "GeForce MX570", "memory_gb": 2.0}, {"name": "Iris", "memory_gb": 0}]})
    assert lines == ["Some CPU, 12 logical cores", "15.7 GB RAM", "GPU: GeForce MX570 (2.0 GB)", "GPU: Iris"]


def test_lm_models_is_none_when_nothing_listens():
    assert D.lm_models("http://127.0.0.1:9/v1") is None


def test_every_demo_page_guards_before_it_imports_its_project():
    """Each code/<project>/app.py calls install_guard() before any import from its own package."""
    assert APPS, "no demo pages found"
    for app in APPS:
        tree = ast.parse(app.read_text(encoding="utf-8"))
        guard_line = next((n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call)
                           and getattr(n.func, "attr", "") == "install_guard"), None)
        assert guard_line, "%s never installs the offline guard" % app
        project_imports = [n.lineno for n in tree.body if isinstance(n, ast.ImportFrom) and n.module
                           and n.module.split(".")[0] not in ("frugalai_common", "__future__")
                           and n.module.split(".")[0] in {p.name for p in app.parent.iterdir() if p.is_dir()}]
        assert all(line > guard_line for line in project_imports), app
