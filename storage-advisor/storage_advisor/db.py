from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager

from .common import DB_PATH, STATE, dumps, now


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS artifacts (
 id TEXT PRIMARY KEY, kind TEXT NOT NULL, locator TEXT NOT NULL,
 fingerprint TEXT NOT NULL, size_bytes INTEGER NOT NULL DEFAULT 0,
 meta TEXT NOT NULL DEFAULT '{}', seen_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS artifacts_kind ON artifacts(kind);
CREATE TABLE IF NOT EXISTS edges (
 src TEXT NOT NULL, dst TEXT NOT NULL, relation TEXT NOT NULL,
 evidence TEXT NOT NULL DEFAULT '{}', seen_at INTEGER NOT NULL,
 PRIMARY KEY(src,dst,relation)
);
CREATE INDEX IF NOT EXISTS edges_dst ON edges(dst,relation);
CREATE TABLE IF NOT EXISTS activity (
 day TEXT NOT NULL, artifact_id TEXT NOT NULL, kind TEXT NOT NULL,
 count INTEGER NOT NULL DEFAULT 0, seconds INTEGER NOT NULL DEFAULT 0,
 PRIMARY KEY(day,artifact_id,kind)
);
CREATE TABLE IF NOT EXISTS coverage (
 day TEXT NOT NULL, source TEXT NOT NULL, minute INTEGER NOT NULL,
 PRIMARY KEY(day,source,minute)
);
CREATE TABLE IF NOT EXISTS suggestions (
 id TEXT PRIMARY KEY, kind TEXT NOT NULL, group_name TEXT NOT NULL,
 target_id TEXT NOT NULL, title TEXT NOT NULL, claim TEXT NOT NULL,
 evidence TEXT NOT NULL, action TEXT NOT NULL, estimated_bytes INTEGER NOT NULL,
 risk TEXT NOT NULL, confidence TEXT NOT NULL, fingerprint TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'new', created_at INTEGER NOT NULL,
 updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS suggestions_status ON suggestions(status,group_name);
CREATE TABLE IF NOT EXISTS decisions (
 id INTEGER PRIMARY KEY, suggestion_id TEXT NOT NULL, decision TEXT NOT NULL,
 at INTEGER NOT NULL, detail TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS previews (
 token TEXT PRIMARY KEY, suggestion_id TEXT NOT NULL, fingerprint TEXT NOT NULL,
 plan TEXT NOT NULL, expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS scans (
 id INTEGER PRIMARY KEY, started_at INTEGER NOT NULL, finished_at INTEGER,
 mode TEXT NOT NULL, status TEXT NOT NULL, stats TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS measurements (
 artifact_id TEXT NOT NULL, day TEXT NOT NULL, size_bytes INTEGER NOT NULL,
 PRIMARY KEY(artifact_id,day)
);
"""


def connect() -> sqlite3.Connection:
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(STATE, 0o700)
    connection = sqlite3.connect(DB_PATH, timeout=30)
    os.chmod(DB_PATH, 0o600)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.executescript(SCHEMA)
    return connection


@contextmanager
def database():
    connection = connect()
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def artifact(db: sqlite3.Connection, aid: str, kind: str, locator: str,
             fingerprint: str, size: int = 0, meta: dict | None = None) -> None:
    db.execute("""INSERT INTO artifacts VALUES(?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET kind=excluded.kind,locator=excluded.locator,
        fingerprint=excluded.fingerprint,size_bytes=excluded.size_bytes,
        meta=excluded.meta,seen_at=excluded.seen_at""",
        (aid, kind, locator, fingerprint, size, dumps(meta or {}), now()))


def edge(db: sqlite3.Connection, src: str, dst: str, relation: str,
         evidence: dict | None = None) -> None:
    db.execute("""INSERT INTO edges VALUES(?,?,?,?,?) ON CONFLICT(src,dst,relation)
        DO UPDATE SET evidence=excluded.evidence,seen_at=excluded.seen_at""",
        (src, dst, relation, dumps(evidence or {}), now()))


def add_activity(db: sqlite3.Connection, day: str, aid: str, kind: str,
                 count: int = 0, seconds: int = 0) -> None:
    db.execute("""INSERT INTO activity VALUES(?,?,?,?,?)
      ON CONFLICT(day,artifact_id,kind) DO UPDATE SET
      count=count+excluded.count,seconds=seconds+excluded.seconds""",
      (day, aid, kind, count, seconds))


def prune(db: sqlite3.Connection) -> None:
    db.execute("DELETE FROM activity WHERE day < date('now','-365 days')")
    db.execute("DELETE FROM coverage WHERE day < date('now','-365 days')")
    db.execute("DELETE FROM previews WHERE expires_at < ?", (now(),))
    db.execute("DELETE FROM edges WHERE seen_at < ?", (now()-120*86400,))
    db.execute("DELETE FROM measurements WHERE day < date('now','-365 days')")


def row_json(row: sqlite3.Row) -> dict:
    value = dict(row)
    for name in ("meta", "evidence", "action", "plan", "stats", "detail"):
        if name in value:
            value[name] = json.loads(value[name])
    return value
