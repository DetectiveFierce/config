#!/usr/bin/python3
"""Root-owned event bridge. It never reads file contents or command arguments."""
from __future__ import annotations

import ctypes
import json
import os
import select
import socket
import stat
import struct
import subprocess
import sys
import time
from pathlib import Path


UID = int(os.environ.get("STORAGE_ADVISOR_UID", "1000"))
HOME = Path(os.environ.get("STORAGE_ADVISOR_HOME", "/home/shared-psychosis"))
RUNTIME = Path(f"/run/user/{UID}/storage-advisor")
WATCHLIST = RUNTIME / "watchlist"
SOCKET = RUNTIME / "events.sock"
PROGRAM = Path("/usr/local/libexec/storage-advisor/exec_collector")
OBJECT = Path("/usr/local/libexec/storage-advisor/exec.bpf.o")
FAN_OPEN = 0x20
FAN_Q_OVERFLOW = 0x4000
FAN_MARK_ADD = 0x1
FAN_MARK_FLUSH = 0x80
FAN_CLOEXEC = 0x1
FAN_NONBLOCK = 0x2
EVENT = struct.Struct("=IBBHQii")
AT_FDCWD = -100


def send(sock: socket.socket, event: dict) -> None:
    try:
        sock.sendto(json.dumps(event, separators=(",", ":")).encode(), str(SOCKET))
    except OSError:
        pass


def owner_and_parent(pid: int) -> tuple[int, int]:
    try:
        text = Path(f"/proc/{pid}/status").read_text()
        uid = int(next(x for x in text.splitlines() if x.startswith("Uid:")).split()[1])
        ppid = int(next(x for x in text.splitlines() if x.startswith("PPid:")).split()[1])
        return uid, ppid
    except (OSError, StopIteration, ValueError):
        return -1, 0


def load_bpf() -> subprocess.Popen | None:
    try:
        process = subprocess.Popen([str(PROGRAM), str(OBJECT)], stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, bufsize=0)
        time.sleep(0.15)
        if process.poll() is not None:
            return None
        return process
    except OSError:
        return None


def fanotify_fd() -> int:
    libc = ctypes.CDLL(None, use_errno=True)
    libc.fanotify_init.argtypes = [ctypes.c_uint, ctypes.c_uint]
    libc.fanotify_init.restype = ctypes.c_int
    return libc.fanotify_init(FAN_CLOEXEC | FAN_NONBLOCK,
                             os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOATIME", 0))


def refresh_marks(fd: int, previous: set[str]) -> set[str]:
    if fd < 0:
        return set()
    libc = ctypes.CDLL(None, use_errno=True)
    libc.fanotify_mark.argtypes = [ctypes.c_int, ctypes.c_uint, ctypes.c_ulonglong,
                                  ctypes.c_int, ctypes.c_char_p]
    libc.fanotify_mark.restype = ctypes.c_int
    try:
        metadata = WATCHLIST.stat()
        if metadata.st_uid != UID or not stat.S_ISREG(metadata.st_mode):
            return previous
        lines = WATCHLIST.read_text().splitlines()[:1000]
    except OSError:
        lines = []
    paths = set()
    for line in lines:
        path = Path(line)
        try:
            if (path.is_file() and not path.is_symlink()
                    and path.resolve().is_relative_to(HOME)
                    and path.stat().st_uid == UID):
                paths.add(str(path))
        except OSError:
            pass
    if paths == previous:
        return previous
    libc.fanotify_mark(fd, FAN_MARK_FLUSH, 0, AT_FDCWD, None)
    marked = set()
    for path in paths:
        if libc.fanotify_mark(fd, FAN_MARK_ADD, FAN_OPEN, AT_FDCWD,
                             os.fsencode(path)) == 0:
            marked.add(path)
    return marked


def read_fanotify(fd: int, watched: set[str], sock: socket.socket) -> None:
    try:
        data = os.read(fd, 65536)
    except (BlockingIOError, OSError):
        return
    offset = 0
    while offset + EVENT.size <= len(data):
        event_len, version, _, metadata_len, mask, filefd, pid = EVENT.unpack_from(data, offset)
        if event_len < EVENT.size or offset + event_len > len(data):
            break
        offset += event_len
        if mask & FAN_Q_OVERFLOW:
            send(sock, {"kind": "gap", "source": "file", "time": int(time.time())})
        if filefd < 0:
            continue
        try:
            path = os.readlink(f"/proc/self/fd/{filefd}")
            uid, _ = owner_and_parent(pid)
            if uid == UID and path in watched and mask & FAN_OPEN:
                send(sock, {"kind": "open", "pid": pid, "path": path})
        except OSError:
            pass
        finally:
            os.close(filefd)


def sample_processes(seen: set[int], sock: socket.socket) -> set[int]:
    current = set()
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        pid = int(name)
        uid, ppid = owner_and_parent(pid)
        if uid != UID:
            continue
        current.add(pid)
        if pid in seen:
            continue
        try:
            exe = os.readlink(f"/proc/{pid}/exe")
            if exe.startswith("/"):
                send(sock, {"kind": "exec", "pid": pid, "ppid": ppid,
                            "exe": exe, "sampled": True})
        except OSError:
            pass
    for pid in seen - current:
        send(sock, {"kind": "exit", "pid": pid})
    return current


def main() -> int:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    fanfd = fanotify_fd()
    process = load_bpf()
    buffer = b""
    watched: set[str] = set()
    seen: set[int] = set()
    next_heartbeat = next_watch = next_sample = 0.0
    try:
        while True:
            time_now = time.monotonic()
            if time_now >= next_watch:
                watched = refresh_marks(fanfd, watched)
                next_watch = time_now + 60
            if time_now >= next_heartbeat:
                send(sock, {"kind": "heartbeat", "exec": process is not None,
                            "fanotify": fanfd >= 0, "time": int(time.time())})
                next_heartbeat = time_now + 60
            if process is None and time_now >= next_sample:
                seen = sample_processes(seen, sock)
                next_sample = time_now + 2
            readable = [fanfd] if fanfd >= 0 else []
            if process is not None and process.stdout:
                readable.append(process.stdout.fileno())
            ready, _, _ = select.select(readable, [], [], 1)
            for fd in ready:
                if fd == fanfd:
                    read_fanotify(fanfd, watched, sock)
                elif process and process.stdout and fd == process.stdout.fileno():
                    block = os.read(fd, 8192)
                    if not block:
                        process = None
                        continue
                    buffer += block
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        parts = line.split(b"\t", 2)
                        try:
                            pid = int(parts[1])
                            if parts[0] == b"X":
                                send(sock, {"kind": "exit", "pid": pid})
                            elif parts[0] == b"E" and len(parts) == 3:
                                exe = bytes.fromhex(parts[2].decode()).decode(errors="replace")
                                uid, ppid = owner_and_parent(pid)
                                # BPF already filtered UID; the process may have exited
                                # before /proc can supply its parent.
                                if uid in (UID, -1) and exe.startswith("/"):
                                    send(sock, {"kind": "exec", "pid": pid,
                                                "ppid": ppid, "exe": exe})
                        except (ValueError, IndexError):
                            pass
            if process is None and time_now >= next_heartbeat - 1:
                process = load_bpf()
    except KeyboardInterrupt:
        return 0
    finally:
        if process:
            process.terminate()
        if fanfd >= 0:
            os.close(fanfd)
        sock.close()


if __name__ == "__main__":
    sys.exit(main())
