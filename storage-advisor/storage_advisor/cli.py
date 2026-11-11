from __future__ import annotations

import argparse
import fcntl
import json
import os
import sqlite3
import sys
from pathlib import Path

from .actions import ActionError, execute, preview, reject
from .common import RUNTIME, STATE, WATCHLIST, dumps, now, save_settings, settings
from .db import database, prune, row_json
from .evaluation import backtest
from .inventory import inventory
from .recommend import generate, report


def _write_watchlist(db) -> None:
    RUNTIME.mkdir(mode=0o700, parents=True, exist_ok=True)
    rows = db.execute("""SELECT a.locator FROM suggestions s JOIN artifacts a ON a.id=s.target_id
      WHERE s.status='new' AND a.kind='file' ORDER BY s.estimated_bytes DESC LIMIT 1000""").fetchall()
    temp = WATCHLIST.with_suffix(".tmp")
    with open(temp, "w") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.writelines(row["locator"] + "\n" for row in rows)
    os.replace(temp, WATCHLIST)


def analyze(db, *, full: bool, scheduled: bool) -> dict:
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    with open(STATE / "scan.lock", "a+") as lock:
        os.fchmod(lock.fileno(), 0o600)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"busy": True, "message": "An analysis is already running"}
        return _analyze_locked(db, full=full, scheduled=scheduled)


def _analyze_locked(db, *, full: bool, scheduled: bool) -> dict:
    cadence = settings()["cadence"]
    if scheduled:
        last = db.execute("SELECT finished_at FROM scans WHERE status='ok' ORDER BY id DESC LIMIT 1").fetchone()
        interval = 86400 if cadence == "daily" else 7*86400
        if last and last["finished_at"] and now() - last["finished_at"] < interval:
            return {"skipped": "not due", "cadence": cadence}
    cur = db.execute("INSERT INTO scans(started_at,mode,status) VALUES(?,?,?)",
                     (now(), "full" if full else "incremental", "running"))
    db.commit()
    try:
        scanned = inventory(db, full)
        suggested = generate(db)
        prune(db)
        _write_watchlist(db)
        outcome = {"inventory": scanned, "suggestions": suggested}
        scan_status = "partial" if any(isinstance(value, dict) and "error" in value
                                       for value in suggested.values()) else "ok"
        db.execute("UPDATE scans SET finished_at=?,status=?,stats=? WHERE id=?",
                   (now(), scan_status, dumps(outcome), cur.lastrowid))
        db.commit()
        return outcome
    except Exception as exc:
        db.execute("UPDATE scans SET finished_at=?,status='failed',stats=? WHERE id=?",
                   (now(), dumps({"error": str(exc)}), cur.lastrowid))
        db.commit()
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="storage-advisor")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze_cmd = sub.add_parser("analyze")
    analyze_cmd.add_argument("--full", action="store_true")
    analyze_cmd.add_argument("--scheduled", action="store_true")
    listing = sub.add_parser("list")
    listing.add_argument("--status", choices=("new", "rejected", "executed", "failed"), default="new")
    listing.add_argument("--limit", type=int, default=12)
    for command in ("preview", "reject"):
        sub.add_parser(command).add_argument("id")
    exe = sub.add_parser("execute")
    exe.add_argument("id")
    exe.add_argument("--token", required=True)
    sub.add_parser("history")
    sub.add_parser("backtest")
    config = sub.add_parser("settings")
    config.add_argument("--cadence", choices=("daily", "weekly"))
    execution = config.add_mutually_exclusive_group()
    execution.add_argument("--enable-execution", action="store_true")
    execution.add_argument("--disable-execution", action="store_true")
    sub.add_parser("status")
    args = parser.parse_args(argv)
    try:
        with database() as db:
            if args.command == "analyze":
                output = analyze(db, full=args.full, scheduled=args.scheduled)
            elif args.command == "list":
                output = {"suggestions": report(db, max(1, min(100, args.limit)), args.status),
                          "cadence": settings()["cadence"],
                          "execution_enabled": settings()["execution_enabled"]}
            elif args.command == "preview":
                output = preview(db, args.id)
            elif args.command == "execute":
                output = execute(db, args.id, args.token)
            elif args.command == "reject":
                output = reject(db, args.id)
            elif args.command == "history":
                rows = db.execute("""SELECT d.*,s.title,s.group_name FROM decisions d
                  LEFT JOIN suggestions s ON s.id=d.suggestion_id
                  ORDER BY d.id DESC LIMIT 100""").fetchall()
                output = {"history": [row_json(row) for row in rows]}
            elif args.command == "backtest":
                output = backtest(db)
            elif args.command == "settings":
                output = settings()
                if args.cadence or args.enable_execution or args.disable_execution:
                    if args.cadence:
                        output["cadence"] = args.cadence
                    if args.enable_execution:
                        output["execution_enabled"] = True
                    if args.disable_execution:
                        output["execution_enabled"] = False
                    save_settings(output)
            elif args.command == "status":
                last = db.execute("SELECT * FROM scans ORDER BY id DESC LIMIT 1").fetchone()
                coverage = db.execute("SELECT source,COUNT(DISTINCT day) days FROM coverage GROUP BY source").fetchall()
                output = {"last_scan": row_json(last) if last else None,
                          "coverage": [dict(x) for x in coverage],
                          "cadence": settings()["cadence"]}
            else:
                raise AssertionError(args.command)
        print(dumps(output))
        return 0
    except (ActionError, OSError, ValueError, sqlite3.Error) as exc:
        print(dumps({"error": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
