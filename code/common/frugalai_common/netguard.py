"""Proof of offline: while a guard is on, any TCP or UDP connection to a host other than this machine, and any
name lookup for another host, made from this Python process is blocked and counted.

Two ways to use it:
- `with offline() as g:` for one block of work (a pipeline run, a test). The counts are in `g`.
- `install()` for the rest of the process (every demo page calls it first, through `demo.install_guard`).

Loopback is allowed: LM Studio, llama-server and the demo page itself live on this machine. A child process (for
example ffmpeg) is not covered. Guards can be nested and used from several threads: the sockets are patched when the
first guard starts and restored when the last one ends, and every active guard records its own counts.
"""

import ipaddress
import socket
import threading
from contextlib import contextmanager
from typing import List

_LOCAL = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
_lock = threading.Lock()
_active: List["Guard"] = []   # the guards currently on
_originals = {}               # the real socket functions, kept while any guard is on


class Blocked(ConnectionError):
    pass


class Guard:
    def __init__(self):
        self.blocked = []      # (host, port) attempts that were stopped
        self.local = 0         # connections to this machine

    @property
    def active(self) -> bool:
        return self in _active


def _host(address):
    if isinstance(address, tuple) and address:
        return str(address[0]), (address[1] if len(address) > 1 else None)
    return str(address), None


def is_local(address) -> bool:
    host = _host(address)[0]
    return host in _LOCAL or host.startswith("127.")


def _is_ip_literal(host: str) -> bool:
    try:
        ipaddress.ip_address(str(host).split("%")[0])
        return True
    except ValueError:
        return False


def _check(address) -> bool:
    """Count the attempt on every active guard. True when the address is this machine."""
    local = is_local(address)
    with _lock:
        guards = list(_active)
    for g in guards:
        if local:
            g.local += 1
        else:
            g.blocked.append(_host(address))
    return local


def _patch():
    orig = {
        "connect": socket.socket.connect, "connect_ex": socket.socket.connect_ex,
        "sendto": socket.socket.sendto, "getaddrinfo": socket.getaddrinfo,
    }
    _originals.update(orig)

    def connect(sock, address):
        if not _check(address):
            host, port = _host(address)
            raise Blocked(f"offline guard: blocked a connection to {host}:{port}")
        return orig["connect"](sock, address)

    def connect_ex(sock, address):
        if not _check(address):
            return 111  # connection refused
        return orig["connect_ex"](sock, address)

    def sendto(sock, data, *args):
        address = args[-1] if args else None   # sendto(data, address) or sendto(data, flags, address)
        if address is not None and not _check(address):
            host, port = _host(address)
            raise Blocked(f"offline guard: blocked a datagram to {host}:{port}")
        return orig["sendto"](sock, data, *args)

    def getaddrinfo(host, *args, **kwargs):
        name = host.decode("ascii", "replace") if isinstance(host, bytes) else host
        if name and not _is_ip_literal(name) and not is_local(name):   # a real name lookup; literals are checked at connect
            with _lock:
                guards = list(_active)
            for g in guards:
                g.blocked.append((name, None))
            raise socket.gaierror(f"offline guard: blocked a name lookup for {name}")
        return orig["getaddrinfo"](host, *args, **kwargs)

    socket.socket.connect, socket.socket.connect_ex = connect, connect_ex
    socket.socket.sendto, socket.getaddrinfo = sendto, getaddrinfo


def _restore():
    socket.socket.connect, socket.socket.connect_ex = _originals["connect"], _originals["connect_ex"]
    socket.socket.sendto, socket.getaddrinfo = _originals["sendto"], _originals["getaddrinfo"]
    _originals.clear()


def install(guard: Guard = None) -> Guard:
    """Turn a guard on and leave it on (demo pages). Calling it again with the same guard does nothing."""
    guard = guard or Guard()
    with _lock:
        if guard not in _active:
            if not _active:
                _patch()
            _active.append(guard)
    return guard


def uninstall(guard: Guard) -> None:
    """Turn a guard off. The sockets are restored when no guard is left on."""
    with _lock:
        if guard in _active:
            _active.remove(guard)
            if not _active:
                _restore()


@contextmanager
def offline():
    """Block every non-loopback connect(), sendto() and name lookup inside the block. Yields a Guard with the counts."""
    guard = install(Guard())
    try:
        yield guard
    finally:
        uninstall(guard)
