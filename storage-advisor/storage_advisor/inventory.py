from __future__ import annotations

import configparser
import datetime as dt
import json
import os
import re
import shlex
import shutil
import sqlite3
from collections import defaultdict
from pathlib import Path

from .common import HOME, STATE, SECRET_PARTS, LIVE_PARTS, file_fingerprint, now, run, stable_id
from .db import artifact, edge


def _bytes(text: str) -> int:
    match = re.search(r"([\d.]+(?:e[+-]?\d+)?)\s*(B|KiB|MiB|GiB|TiB|kB|MB|GB|TB)?", text, re.I)
    if not match:
        return 0
    unit = match.group(2) or "B"
    mult = {"B": 1, "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3,
            "TiB": 1024**4, "kB": 1000, "MB": 1000**2,
            "GB": 1000**3, "TB": 1000**4}[unit]
    return int(float(match.group(1)) * mult)


def _fields(record: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in record.splitlines():
        if ": " in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
        elif line.startswith(" ") and result:
            key = next(reversed(result))
            result[key] += " " + line.strip()
    return result


def pacman(db: sqlite3.Connection) -> dict:
    info = run(["pacman", "-Qi"], 90)
    if info.returncode:
        return {"error": info.stderr.strip()}
    explicit = set(run(["pacman", "-Qeq"], 30).stdout.split())
    foreign = set(run(["pacman", "-Qmq"], 30).stdout.split())
    orphans = set(run(["pacman", "-Qdtq"], 30).stdout.split())
    count = 0
    for chunk in re.split(r"\n\s*\n", info.stdout):
        fields = _fields(chunk)
        name = fields.get("Name")
        if not name:
            continue
        aid = f"pkg:{name}"
        fingerprint = stable_id(name, fields.get("Version"), fields.get("Install Reason"))
        meta = {"version": fields.get("Version", ""),
                "description": fields.get("Description", ""),
                "installed_size": _bytes(fields.get("Installed Size", "0 B")),
                "install_date": fields.get("Install Date", ""),
                "explicit": name in explicit, "foreign": name in foreign,
                "orphan": name in orphans,
                "required_by": fields.get("Required By", "None"),
                "optional_for": fields.get("Optional For", "None")}
        artifact(db, aid, "package", name, fingerprint, meta["installed_size"], meta)
        for dependency in fields.get("Depends On", "").split():
            if dependency == "None":
                continue
            depname = re.split(r"[<>=]", dependency)[0]
            edge(db, aid, f"pkg:{depname}", "depends", {"declared": dependency})
        count += 1
    return {"packages": count, "orphans": len(orphans)}


def _desktop_executable(value: str) -> str | None:
    try:
        parts = shlex.split(value)
    except ValueError:
        return None
    if not parts:
        return None
    if parts[0] == "env":
        parts = parts[1:]
        while parts and "=" in parts[0] and not parts[0].startswith("/"):
            parts.pop(0)
    if not parts:
        return None
    command = parts[0]
    return shutil.which(command) or (command if command.startswith("/") else None)


def desktop_entries(db: sqlite3.Connection) -> dict:
    roots = [Path("/usr/share/applications"), HOME / ".local/share/applications"]
    defaults: set[str] = set()
    for cfgpath in (HOME / ".config/mimeapps.list", HOME / ".local/share/applications/mimeapps.list"):
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            parser.read(cfgpath)
            defaults.update(x for value in parser["Default Applications"].values()
                            for x in value.split(";") if x)
        except (KeyError, configparser.Error):
            pass
    count = 0
    owner_cache: dict[str, str] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.glob("*.desktop"):
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                parser.read(path, encoding="utf-8")
                data = parser["Desktop Entry"]
                if data.get("Type") != "Application" or data.getboolean("Hidden", False):
                    continue
                appid = path.name
                aid = f"app:{appid}"
                executable = _desktop_executable(data.get("Exec", ""))
                mimes = [x for x in data.get("MimeType", "").split(";") if x]
                meta = {"name": data.get("Name", path.stem), "comment": data.get("Comment", ""),
                        "categories": data.get("Categories", ""), "mimes": mimes,
                        "default": appid in defaults, "exec": executable or ""}
                artifact(db, aid, "app", appid, stable_id(path, path.stat().st_mtime_ns), 0, meta)
                if executable:
                    edge(db, aid, f"exe:{executable}", "launches")
                    if executable not in owner_cache:
                        result = run(["pacman", "-Qoq", executable], 8)
                        owner_cache[executable] = result.stdout.strip() if result.returncode == 0 else ""
                    if owner_cache[executable]:
                        edge(db, f"pkg:{owner_cache[executable]}", f"exe:{executable}",
                             "owns_executable", {"pacman_query": True})
                for mime in mimes:
                    edge(db, aid, f"mime:{mime}", "handles")
                count += 1
            except (OSError, KeyError, ValueError, configparser.Error):
                continue
    return {"desktop_apps": count}


def home_files(db: sqlite3.Connection, full: bool) -> dict:
    roots = [HOME / name for name in ("Downloads", "Documents", "Pictures", "Videos",
                                    "Music", "Desktop", "Projects", "pdfs", "Landing Zone")]
    count = 0
    scanned = 0
    truncated = False
    if full:
        for root in roots:
            if truncated:
                break
            if not root.is_dir():
                continue
            for base, directories, files in os.walk(root, followlinks=False):
                directories[:] = [x for x in directories if x not in SECRET_PARTS | LIVE_PARTS
                                  and not Path(base, x).is_symlink()]
                for name in files:
                    if scanned >= 300000:
                        truncated = True
                        break
                    path = Path(base, name)
                    try:
                        stat = path.stat(follow_symlinks=False)
                    except OSError:
                        continue
                    scanned += 1
                    if not path.is_file() or path.is_symlink() or stat.st_size < 1024 * 1024:
                        continue
                    aid = f"file:{path}"
                    meta = {"mtime": int(stat.st_mtime), "atime": int(stat.st_atime),
                            "dev": stat.st_dev, "ino": stat.st_ino, "nlink": stat.st_nlink,
                            "blocks": stat.st_blocks * 512, "extension": path.suffix.lower()}
                    artifact(db, aid, "file", str(path), file_fingerprint(path),
                             stat.st_blocks * 512, meta)
                    count += 1
                if truncated:
                    break
    else:
        rows = db.execute("SELECT id,locator FROM artifacts WHERE kind='file'").fetchall()
        for row in rows:
            path = Path(row["locator"])
            try:
                stat = path.stat(follow_symlinks=False)
                if not path.is_file() or path.is_symlink():
                    continue
                meta = {"mtime": int(stat.st_mtime), "atime": int(stat.st_atime),
                        "dev": stat.st_dev, "ino": stat.st_ino, "nlink": stat.st_nlink,
                        "blocks": stat.st_blocks * 512, "extension": path.suffix.lower()}
                artifact(db, row["id"], "file", str(path), file_fingerprint(path),
                         stat.st_blocks * 512, meta)
                count += 1
            except OSError:
                pass
    today = dt.date.today().isoformat()
    measured_roots = [HOME / ".cache/yay", Path("/var/cache/pacman/pkg")]
    if full:
        measured_roots += [HOME / ".local/share/Steam", HOME / ".local/share/pdf-folio"]
    for root in measured_roots:
        if not root.exists():
            continue
        result = run(["du", "-sx", "-B1", str(root)], 90)
        try:
            size = int(result.stdout.split()[0])
        except (IndexError, ValueError):
            continue
        aid = f"dir:{root}"
        artifact(db, aid, "directory", str(root), stable_id(root, size), size)
        db.execute("INSERT OR REPLACE INTO measurements VALUES(?,?,?)", (aid, today, size))
    return {"files": count, "scanned": scanned, "truncated": truncated,
            "mode": "full" if full else "incremental"}


def projects(db: sqlite3.Connection) -> dict:
    roots = [HOME / "Landing Zone", HOME / "Documents", HOME]
    found: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            continue
        # Limit discovery depth; nested dependencies and generated trees are excluded.
        for base, dirs, _ in os.walk(root):
            rel_depth = len(Path(base).relative_to(root).parts)
            if ".git" in dirs or (Path(base) / ".git").is_file():
                found.add(Path(base))
                dirs[:] = []
            elif rel_depth >= 4:
                dirs[:] = []
            else:
                dirs[:] = [x for x in dirs if x not in SECRET_PARTS | LIVE_PARTS
                           and not x.startswith(".") and x not in ("Steam", "node_modules")]
    manifests = {"package.json": ["node", "npm"], "Cargo.toml": ["cargo", "rustc"],
                 "pyproject.toml": ["python"], "go.mod": ["go"],
                 "Dockerfile": ["docker"], "Gemfile": ["ruby"],
                 "renv.lock": ["R"], "Makefile": ["make"],
                 "build.zig": ["zig"]}
    for root in found:
        aid = f"project:{root}"
        last = run(["git", "-C", str(root), "log", "-1", "--format=%ct"], 10)
        last_commit = int(last.stdout.strip()) if last.stdout.strip().isdigit() else 0
        observed = [name for name in manifests if (root / name).is_file()]
        artifact(db, aid, "project", str(root), stable_id(root, last_commit, observed), 0,
                 {"last_commit": last_commit, "manifests": observed})
        for name in observed:
            for tool in manifests[name]:
                edge(db, aid, f"command:{tool}", "uses_tool", {"manifest": name})
                executable = shutil.which(tool)
                if executable:
                    edge(db, f"command:{tool}", f"exe:{executable}", "resolves_to")
    return {"projects": len(found)}


def configured_services(db: sqlite3.Connection) -> dict:
    """Record referenced commands without storing unit or Niri file contents."""
    sources = list((HOME / ".config/systemd/user").glob("*.service"))
    sources += list(Path("/etc/systemd/system").glob("*.service"))
    sources += list((HOME / ".config/niri").rglob("*.kdl"))[:200]
    count = 0
    for path in sources[:400]:
        if not path.is_file():
            continue
        try:
            text = path.read_text(errors="replace")[:150_000]
        except OSError:
            continue
        aid = f"config:{path}"
        artifact(db, aid, "config_reference", str(path), stable_id(path, path.stat().st_mtime_ns), 0)
        commands = []
        if path.suffix == ".service":
            commands = re.findall(r"^Exec(?:Start|Reload|Stop)=(?:[-@+:!]*)([^\s]+)", text, re.M)
        else:
            commands = re.findall(r"spawn(?:-at-startup)?\s+\"([^\"]+)\"", text)
        for command in commands[:100]:
            executable = shutil.which(command) or (command if command.startswith("/") else "")
            if executable:
                edge(db, aid, f"exe:{executable}", "references_executable")
        count += 1
    return {"configured_sources": count}


def docker(db: sqlite3.Connection) -> dict:
    ids = [x for x in run(["docker", "image", "ls", "-aq", "--no-trunc"], 20).stdout.split()
           if x.startswith("sha256:")]
    if not ids:
        return {"docker_images": 0}
    raw = run(["docker", "image", "inspect", *ids], 50)
    try:
        images = json.loads(raw.stdout)
    except ValueError:
        return {"docker_error": raw.stderr.strip()[:200]}
    container_ids = run(["docker", "container", "ls", "-aq"], 20).stdout.split()
    inspected = run(["docker", "container", "inspect", *container_ids], 40) if container_ids else None
    try:
        used_ids = {item["Image"] for item in json.loads(inspected.stdout)} if inspected and inspected.returncode == 0 else set()
    except (ValueError, KeyError):
        return {"docker_error": "Container references could not be verified"}
    if container_ids and (not inspected or inspected.returncode):
        return {"docker_error": "Container references could not be verified"}
    unique: dict[str, int] = {}
    usage = run(["docker", "system", "df", "-v"], 60)
    for line in usage.stdout.splitlines():
        columns = re.split(r"\s{2,}", line.strip())
        if len(columns) >= 8 and re.fullmatch(r"[0-9a-f]{12}", columns[2]):
            unique[columns[2]] = _bytes(columns[-2])
    for image in images:
        iid = image.get("Id", "")
        if not iid:
            continue
        tags = [x for x in image.get("RepoTags") or [] if x != "<none>:<none>"]
        layers = image.get("RootFS", {}).get("Layers") or []
        meta = {"tags": tags, "created": image.get("Created", ""),
                "containers": iid in used_ids, "layer_count": len(layers),
                "unique_bytes": unique.get(iid[7:19], 0)}
        artifact(db, f"docker:{iid}", "docker_image", iid,
                 stable_id(iid, tags, iid in used_ids), image.get("Size", 0), meta)
        for layer in layers:
            edge(db, f"docker:{iid}", f"layer:{layer}", "uses_layer")
    return {"docker_images": len(images)}


def steam(db: sqlite3.Connection) -> dict:
    root = HOME / ".local/share/Steam/steamapps"
    count = 0
    for manifest in root.glob("appmanifest_*.acf"):
        try:
            text = manifest.read_text(errors="replace")
            fields = dict(re.findall(r'^\s*"([^"\n]+)"\s+"([^"\n]*)"', text, re.M))
            appid = fields.get("appid", manifest.stem.removeprefix("appmanifest_"))
            common = root / "common" / fields.get("installdir", "")
            size = int(fields.get("SizeOnDisk", "0"))
            meta = {"name": fields.get("name", appid), "install_dir": str(common),
                    "last_updated": fields.get("LastUpdated", ""),
                    "shadercache": str(root / "shadercache" / appid),
                    "compatdata": str(root / "compatdata" / appid)}
            aid = f"steam:{appid}"
            artifact(db, aid, "steam_game", appid, stable_id(appid, size, common), size, meta)
            edge(db, aid, f"dir:{common}", "installs_to")
            count += 1
        except (OSError, ValueError):
            continue
    return {"steam_games": count}


def flatpak(db: sqlite3.Connection) -> dict:
    result = run(["flatpak", "list", "--app", "--columns=application,installation,size"], 30)
    count = 0
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if not parts or "." not in parts[0]:
            continue
        appid = parts[0]
        size = _bytes(parts[2]) if len(parts) > 2 else 0
        artifact(db, f"flatpak:{appid}", "flatpak", appid,
                 stable_id(appid, parts[1:]), size,
                 {"installation": parts[1] if len(parts) > 1 else "system"})
        count += 1
    return {"flatpaks": count}


def inventory(db: sqlite3.Connection, full: bool) -> dict:
    stats = {}
    collectors = (pacman, desktop_entries, projects, configured_services, docker, steam, flatpak) if full else \
                 (pacman, desktop_entries, configured_services, docker, steam, flatpak)
    for collector in collectors:
        stats.update(collector(db))
        db.commit()
    stats.update(home_files(db, full))
    db.commit()
    return stats
