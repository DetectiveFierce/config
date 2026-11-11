"""Aggregate activity in memory; no raw command lines or open-event log is stored."""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import os
import socket
import time
from collections import defaultdict
from pathlib import Path

from .common import RUNTIME, SOCKET, now, stable_id
from .db import artifact, connect, edge, add_activity


class ActivityDaemon:
    def __init__(self):
        self.db = connect()
        self.pending: dict[tuple[str, str, str], list[int]] = defaultdict(lambda: [0, 0])
        self.process_parent: dict[int, int] = {}
        self.process_exe: dict[int, str] = {}
        self.windows: dict[int, dict] = {}
        self.focused_pid = 0
        self.focused_app = ""
        self.focus_start = now()
        self.sock: socket.socket | None = None
        self.niri_connected = False

    def day(self) -> str:
        return dt.date.today().isoformat()

    def count(self, aid: str, kind: str, count: int = 0, seconds: int = 0) -> None:
        values = self.pending[(self.day(), aid, kind)]
        values[0] += count
        values[1] += seconds

    def coverage(self, source: str) -> None:
        day = self.day()
        minute = int(time.time() // 60) % (24 * 60)
        self.db.execute("INSERT OR IGNORE INTO coverage VALUES(?,?,?)", (day, source, minute))
        self.db.commit()

    def _focused_descendant(self, pid: int) -> bool:
        seen = set()
        for _ in range(12):
            if not pid or pid in seen:
                break
            if pid == self.focused_pid:
                return True
            seen.add(pid)
            pid = self.process_parent.get(pid, 0)
        return False

    def steam_game_for(self, exe: str) -> str | None:
        if "/steamapps/common/" not in exe:
            return None
        for game in self.db.execute("SELECT id,meta FROM artifacts WHERE kind='steam_game'").fetchall():
            install_dir = json.loads(game["meta"]).get("install_dir", "")
            if install_dir and exe.startswith(install_dir.rstrip("/") + "/"):
                return game["id"]
        return None

    def handle_root(self, data: bytes) -> None:
        try:
            event = json.loads(data)
        except ValueError:
            return
        kind = event.get("kind")
        if kind == "heartbeat":
            if event.get("exec"):
                self.coverage("exec")
            else:
                self.coverage("exec_sampled")
            if event.get("fanotify"):
                self.coverage("file")
            return
        if kind == "gap":
            self.count(f"gap:{event.get('source', 'unknown')}", "collector_gap", count=1)
            return
        pid = int(event.get("pid") or 0)
        if kind == "exec":
            exe = event.get("exe", "")
            if not isinstance(exe, str) or not exe.startswith("/") or len(exe) > 4096:
                return
            aid = f"exe:{exe}"
            artifact(self.db, aid, "executable", exe, stable_id(exe), 0)
            self.db.commit()
            self.process_parent[pid] = int(event.get("ppid") or 0)
            self.process_exe[pid] = exe
            self.count(aid, "exec_foreground" if self._focused_descendant(pid)
                       else "exec_background", count=1)
            game = self.steam_game_for(exe)
            if game:
                edge(self.db, game, aid, "launches_executable")
                self.db.commit()
                self.count(game, "exec_foreground" if self._focused_descendant(pid)
                           else "exec_background", count=1)
        elif kind == "exit":
            exe = self.process_exe.get(pid)
            if exe:
                self.count(f"exe:{exe}", "exit", count=1)
            self.process_parent.pop(pid, None)
            self.process_exe.pop(pid, None)
        elif kind == "open":
            path = event.get("path", "")
            if not isinstance(path, str) or not path.startswith(str(Path.home()) + "/"):
                return
            aid = f"file:{path}"
            exe = self.process_exe.get(pid, "")
            if exe:
                edge(self.db, f"exe:{exe}", aid, "opens_file", {"source": "fanotify"})
                self.db.commit()
            self.count(aid, "open_foreground" if self._focused_descendant(pid)
                       else "open_background", count=1)

    def _end_focus(self) -> None:
        elapsed = max(0, min(now() - self.focus_start, 300))
        if self.focused_app and elapsed:
            self.count(f"session:{self.focused_app}", "focus", seconds=elapsed)
        self.focus_start = now()

    def handle_niri(self, event: dict) -> None:
        if "WindowsChanged" in event:
            self.windows = {w["id"]: w for w in event["WindowsChanged"].get("windows", [])}
            focus = next((w for w in self.windows.values() if w.get("is_focused")), None)
            if focus:
                self._set_focus(focus)
        elif "WindowOpenedOrChanged" in event:
            w = event["WindowOpenedOrChanged"].get("window", {})
            if "id" in w:
                self.windows[w["id"]] = w
                if w.get("is_focused"):
                    self._set_focus(w)
        elif "WindowFocusChanged" in event:
            wid = event["WindowFocusChanged"].get("id")
            if wid in self.windows:
                self._set_focus(self.windows[wid])

    def _set_focus(self, window: dict) -> None:
        app = str(window.get("app_id") or "").strip()
        pid = int(window.get("pid") or 0)
        if app == self.focused_app and pid == self.focused_pid:
            return
        self._end_focus()
        self.focused_app, self.focused_pid = app, pid
        if not app:
            return
        aid = f"session:{app}"
        artifact(self.db, aid, "session_app", app, stable_id(app), 0)
        self.count(aid, "focus", count=1)
        try:
            exe = os.readlink(f"/proc/{pid}/exe")
            if exe.startswith("/"):
                edge(self.db, aid, f"exe:{exe}", "window_process")
                game = self.steam_game_for(exe)
                if game:
                    edge(self.db, game, aid, "has_window")
                    self.count(game, "focus", count=1)
        except OSError:
            pass
        self.db.commit()

    def flush(self) -> None:
        self._end_focus()
        if self.niri_connected:
            self.coverage("niri")
        for (day, aid, kind), (count, seconds) in list(self.pending.items()):
            add_activity(self.db, day, aid, kind, count, seconds)
        self.pending.clear()
        self.db.commit()

    async def _flush_loop(self) -> None:
        while True:
            await asyncio.sleep(30)
            self.flush()

    async def _niri_loop(self) -> None:
        while True:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "niri", "msg", "--json", "event-stream",
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
                assert proc.stdout
                self.niri_connected = True
                while line := await proc.stdout.readline():
                    try:
                        self.handle_niri(json.loads(line))
                    except (ValueError, KeyError, TypeError):
                        pass
                await proc.wait()
            except OSError:
                pass
            self.niri_connected = False
            await asyncio.sleep(5)

    def _on_socket(self) -> None:
        assert self.sock
        while True:
            try:
                data = self.sock.recv(16384)
                self.handle_root(data)
            except BlockingIOError:
                return
            except OSError:
                return

    async def run(self) -> None:
        RUNTIME.mkdir(mode=0o700, parents=True, exist_ok=True)
        SOCKET.unlink(missing_ok=True)
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.sock.bind(str(SOCKET))
        os.chmod(SOCKET, 0o600)
        self.sock.setblocking(False)
        loop = asyncio.get_running_loop()
        loop.add_reader(self.sock.fileno(), self._on_socket)
        try:
            await asyncio.gather(self._flush_loop(), self._niri_loop())
        finally:
            self.flush()
            loop.remove_reader(self.sock.fileno())
            self.sock.close()
            SOCKET.unlink(missing_ok=True)
            self.db.close()


def main() -> None:
    asyncio.run(ActivityDaemon().run())


if __name__ == "__main__":
    main()
