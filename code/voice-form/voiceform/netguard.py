"""Proof of offline: while the guard is on, any TCP or UDP connection to a host other than this machine, and any
name lookup for another host, made from this Python process is blocked and counted.

LM Studio and the Streamlit page live on this machine, so loopback is allowed. The demo shows the counter
("connections to the internet: 0"); the tests fail if any step tries to reach the internet. A child process
(for example ffmpeg) is not covered: it is started with a local file only (see audio.load).

The guard can be nested and used from several threads: the sockets are patched when the first guard starts and
restored when the last one ends, and every active guard records its own counts.
"""

import ipaddress
import socket
import threading
from contextlib import contextmanager

_LOCAL = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
_lock = threading.Lock()
_active = []          # the guards currently inside a `with offline()` block
_originals = {}       # the real socket functions, kept while any guard is active


class Blocked(ConnectionError):
    pass


class Guard:
    def __init__(self, raise_on_block: bool = True):
        self.raise_on_block = raise_on_block
        self.blocked = []      # (host, port) attempts that were stopped
        self.local = 0         # connections to this machine (LM Studio)


def _host(address):
    if isinstance(address, tuple) and address:
        return str(address[0]), (address[1] if len(address) > 1 else None)
    return str(address), None


def _is_local(host: str) -> bool:
    return host in _LOCAL or host.startswith("127.")


def _is_ip_literal(host: str) -> bool:
    try:
        ipaddress.ip_address(host.split("%")[0])
        return True
    except ValueError:
        return False


def _check(address) -> bool:
    """Count the attempt on every active guard. True when the address is this machine."""
    host, port = _host(address)
    local = _is_local(host)
    with _lock:
        guards = list(_active)
    for g in guards:
        if local:
            g.local += 1
        else:
            g.blocked.append((host, port))
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
        if name and not _is_ip_literal(name) and not _is_local(name):   # a real name lookup; literals are checked at connect
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


@contextmanager
def offline(raise_on_block: bool = True):
    """Block every non-loopback connect(), sendto() and name lookup inside the block. Yields a Guard with the counts."""
    guard = Guard(raise_on_block)
    with _lock:
        if not _active:
            _patch()
        _active.append(guard)
    try:
        yield guard
    finally:
        with _lock:
            _active.remove(guard)
            if not _active:
                _restore()
