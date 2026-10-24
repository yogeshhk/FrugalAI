"""Proof of offline: while the guard is on, any connection to a host other than this machine is blocked and counted.

LM Studio and the Streamlit page live on this machine, so loopback is allowed. The demo shows the counter
("connections to the internet: 0"); the tests fail if any step tries to reach the internet.
"""

import socket
import threading
from contextlib import contextmanager

_LOCAL = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
_lock = threading.Lock()


class Blocked(ConnectionError):
    pass


class Guard:
    def __init__(self):
        self.blocked = []      # (host, port) attempts that were stopped
        self.local = 0         # connections to this machine (LM Studio)


def _host(address):
    if isinstance(address, tuple) and address:
        return str(address[0]), (address[1] if len(address) > 1 else None)
    return str(address), None


@contextmanager
def offline(raise_on_block: bool = True):
    """Block every non-loopback connect() inside the block. Yields a Guard with the counts."""
    guard = Guard()
    original = socket.socket.connect
    original_ex = socket.socket.connect_ex

    def check(sock, address):
        host, port = _host(address)
        if host in _LOCAL or host.startswith("127."):
            guard.local += 1
            return True
        guard.blocked.append((host, port))
        if raise_on_block:
            raise Blocked(f"offline guard: blocked a connection to {host}:{port}")
        return False

    def connect(sock, address):
        check(sock, address)
        return original(sock, address)

    def connect_ex(sock, address):
        if not check(sock, address):
            return 111  # connection refused
        return original_ex(sock, address)

    with _lock:
        socket.socket.connect, socket.socket.connect_ex = connect, connect_ex
    try:
        yield guard
    finally:
        with _lock:
            socket.socket.connect, socket.socket.connect_ex = original, original_ex
