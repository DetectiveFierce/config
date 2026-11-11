from __future__ import annotations

import json
import hashlib
import os
import re
import secrets
import shutil
import sqlite3
import stat
from pathlib import Path

from .common import HOME, directory_fingerprint, dumps, file_fingerprint, now, run, safe_home_file, settings, stable_id
from .db import row_json
from .similarity import exact_digest


class ActionError(Exception):
    pass


def paccache_candidates(keep: int) -> list[Path]:
    result = run(["paccache", "-d", "-k", str(keep), "-v"], 45)
    if result.returncode:
        raise ActionError(result.stderr.strip() or "Paccache preview failed")
    root = Path("/var/cache/pacman/pkg")
    return sorted(root / line for line in result.stdout.splitlines()
                  if line and not line.startswith("==>") and (root / line).parent == root)


def _guard_digest(value: object) -> str:
    return hashlib.sha256(dumps(value).encode()).hexdigest()


def package_reclaimable_bytes(targets: list[str]) -> int:
    listing = run(["pacman", "-Qlq", *targets], 30)
    if listing.returncode:
        raise ActionError("Package files could not be inventoried")
    inodes: dict[tuple[int, int], list[int]] = {}
    for name in listing.stdout.splitlines():
        try:
            st = Path(name).lstat()
        except OSError:
            continue
        if not stat.S_ISREG(st.st_mode):
            continue
        record = inodes.setdefault((st.st_dev, st.st_ino), [st.st_blocks * 512, st.st_nlink, 0])
        record[2] += 1
    return sum(blocks for blocks, links, listed in inodes.values() if listed >= links)


def _get(db: sqlite3.Connection, sid: str) -> dict:
    row = db.execute("SELECT * FROM suggestions WHERE id=?", (sid,)).fetchone()
    if not row:
        raise ActionError("Suggestion no longer exists")
    return row_json(row)


def _pacman_plan(package: str) -> dict:
    if not package or not all(c.isalnum() or c in "@+._-" for c in package):
        raise ActionError("Invalid package name")
    result = run(["pacman", "-Rs", "--print-format", "%n", package], 20)
    if result.returncode:
        raise ActionError(result.stderr.strip() or "Pacman cannot preview removal")
    targets = [x for x in result.stdout.splitlines() if x]
    if not targets:
        raise ActionError("Empty pacman transaction")
    from .recommend import PROTECTED_PACKAGES
    if set(targets) & PROTECTED_PACKAGES:
        raise ActionError("A protected system package is in the transaction")
    versions = {}
    for target in targets:
        version = run(["pacman", "-Q", target], 10)
        if version.returncode:
            raise ActionError("A package changed during preview")
        versions[target] = version.stdout.strip()
    return {"type": "pacman_remove", "package": package, "targets": targets,
            "bytes": package_reclaimable_bytes(targets),
            "versions": versions, "guard_digest": _guard_digest({"targets": targets, "versions": versions}),
            "command": ["pacman", "-Rns", "--", package],
            "restore": f"Reinstall with pacman -S {package}; configuration may need restoration"}


def _current_plan(suggestion: dict) -> dict:
    action = suggestion["action"]
    typ = action["type"]
    if typ == "pacman_remove":
        return _pacman_plan(action["package"])
    if typ == "guided_app":
        dbid = action["app"]
        # Desktop app ownership is resolved from its executable, never from a
        # guessed package name.
        import configparser
        for root in (HOME / ".local/share/applications", Path("/usr/share/applications")):
            path = root / dbid.removeprefix("app:")
            if not path.is_file():
                continue
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            parser.read(path)
            from .inventory import _desktop_executable
            exe = _desktop_executable(parser["Desktop Entry"].get("Exec", ""))
            if exe:
                owner = run(["pacman", "-Qoq", exe], 10)
                if owner.returncode == 0 and owner.stdout.strip():
                    return _pacman_plan(owner.stdout.strip())
        raise ActionError("This app needs a manual uninstall; no verified package owner was found")
    if typ == "paccache":
        keep = action["keep"]
        paths = paccache_candidates(keep)
        files = [(str(p), p.stat().st_size) for p in paths if p.is_file()]
        return {"type": "paccache", "keep": keep, "files": files,
                "bytes": sum(size for _, size in files),
                "guard_digest": _guard_digest(files),
                "command": ["paccache", "-r", "-k", str(keep)],
                "restore": "Re-download or reinstall the removed package archives if needed"}
    if typ == "remove_cache_directory":
        path = Path(action["path"])
        root = HOME / ".cache/yay"
        if path.parent != root or path.is_symlink() or not path.is_dir():
            raise ActionError("The yay cache directory changed or is outside the allowed root")
        result = run(["du", "-sx", "-B1", str(path)], 30)
        size = int(result.stdout.split()[0]) if result.stdout.split() else 0
        tree_fingerprint, item_count = directory_fingerprint(path, limit=100000)
        return {"type": typ, "path": str(path), "tree_fingerprint": tree_fingerprint,
                "items": item_count,
                "bytes": size, "command": ["remove this yay cache directory"],
                "restore": "Yay can rebuild this directory during a later update"}
    if typ == "docker_image_remove":
        iid = action["image_id"]
        if not iid.startswith("sha256:") or len(iid) != 71:
            raise ActionError("Invalid Docker image ID")
        image = run(["docker", "image", "inspect", iid], 20)
        if image.returncode:
            raise ActionError("Docker image no longer exists")
        inspected = json.loads(image.stdout)[0]
        if any(tag != "<none>:<none>" for tag in (inspected.get("RepoTags") or [])):
            raise ActionError("Image acquired a tag and is no longer a dangling candidate")
        ids = run(["docker", "container", "ls", "-aq"], 20)
        if ids.returncode:
            raise ActionError("Container references could not be verified")
        if ids.stdout.strip():
            containers = run(["docker", "container", "inspect", *ids.stdout.split()], 40)
            if containers.returncode:
                raise ActionError("Container references could not be verified")
            if any(item.get("Image") == iid for item in json.loads(containers.stdout)):
                raise ActionError("A container references this image")
        from .inventory import _bytes
        usage = run(["docker", "system", "df", "-v"], 60)
        if usage.returncode:
            raise ActionError("Docker recovery could not be measured")
        unique = None
        for line in usage.stdout.splitlines():
            columns = re.split(r"\s{2,}", line.strip())
            if len(columns) >= 8 and columns[2] == iid[7:19]:
                unique = _bytes(columns[-2])
                break
        if unique is None:
            raise ActionError("Docker image is missing from its storage report")
        return {"type": typ, "image_id": iid, "bytes": unique,
                "command": ["docker", "image", "rm", iid],
                "restore": "Pull or rebuild the image again"}
    if typ == "steam_uninstall":
        appid = action["appid"]
        if not isinstance(appid, str) or not appid.isdigit():
            raise ActionError("Invalid Steam app ID")
        root = HOME / ".local/share/Steam/steamapps"
        manifest = root / f"appmanifest_{appid}.acf"
        if not manifest.is_file() or manifest.is_symlink():
            raise ActionError("Steam manifest changed")
        game = action["install_dir"]
        path = Path(game)
        if path.parent != root / "common" or not path.is_dir() or path.is_symlink():
            raise ActionError("Steam install directory changed")
        for proc in Path("/proc").iterdir():
            if proc.name.isdigit():
                try:
                    if os.readlink(proc / "exe").startswith(str(path) + "/"):
                        raise ActionError("The game has a running process")
                except OSError:
                    pass
        size = run(["du", "-sx", "-B1", str(path)], 40)
        if size.returncode:
            raise ActionError("Game size could not be measured")
        return {"type": typ, "appid": appid, "manifest": str(manifest),
                "manifest_fingerprint": file_fingerprint(manifest),
                "install_dir": str(path), "install_mtime_ns": path.stat().st_mtime_ns,
                "bytes": int(size.stdout.split()[0]),
                "command": ["xdg-open", f"steam://uninstall/{appid}"],
                "restore": "Reinstall the game from the Steam library; Steam handles its own confirmation"}
    if typ == "trash_file":
        path = Path(action["path"])
        keep = Path(action["keep"])
        if not safe_home_file(path) or not safe_home_file(keep):
            raise ActionError("A compared file changed or is excluded")
        if path == keep or path.stat().st_nlink != 1:
            raise ActionError("Unsafe duplicate target")
        from .recommend import git_tracked
        if git_tracked(path):
            raise ActionError("The target is Git tracked")
        if action.get("digest") and (exact_digest(path) != action["digest"] or
                                     exact_digest(keep) != action["digest"]):
            raise ActionError("The duplicate files changed")
        return {"type": typ, "path": str(path), "keep": str(keep),
                "path_fingerprint": file_fingerprint(path),
                "keep_fingerprint": file_fingerprint(keep),
                "near_duplicate": bool(action.get("near_duplicate")),
                "command": ["gio", "trash", "--", str(path)],
                "restore": "Restore from Trash; disk space is freed only after Trash is emptied"}
    if typ == "trash_directory":
        path = Path(action["path"])
        if (not path.is_dir() or path.is_symlink() or not path.resolve().is_relative_to(HOME)
                or path.stat().st_uid != os.getuid()):
            raise ActionError("Directory changed or is outside the home directory")
        if action.get("project"):
            project = Path(action["project"])
            if path.parent != project or run(["git", "-C", str(project), "check-ignore", "-q", str(path)], 10).returncode:
                raise ActionError("Generated directory is no longer Git ignored")
            tracked = run(["git", "-C", str(project), "ls-files", "--", path.name], 10)
            if tracked.returncode or tracked.stdout.strip():
                raise ActionError("Generated directory contains Git tracked files")
        elif action.get("removed_package"):
            package = action["removed_package"]
            if path.name != package or path.parent not in (HOME / ".cache", HOME / ".local/share", HOME / ".config"):
                raise ActionError("Former package ownership is no longer clear")
            if run(["pacman", "-Qq", package], 10).returncode == 0:
                raise ActionError("Package was reinstalled")
        elif action.get("steam_orphan_shader"):
            appid = action["steam_orphan_shader"]
            root = HOME / ".local/share/Steam/steamapps"
            if not appid.isdigit() or path != root / "shadercache" / appid:
                raise ActionError("Unexpected Steam cache target")
            if (root / f"appmanifest_{appid}.acf").exists():
                raise ActionError("The Steam game was installed again")
            if run(["pgrep", "-xu", str(os.getuid()), "steam"], 5).returncode == 0:
                raise ActionError("Close Steam before reviewing this cache")
        else:
            raise ActionError("Directory has no verified owner")
        fingerprint, count = directory_fingerprint(path)
        size = run(["du", "-sx", "-B1", str(path)], 40)
        if size.returncode:
            raise ActionError("Directory size could not be measured")
        return {"type": typ, "path": str(path), "fingerprint": fingerprint,
                "items": count, "bytes_to_trash": int(size.stdout.split()[0]),
                "command": ["gio", "trash", "--", str(path)],
                "restore": "Restore the directory from Trash; free space appears only after Trash is emptied"}
    raise ActionError("Unsupported action type")


def preview(db: sqlite3.Connection, sid: str) -> dict:
    suggestion = _get(db, sid)
    if suggestion["status"] != "new":
        raise ActionError("Suggestion is no longer actionable")
    plan = _current_plan(suggestion)
    token = secrets.token_urlsafe(24)
    fingerprint = stable_id(suggestion["fingerprint"], dumps(plan))
    db.execute("INSERT INTO previews VALUES(?,?,?,?,?)",
               (token, sid, fingerprint, dumps(plan), now() + 300))
    db.commit()
    return {"suggestion": suggestion, "plan": plan, "token": token, "expires_at": now()+300}


def execute(db: sqlite3.Connection, sid: str, token: str) -> dict:
    if not settings().get("execution_enabled", False):
        raise ActionError("Execution is disabled until the first live report is reviewed")
    row = db.execute("SELECT * FROM previews WHERE token=? AND suggestion_id=?",
                     (token, sid)).fetchone()
    if not row or row["expires_at"] < now():
        raise ActionError("Preview expired; review the action again")
    suggestion = _get(db, sid)
    if suggestion["status"] != "new":
        raise ActionError("Suggestion is no longer actionable")
    plan = _current_plan(suggestion)
    if stable_id(suggestion["fingerprint"], dumps(plan)) != row["fingerprint"]:
        raise ActionError("The target or affected items changed; review again")
    typ = plan["type"]
    if typ in ("pacman_remove", "paccache"):
        argv = ["pkexec", "/usr/bin/python3", "/usr/local/libexec/storage-advisor/guarded_action.py",
                typ, plan.get("package", str(plan.get("keep", ""))), plan["guard_digest"]]
        result = run(argv, 300)
    elif typ == "docker_image_remove":
        result = run(plan["command"], 120)
    elif typ == "steam_uninstall":
        result = run(plan["command"], 30)
    elif typ in ("trash_file", "trash_directory"):
        result = run(plan["command"], 120)
    elif typ == "remove_cache_directory":
        path = Path(plan["path"])
        if directory_fingerprint(path, limit=100000)[0] != plan["tree_fingerprint"]:
            raise ActionError("Cache directory changed; review again")
        try:
            shutil.rmtree(path)
            result = type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        except OSError as exc:
            result = type("Result", (), {"returncode": 1, "stdout": "", "stderr": str(exc)})()
    else:
        raise ActionError("Unsupported action")
    db.execute("DELETE FROM previews WHERE token=?", (token,))
    detail = {"plan": plan, "exit_code": result.returncode,
              "output": (result.stdout + result.stderr)[-2000:]}
    decision = ("handed_off" if typ == "steam_uninstall" and result.returncode == 0
                else "accepted" if result.returncode == 0 else "failed")
    db.execute("INSERT INTO decisions(suggestion_id,decision,at,detail) VALUES(?,?,?,?)",
               (sid, decision, now(), dumps(detail)))
    db.execute("UPDATE suggestions SET status=?,updated_at=? WHERE id=?",
               ("pending_external" if decision == "handed_off" else
                "executed" if result.returncode == 0 else "failed", now(), sid))
    db.commit()
    return {"ok": result.returncode == 0, "pending_external": decision == "handed_off",
            "detail": detail}


def reject(db: sqlite3.Connection, sid: str) -> dict:
    suggestion = _get(db, sid)
    if suggestion["status"] != "new":
        raise ActionError("Suggestion is no longer open for review")
    db.execute("UPDATE suggestions SET status='rejected',updated_at=? WHERE id=?", (now(), sid))
    db.execute("INSERT INTO decisions(suggestion_id,decision,at) VALUES(?,?,?)",
               (sid, "rejected", now()))
    db.commit()
    return {"ok": True, "id": sid, "title": suggestion["title"]}
