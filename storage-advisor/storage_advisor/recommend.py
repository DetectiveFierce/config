from __future__ import annotations

import datetime as dt
import json
import os
import re
import sqlite3
import time
from collections import defaultdict
from pathlib import Path

from .common import HOME, dumps, now, run, safe_home_file, stable_id
from .db import artifact, edge
from .inventory import _bytes
from .similarity import app_embeddings, cosine, exact_digest, hamming, image_hash, minhash, pdf_text, signature_similarity


PROTECTED_PACKAGES = {"base", "filesystem", "glibc", "linux", "linux-firmware", "systemd",
                      "pacman", "sudo", "niri", "dms-shell", "networkmanager", "cryptsetup",
                      "grub", "efibootmgr", "mkinitcpio", "openssh", "dbus", "pipewire"}


def git_tracked(path: Path) -> bool:
    return run(["git", "-C", str(path.parent), "ls-files", "--error-unmatch", "--", path.name], 5).returncode == 0


def covered_days(db: sqlite3.Connection) -> int:
    oldest = db.execute("SELECT MIN(day) day FROM coverage WHERE source='exec'").fetchone()["day"]
    if not oldest or (dt.date.today() - dt.date.fromisoformat(oldest)).days < 59:
        return 0
    cutoff = (dt.date.today() - dt.timedelta(days=59)).isoformat()
    joint = db.execute("""SELECT COUNT(*) n FROM coverage e JOIN coverage n
      ON n.day=e.day AND n.minute=e.minute AND n.source='niri'
      WHERE e.source='exec' AND e.day>=?""", (cutoff,)).fetchone()["n"]
    return joint // 1440 if joint >= 60 * 1440 * 0.9 else 0


def _activity(db: sqlite3.Connection, aid: str) -> tuple[int, int]:
    row = db.execute("""SELECT COALESCE(SUM(count),0) hits,
      COALESCE(MAX(day),'') last_day FROM activity WHERE artifact_id=?
      AND kind IN ('focus','exec_foreground','open_foreground') AND day>=date('now','-365 days')""",
      (aid,)).fetchone()
    if not row or not row["last_day"]:
        return 0, 0
    try:
        days_ago = (dt.date.today() - dt.date.fromisoformat(row["last_day"])).days
    except ValueError:
        days_ago = 0
    return row["hits"], days_ago


def _app_activity(db: sqlite3.Connection, row: sqlite3.Row) -> tuple[int, int]:
    meta = json.loads(row["meta"])
    desktop_id = Path(row["locator"]).stem
    candidates = {f"session:{desktop_id}", f"session:{row['locator']}"}
    exe = meta.get("exec")
    if exe:
        candidates.add(f"exe:{exe}")
        for link in db.execute("SELECT src FROM edges WHERE dst=? AND relation='window_process'", (f"exe:{exe}",)):
            candidates.add(link["src"])
    marks = [_activity(db, aid) for aid in candidates]
    return sum(hits for hits, _ in marks), min((age for hits, age in marks if hits), default=0)


def _emit(db: sqlite3.Connection, *, kind: str, group: str, target: str,
          title: str, claim: str, evidence: dict, action: dict,
          bytes_saved: int, risk: str, confidence: str, fingerprint: str) -> None:
    sid = stable_id(kind, target)
    old = db.execute("SELECT status,fingerprint FROM suggestions WHERE id=?", (sid,)).fetchone()
    if old and old["status"] == "rejected" and old["fingerprint"] == fingerprint:
        return
    status = "new" if not old or old["fingerprint"] != fingerprint or old["status"] in ("stale", "failed") else old["status"]
    db.execute("""INSERT INTO suggestions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(id) DO UPDATE SET title=excluded.title,claim=excluded.claim,
      evidence=excluded.evidence,action=excluded.action,
      estimated_bytes=excluded.estimated_bytes,risk=excluded.risk,
      confidence=excluded.confidence,fingerprint=excluded.fingerprint,
      status=excluded.status,updated_at=excluded.updated_at""",
      (sid, kind, group, target, title, claim, dumps(evidence), dumps(action),
       bytes_saved, risk, confidence, fingerprint, status, now(), now()))
    db.commit()


def _score(row: sqlite3.Row, db: sqlite3.Connection) -> float:
    # A small, transparent ranking prior; accepted/rejected feedback adjusts groups.
    benefit = min(5.0, max(0, row["estimated_bytes"]) / (1024**3))
    risk = {"low": 0, "medium": 1.5, "high": 3}.get(row["risk"], 3)
    confidence = {"high": 1, "medium": 0.5, "low": 0}.get(row["confidence"], 0)
    feedback = db.execute("""SELECT decision,COUNT(*) n FROM decisions d JOIN suggestions s
      ON s.id=d.suggestion_id WHERE s.group_name=? GROUP BY decision""",
      (row["group_name"],)).fetchall()
    accepted = sum(x["n"] for x in feedback if x["decision"] == "accepted")
    rejected = sum(x["n"] for x in feedback if x["decision"] == "rejected")
    personal = (accepted + 2) / (accepted + rejected + 4)
    evidence = json.loads(row["evidence"])
    future_need = float(evidence.get("future_need_indicator", 0))
    recent = db.execute("""SELECT COALESCE(SUM(count),0) n FROM activity
      WHERE artifact_id=? AND kind='open_foreground' AND day>=date('now','-30 days')""",
      (row["target_id"],)).fetchone()["n"]
    return benefit + confidence - risk + 2 * personal - 2 * future_need - min(3, 0.5 * recent)


def report(db: sqlite3.Connection, limit: int = 12, status: str = "new") -> list[dict]:
    rows = db.execute("SELECT * FROM suggestions WHERE status=?", (status,)).fetchall()
    groups: dict[str, list] = defaultdict(list)
    for row in rows:
        groups[row["group_name"]].append(row)
    for group in groups:
        groups[group].sort(key=lambda row: _score(row, db), reverse=True)
    chosen = []
    order = ("storage", "software", "files")
    while len(chosen) < limit and any(groups.values()):
        for group in order:
            if groups[group] and len(chosen) < limit:
                chosen.append(dict(groups[group].pop(0)))
    for item in chosen:
        item["evidence"] = json.loads(item["evidence"])
        item["action"] = json.loads(item["action"])
    return chosen


def package_orphans(db: sqlite3.Connection) -> int:
    rows = db.execute("SELECT * FROM artifacts WHERE kind='package'").fetchall()
    referenced_exes = {r["dst"] for r in db.execute("""SELECT dst FROM edges
      WHERE relation='references_executable'""")}
    referenced_exes.update(r["dst"] for r in db.execute("""SELECT e2.dst FROM edges e1
      JOIN edges e2 ON e1.dst=e2.src WHERE e1.relation='uses_tool'
      AND e2.relation='resolves_to'"""))
    needed_packages = set()
    for exe in referenced_exes:
        result = run(["pacman", "-Qoq", exe.removeprefix("exe:")], 8)
        if result.returncode == 0:
            needed_packages.add(result.stdout.strip())
    count = 0
    for row in sorted(rows, key=lambda x: x["size_bytes"], reverse=True):
        meta = json.loads(row["meta"])
        name = row["locator"]
        if (not meta.get("orphan") or name in PROTECTED_PACKAGES | needed_packages or
                row["size_bytes"] < 20*1024**2):
            continue
        # Orphan is a package-manager fact, but optional use remains possible.
        preview = run(["pacman", "-Rs", "--print-format", "%n", name], 12)
        targets = preview.stdout.splitlines() if preview.returncode == 0 else []
        if not targets or any(x in PROTECTED_PACKAGES for x in targets):
            continue
        from .actions import package_reclaimable_bytes
        try:
            recoverable = package_reclaimable_bytes(targets)
        except Exception:
            continue
        _emit(db, kind="orphan_package", group="software", target=row["id"],
              title=f"Review orphaned package {name}",
              claim=f"Pacman marks {name} as an unneeded dependency. A removal preview includes {len(targets)} package(s); optional use still needs review.",
              evidence={"pacman_orphan": True, "targets": targets,
                        "installed_bytes_in_transaction": recoverable},
              action={"type": "pacman_remove", "package": name},
              bytes_saved=recoverable, risk="medium", confidence="medium",
              fingerprint=stable_id(row["fingerprint"], targets))
        count += 1
        if count >= 20:
            break
    return count


def package_cache(db: sqlite3.Connection) -> int:
    from .actions import paccache_candidates
    paths = paccache_candidates(3)
    size = sum(p.stat().st_size for p in paths if p.is_file())
    if size < 200*1024**2:
        return 0
    _emit(db, kind="pacman_cache", group="storage", target="dir:/var/cache/pacman/pkg",
          title="Retire older pacman package archives",
          claim=f"Paccache identifies {len(paths)} archives beyond the newest three versions per package.",
          evidence={"count": len(paths), "paths": [str(x) for x in paths[:30]],
                    "remaining_paths": max(0, len(paths)-30), "bytes": size},
          action={"type": "paccache", "keep": 3}, bytes_saved=size,
          risk="low", confidence="high", fingerprint=stable_id(*paths, size))
    return 1


def yay_cache(db: sqlite3.Connection) -> int:
    root = HOME / ".cache/yay"
    if not root.is_dir():
        return 0
    count = 0
    for directory in root.iterdir():
        if not directory.is_dir() or directory.is_symlink():
            continue
        owner_name = next((name for name in (directory.name, directory.name + "-bin")
                           if db.execute("SELECT 1 FROM artifacts WHERE id=? AND kind='package'",
                                         (f"pkg:{name}",)).fetchone()), None)
        # Only nominate build directories for installed packages, after seven quiet days.
        if not owner_name or now() - int(directory.stat().st_mtime) < 7*86400:
            continue
        result = run(["du", "-sx", "-B1", str(directory)], 20)
        try:
            size = int(result.stdout.split()[0])
        except (ValueError, IndexError):
            continue
        if size < 500*1024**2:
            continue
        aid = f"dir:{directory}"
        artifact(db, aid, "directory", str(directory), stable_id(directory, directory.stat().st_mtime_ns, size), size,
                 {"owner_package": owner_name, "regenerable": True})
        edge(db, f"pkg:{owner_name}", aid, "build_cache")
        _emit(db, kind="yay_build_cache", group="storage", target=aid,
              title=f"Review yay build cache for {directory.name}",
              claim=f"The installed package has a {size/1024**3:.1f} GiB build directory that has not changed for at least seven days. It can be rebuilt, but this copy may speed a future update.",
              evidence={"owner_package": owner_name, "path": str(directory), "bytes": size},
              action={"type": "remove_cache_directory", "path": str(directory)},
              bytes_saved=size, risk="medium", confidence="high",
              fingerprint=stable_id(directory, directory.stat().st_mtime_ns, size))
        count += 1
    return count


def generated_projects(db: sqlite3.Connection) -> int:
    """Nominate substantial, Git-ignored build output without touching source."""
    count = 0
    running = set()
    for proc in Path("/proc").iterdir():
        if proc.name.isdigit():
            try:
                running.add(os.readlink(proc / "exe"))
            except OSError:
                pass
    projects = db.execute("SELECT * FROM artifacts WHERE kind='project'").fetchall()
    for project in projects:
        root = Path(project["locator"])
        for name in ("target", ".next", "dist", "build", ".cache"):
            path = root / name
            if not path.is_dir() or path.is_symlink() or path.stat().st_uid != os.getuid():
                continue
            if any(exe.startswith(str(path) + "/") for exe in running):
                continue
            if run(["git", "-C", str(root), "check-ignore", "-q", str(path)], 10).returncode:
                continue
            tracked = run(["git", "-C", str(root), "ls-files", "--", name], 10)
            if tracked.returncode or tracked.stdout.strip():
                continue
            size_result = run(["du", "-sx", "-B1", str(path)], 40)
            if size_result.returncode:
                continue
            size = int(size_result.stdout.split()[0])
            if size < 500 * 1024**2:
                continue
            aid = f"dir:{path}"
            fingerprint = stable_id(path, path.stat().st_mtime_ns, size)
            artifact(db, aid, "directory", str(path), fingerprint, size,
                     {"project": str(root), "generated": True})
            edge(db, project["id"], aid, "generated_output", {"git_ignored": True})
            _emit(db, kind="project_generated", group="storage", target=aid,
                  title=f"Review generated {name} in {root.name}",
                  claim=f"This {size/1024**3:.1f} GiB directory is Git ignored build output. The project remains; the output may need rebuilding after Trash is emptied.",
                  evidence={"project": str(root), "path": str(path), "bytes_to_trash": size,
                            "git_ignored": True},
                  action={"type": "trash_directory", "path": str(path), "project": str(root)},
                  bytes_saved=0, risk="medium", confidence="high", fingerprint=fingerprint)
            count += 1
            if count >= 12:
                return count
    return count


def removed_app_data(db: sqlite3.Connection) -> int:
    """Use transaction history and exact directory names as a conservative lead."""
    try:
        log = Path("/var/log/pacman.log").read_text(errors="replace")[-2_000_000:]
    except OSError:
        return 0
    removed = set(re.findall(r"\[ALPM\] removed ([a-zA-Z0-9@+._-]+) \(", log))
    active_projects = [Path(row["locator"]).name for row in db.execute(
        "SELECT locator FROM artifacts WHERE kind='project'").fetchall()]
    count = 0
    for package in sorted(removed):
        if db.execute("SELECT 1 FROM artifacts WHERE id=? AND kind='package'", (f"pkg:{package}",)).fetchone():
            continue
        if any(name.startswith(package) or package.startswith(name) for name in active_projects):
            continue
        for base in (HOME / ".cache", HOME / ".local/share", HOME / ".config"):
            path = base / package
            if not path.is_dir() or path.is_symlink() or path.stat().st_uid != os.getuid():
                continue
            if now() - int(path.stat().st_mtime) < 30 * 86400:
                continue
            result = run(["du", "-sx", "-B1", str(path)], 30)
            if result.returncode:
                continue
            size = int(result.stdout.split()[0])
            if size < 200 * 1024**2:
                continue
            aid = f"dir:{path}"
            fingerprint = stable_id(path, path.stat().st_mtime_ns, size)
            artifact(db, aid, "directory", str(path), fingerprint, size,
                     {"former_package": package})
            edge(db, f"pkg:{package}", aid, "possible_residue", {"name_match": True, "pacman_removed": True})
            _emit(db, kind="removed_app_data", group="software", target=aid,
                  title=f"Review data left by {package}",
                  claim=f"Pacman recorded removal of {package}; a same-named {size/1024**3:.1f} GiB directory remains. Check whether it holds personal data before moving it to Trash.",
                  evidence={"package": package, "path": str(path), "bytes_to_trash": size,
                            "owner_evidence": "pacman removal plus exact directory name"},
                  action={"type": "trash_directory", "path": str(path), "removed_package": package},
                  bytes_saved=0, risk="high", confidence="low", fingerprint=fingerprint)
            count += 1
            if count >= 10:
                return count
    return count


def steam_orphan_shaders(db: sqlite3.Connection) -> int:
    root = HOME / ".local/share/Steam/steamapps"
    shader_root = root / "shadercache"
    if not shader_root.is_dir():
        return 0
    count = 0
    for path in shader_root.iterdir():
        appid = path.name
        if (not appid.isdigit() or not path.is_dir() or path.is_symlink()
                or (root / f"appmanifest_{appid}.acf").exists()
                or now() - int(path.stat().st_mtime) < 30 * 86400):
            continue
        result = run(["du", "-sx", "-B1", str(path)], 30)
        if result.returncode:
            continue
        size = int(result.stdout.split()[0])
        if size < 100 * 1024**2:
            continue
        aid = f"dir:{path}"
        fingerprint = stable_id(path, path.stat().st_mtime_ns, size)
        artifact(db, aid, "directory", str(path), fingerprint, size,
                 {"steam_appid": appid, "shader_cache": True})
        edge(db, f"steam:{appid}", aid, "shader_cache", {"manifest_absent": True})
        _emit(db, kind="steam_orphan_shader", group="storage", target=aid,
              title=f"Review shader cache for uninstalled Steam app {appid}",
              claim=f"Steam has no installed manifest for app {appid}, but its {size/1024**3:.1f} GiB shader cache remains. Steam can regenerate it if the game returns.",
              evidence={"appid": appid, "path": str(path), "bytes_to_trash": size,
                        "game_manifest_absent": True},
              action={"type": "trash_directory", "path": str(path), "steam_orphan_shader": appid},
              bytes_saved=0, risk="low", confidence="high", fingerprint=fingerprint)
        count += 1
        if count >= 12:
            break
    return count


def steam_games(db: sqlite3.Connection) -> int:
    if covered_days(db) < 54:
        return 0
    cutoff = (dt.date.today() - dt.timedelta(days=59)).isoformat()
    count = 0
    for row in db.execute("SELECT * FROM artifacts WHERE kind='steam_game'").fetchall():
        if row["size_bytes"] < 5 * 1024**3:
            continue
        # A past path-based game launch is required to know this collector can
        # identify the game. Proton-only games may lack this evidence.
        if not db.execute("SELECT 1 FROM edges WHERE src=? AND relation='launches_executable'",
                          (row["id"],)).fetchone():
            continue
        recent = db.execute("""SELECT COALESCE(SUM(count),0) n FROM activity
          WHERE artifact_id=? AND day>=? AND kind IN ('focus','exec_foreground')""",
          (row["id"], cutoff)).fetchone()["n"]
        if recent:
            continue
        meta = json.loads(row["meta"])
        path = Path(meta["install_dir"])
        manifest = HOME / ".local/share/Steam/steamapps" / f"appmanifest_{row['locator']}.acf"
        if not path.is_dir() or path.is_symlink() or not manifest.is_file():
            continue
        measured = run(["du", "-sx", "-B1", str(path)], 40)
        if measured.returncode:
            continue
        game_bytes = int(measured.stdout.split()[0])
        aid = row["id"]
        _emit(db, kind="steam_game", group="software", target=aid,
              title=f"Review Steam game {meta['name']}",
              claim=f"This game has no observed foreground play across 60 calendar days with at least 90% joint collector coverage. Earlier launches prove the collector can identify it. Steam handles the uninstall confirmation.",
              evidence={"appid": row["locator"], "install_dir": str(path),
                        "game_installed_bytes": game_bytes,
                        "shader_cache_separate": meta["shadercache"],
                        "compatibility_data_separate": meta["compatdata"],
                        "prior_game_launch_observed": True},
              action={"type": "steam_uninstall", "appid": row["locator"],
                      "install_dir": str(path)}, bytes_saved=game_bytes,
              risk="medium", confidence="medium",
              fingerprint=stable_id(row["fingerprint"], manifest.stat().st_mtime_ns))
        count += 1
    return count


def reconcile_steam_handoffs(db: sqlite3.Connection) -> None:
    for row in db.execute("SELECT id,action,updated_at FROM suggestions WHERE status='pending_external'").fetchall():
        action = json.loads(row["action"])
        if action.get("type") != "steam_uninstall":
            continue
        appid = action["appid"]
        manifest = HOME / ".local/share/Steam/steamapps" / f"appmanifest_{appid}.acf"
        if not manifest.exists():
            db.execute("UPDATE suggestions SET status='executed',updated_at=? WHERE id=?", (now(), row["id"]))
            db.execute("INSERT INTO decisions(suggestion_id,decision,at,detail) VALUES(?,?,?,?)",
                       (row["id"], "accepted", now(), dumps({"steam_manifest_removed": True})))
        elif now() - row["updated_at"] > 86400:
            db.execute("UPDATE suggestions SET status='new',updated_at=? WHERE id=?", (now(), row["id"]))
            db.execute("INSERT INTO decisions(suggestion_id,decision,at,detail) VALUES(?,?,?,?)",
                       (row["id"], "not_completed", now(), dumps({"steam_manifest_present": True})))
    db.commit()


def docker_images(db: sqlite3.Connection) -> int:
    images = db.execute("SELECT * FROM artifacts WHERE kind='docker_image'").fetchall()
    counts = defaultdict(int)
    for row in db.execute("SELECT dst FROM edges WHERE relation='uses_layer'"):
        counts[row["dst"]] += 1
    count = 0
    for image in sorted(images, key=lambda r: json.loads(r["meta"]).get("unique_bytes", 0), reverse=True):
        meta = json.loads(image["meta"])
        if meta.get("containers") or meta.get("tags") or meta.get("unique_bytes", 0) < 20*1024**2:
            continue
        unique = int(meta.get("unique_bytes", 0))
        _emit(db, kind="docker_dangling", group="storage", target=image["id"],
              title=f"Review unused Docker image {image['locator'][7:19]}",
              claim="This dangling image has no associated container. Its apparent size includes layers shared with other images, so recovery is verified before removal.",
              evidence={"image_id": image["locator"], "virtual_bytes": image["size_bytes"],
                        "unique_bytes": unique,
                        "shared_layer_count": sum(counts[e["dst"]] > 1 for e in db.execute(
                            "SELECT dst FROM edges WHERE src=? AND relation='uses_layer'", (image["id"],)))},
              action={"type": "docker_image_remove", "image_id": image["locator"]},
              bytes_saved=unique, risk="medium", confidence="medium", fingerprint=image["fingerprint"])
        count += 1
        if count >= 10:
            break
    return count


def exact_duplicates(db: sqlite3.Connection) -> int:
    rows = db.execute("SELECT * FROM artifacts WHERE kind='file' AND size_bytes>=?",
                      (20*1024**2,)).fetchall()
    by_size = defaultdict(list)
    for row in rows:
        meta = json.loads(row["meta"])
        if meta.get("nlink", 1) != 1:
            continue
        by_size[row["size_bytes"]].append(row)
    count = 0
    for group in by_size.values():
        if len(group) < 2:
            continue
        by_hash = defaultdict(list)
        for row in group[:30]:
            path = Path(row["locator"])
            if not safe_home_file(path):
                continue
            try:
                by_hash[exact_digest(path)].append(row)
            except OSError:
                pass
        for digest, copies in by_hash.items():
            if len(copies) < 2:
                continue
            # Prefer a copy outside Downloads and then the one used most recently.
            copies.sort(key=lambda x: ("/Downloads/" in x["locator"],
                                       -json.loads(x["meta"]).get("atime", 0)))
            keep = copies[0]
            for remove in copies[1:]:
                if remove["locator"] == keep["locator"]:
                    continue
                if git_tracked(Path(remove["locator"])):
                    continue
                edge(db, remove["id"], keep["id"], "exact_duplicate", {"digest": digest})
                _emit(db, kind="exact_duplicate", group="files", target=remove["id"],
                      title=f"Exact copy: {Path(remove['locator']).name}",
                      claim="These files have identical size and a full matching digest. Keep the more established copy and send this one to Trash after review.",
                      evidence={"remove": remove["locator"], "keep": keep["locator"],
                                "digest": digest, "bytes": remove["size_bytes"]},
                      action={"type": "trash_file", "path": remove["locator"],
                              "keep": keep["locator"], "digest": digest},
                      bytes_saved=0, risk="medium", confidence="high",
                      fingerprint=stable_id(remove["fingerprint"], keep["fingerprint"], digest))
                count += 1
    return count


def near_duplicates(db: sqlite3.Connection) -> int:
    # Content is processed in memory only and limited to eligible PDF/image sets.
    rows = db.execute("SELECT * FROM artifacts WHERE kind='file' AND size_bytes<=?",
                      (100*1024**2,)).fetchall()
    pdfs = [r for r in rows if Path(r["locator"]).suffix.lower() == ".pdf"][:120]
    images = [r for r in rows if Path(r["locator"]).suffix.lower() in
              (".png", ".jpg", ".jpeg", ".webp")][:180]
    count = 0
    signatures = []
    for row in pdfs:
        path = Path(row["locator"])
        if safe_home_file(path):
            sig = minhash(pdf_text(path))
            if sig:
                signatures.append((row, sig))
    # Bucket by matching minhash bands to avoid all-pairs document comparison.
    buckets = defaultdict(list)
    pairs = set()
    for i, (_, sig) in enumerate(signatures):
        for band in range(8):
            key = (band, sig[band*4:(band+1)*4])
            for j in buckets[key]:
                pairs.add((j, i))
            buckets[key].append(i)
    for a, b in sorted(pairs):
        first, left = signatures[a]
        second, right = signatures[b]
        similarity = signature_similarity(left, right)
        if similarity < 0.85 or first["locator"] == second["locator"]:
            continue
        older, newer = sorted((first, second), key=lambda x: json.loads(x["meta"]).get("mtime", 0))
        if "/Downloads/" not in older["locator"]:
            continue
        count += _near_emit(db, older, newer, "pdf", similarity)
    hashes = []
    for row in images:
        path = Path(row["locator"])
        if safe_home_file(path):
            value = image_hash(path)
            if value:
                hashes.append((row, value))
    for i, (first, h1) in enumerate(hashes):
        for second, h2 in hashes[i+1:]:
            if first["locator"] == second["locator"] or hamming(h1[0], h2[0]) > 6:
                continue
            # Keep the higher-resolution image; present both for visual review.
            keep, remove = sorted(((first, h1), (second, h2)),
                                  key=lambda x: x[1][1]*x[1][2], reverse=True)
            if "/Downloads/" not in remove[0]["locator"]:
                continue
            count += _near_emit(db, remove[0], keep[0], "image", 1-hamming(h1[0], h2[0])/63)
            if count >= 25:
                return count
    return count


def _near_emit(db, remove, keep, kind, similarity):
    if git_tracked(Path(remove["locator"])):
        return 0
    if kind == "pdf":
        remove_words = len(pdf_text(Path(remove["locator"])).split())
        keep_words = len(pdf_text(Path(keep["locator"])).split())
        differences = {"sampled_words_remove": remove_words,
                       "sampled_words_keep": keep_words,
                       "word_count_delta": remove_words - keep_words}
    else:
        old = image_hash(Path(remove["locator"]))
        retained = image_hash(Path(keep["locator"]))
        differences = {"remove_dimensions": list(old[1:]) if old else None,
                       "keep_dimensions": list(retained[1:]) if retained else None,
                       "perceptual_hash_distance": hamming(old[0], retained[0]) if old and retained else None}
    edge(db, remove["id"], keep["id"], "near_duplicate", {"similarity": similarity, "type": kind})
    _emit(db, kind=f"near_{kind}", group="files", target=remove["id"],
          title=f"Review similar {kind}s: {Path(remove['locator']).name}",
          claim=f"The files appear {similarity:.0%} similar by a {kind}-specific fingerprint. Differences may matter; inspect both before sending one to Trash.",
          evidence={"remove": remove["locator"], "keep": keep["locator"],
                    "similarity": round(similarity, 3), "bytes": remove["size_bytes"],
                    "comparison_required": True, "differences": differences},
          action={"type": "trash_file", "path": remove["locator"], "keep": keep["locator"],
                  "near_duplicate": True},
          bytes_saved=0, risk="high", confidence="medium",
          fingerprint=stable_id(remove["fingerprint"], keep["fingerprint"], round(similarity, 2)))
    return 1


def app_substitutes(db: sqlite3.Connection) -> int:
    if covered_days(db) < 54:
        return 0
    rows = db.execute("SELECT * FROM artifacts WHERE kind='app'").fetchall()
    descriptions = {}
    for row in rows:
        meta = json.loads(row["meta"])
        descriptions[row["id"]] = " ".join((meta.get("name", ""), meta.get("comment", ""),
                                             meta.get("categories", "")))
    vectors = app_embeddings(descriptions)
    protected_exes = {r["dst"] for r in db.execute("""SELECT dst FROM edges WHERE relation='references_executable'""")}
    protected_exes.update(r["dst"] for r in db.execute("""SELECT e2.dst FROM edges e1
      JOIN edges e2 ON e1.dst=e2.src WHERE e1.relation='uses_tool' AND e2.relation='resolves_to'"""))
    category_counts = defaultdict(lambda: [0, 0])
    for app in rows:
        metadata = json.loads(app["meta"])
        category = next((c for c in metadata.get("categories", "").split(";") if c), "other")
        category_counts[category][1] += 1
        category_counts[category][0] += int(_app_activity(db, app)[0] > 0)
    count = 0
    for i, left in enumerate(rows):
        lm = json.loads(left["meta"])
        lh, lage = _app_activity(db, left)
        if lh or lm.get("default") or f"exe:{lm.get('exec', '')}" in protected_exes:
            continue
        category = next((c for c in lm.get("categories", "").split(";") if c), "other")
        active, total = category_counts[category]
        prior = (active + 2) / (total + 4)
        for right in rows[i+1:]:
            rm = json.loads(right["meta"])
            rh, _ = _app_activity(db, right)
            shared = set(lm.get("mimes", [])) & set(rm.get("mimes", []))
            if not shared or rh < 5:
                continue
            sim = cosine(vectors[left["id"]], vectors[right["id"]]) if vectors else 0
            if sim < 0.72:
                continue
            # A substitute may cover common MIME types but not unique features.
            _emit(db, kind="app_overlap", group="software", target=left["id"],
                  title=f"Review overlap: {lm.get('name')} and {rm.get('name')}",
                  claim=f"{lm.get('name')} has no observed foreground use across 60 calendar days with at least 90% joint collector coverage; {rm.get('name')} was used {rh} times and shares {len(shared)} file types. Check unique features before removing anything.",
                  evidence={"substitute": right["id"], "shared_mimes": sorted(shared)[:20],
                            "semantic_similarity": round(sim, 3), "substitute_sessions": rh,
                            "future_need_indicator": round(prior, 3),
                            "category_peer_use": {"active": active, "total": total}},
                  action={"type": "guided_app", "app": left["id"]},
                  bytes_saved=0, risk="high", confidence="low",
                  fingerprint=stable_id(left["fingerprint"], right["fingerprint"], rh))
            count += 1
            break
    return count


def generate(db: sqlite3.Connection) -> dict:
    reconcile_steam_handoffs(db)
    db.execute("UPDATE suggestions SET status='stale' WHERE status='new'")
    db.commit()
    stats = {}
    for name, func in (("orphan_packages", package_orphans), ("pacman_cache", package_cache),
                       ("yay_caches", yay_cache), ("project_generated", generated_projects),
                       ("removed_app_data", removed_app_data), ("docker_images", docker_images),
                       ("steam_orphan_shaders", steam_orphan_shaders),
                       ("steam_games", steam_games),
                       ("exact_duplicates", exact_duplicates),
                       ("near_duplicates", near_duplicates), ("app_substitutes", app_substitutes)):
        for attempt in range(3):
            try:
                db.commit()
                stats[name] = func(db)
                db.commit()
                break
            except sqlite3.OperationalError as exc:
                db.rollback()
                if "locked" in str(exc).lower() and attempt < 2:
                    time.sleep(0.3 * (attempt + 1))
                    continue
                stats[name] = {"error": str(exc)[:180]}
                break
            except Exception as exc:
                db.rollback()
                stats[name] = {"error": str(exc)[:180]}
                break
    return stats
