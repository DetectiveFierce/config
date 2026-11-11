from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path


HOME = Path.home()
STATE = Path(os.environ.get("XDG_STATE_HOME", HOME / ".local/state")) / "storage-advisor"
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config")) / "storage-advisor"
RUNTIME = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "storage-advisor"
DB_PATH = STATE / "advisor.db"
SOCKET = RUNTIME / "events.sock"
WATCHLIST = RUNTIME / "watchlist"
DEFAULT_SETTINGS = {"cadence": "weekly", "max_suggestions": 12,
                    "embeddings": True, "execution_enabled": False}
SECRET_PARTS = {".ssh", ".gnupg", ".pki", "keyrings", "wallets", "secrets", ".password-store"}
LIVE_PARTS = {".git", "node_modules", "__pycache__", "browser", "Default", "Profiles",
              "Firefox", "Chromium", "Google", "BraveSoftware", "storage-advisor", "databases"}


def now() -> int:
    return int(time.time())


def stable_id(*parts: object) -> str:
    text = "\0".join(str(x) for x in parts)
    return hashlib.sha256(text.encode()).hexdigest()[:24]


def dumps(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def settings() -> dict:
    path = CONFIG / "settings.json"
    try:
        value = json.loads(path.read_text())
        return {**DEFAULT_SETTINGS, **value}
    except (OSError, ValueError):
        return DEFAULT_SETTINGS.copy()


def save_settings(value: dict) -> None:
    CONFIG.mkdir(mode=0o700, parents=True, exist_ok=True)
    target = CONFIG / "settings.json"
    temp = target.with_suffix(".tmp")
    with open(temp, "w", encoding="utf-8") as stream:
        os.fchmod(stream.fileno(), 0o600)
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
    os.replace(temp, target)


def run(argv: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(argv, text=True, capture_output=True, timeout=timeout,
                              env={**os.environ, "LC_ALL": "C"}, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(argv, 127, "", str(exc))


def safe_home_file(path: Path) -> bool:
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(HOME)
        return (path.is_file() and not path.is_symlink() and path.stat().st_uid == os.getuid()
                and not any(p in SECRET_PARTS for p in path.parts)
                and not any(p in LIVE_PARTS for p in path.parts)
                and STATE not in resolved.parents)
    except (OSError, ValueError):
        return False


def file_fingerprint(path: Path) -> str:
    stat = path.stat(follow_symlinks=False)
    return stable_id(path, stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)


def directory_fingerprint(path: Path, limit: int = 20000) -> tuple[str, int]:
    """Bounded tree identity for refusing a changed directory at execution time."""
    digest = hashlib.sha256()
    count = 0
    for base, dirs, files in os.walk(path, followlinks=False):
        names = sorted(dirs + files)
        dirs[:] = sorted(d for d in dirs if not (Path(base) / d).is_symlink())
        for name in names:
            child = Path(base) / name
            st = child.stat(follow_symlinks=False)
            count += 1
            if count > limit:
                raise ValueError("Directory has too many entries for a safe preview")
            digest.update(str(child.relative_to(path)).encode(errors="surrogateescape"))
            digest.update(f":{st.st_mode}:{st.st_size}:{st.st_mtime_ns}:{st.st_ino}".encode())
    return digest.hexdigest(), count
