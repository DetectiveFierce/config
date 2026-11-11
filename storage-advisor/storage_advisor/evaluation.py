"""Temporal holdout audit; reports evidence only after adequate live history."""
from __future__ import annotations

import datetime as dt
import sqlite3


def backtest(db: sqlite3.Connection) -> dict:
    today = dt.date.today()
    start = today - dt.timedelta(days=119)
    middle = today - dt.timedelta(days=59)
    end = today + dt.timedelta(days=1)
    joint = db.execute("""SELECT COUNT(*) n FROM coverage e JOIN coverage n
      ON n.day=e.day AND n.minute=e.minute AND n.source='niri'
      WHERE e.source='exec' AND e.day>=? AND e.day<?""",
      (start.isoformat(), end.isoformat())).fetchone()["n"]
    if joint < 120 * 1440 * 0.9:
        return {"ready": False, "reason": "Need 120 days with at least 90% joint process/Niri coverage",
                "joint_covered_minutes": joint}
    rows = db.execute("""SELECT a.id artifact_id,
      COALESCE(SUM(CASE WHEN act.day<? THEN act.count ELSE 0 END),0) training,
      COALESCE(SUM(CASE WHEN act.day>=? THEN act.count ELSE 0 END),0) holdout
      FROM artifacts a LEFT JOIN activity act ON act.artifact_id=a.id
      AND act.day>=? AND act.day<?
      AND act.kind IN ('focus','exec_foreground','open_foreground')
      WHERE a.kind IN ('file','session_app') GROUP BY a.id""",
      (middle.isoformat(), middle.isoformat(), start.isoformat(), end.isoformat())).fetchall()
    predicted_unused = [row for row in rows if row["training"] == 0]
    false_unused = sum(row["holdout"] > 0 for row in predicted_unused)
    return {"ready": True, "items_evaluated": len(rows),
            "predicted_unused": len(predicted_unused),
            "later_used_after_no_training_activity": false_unused,
            "false_unused_rate": round(false_unused / len(predicted_unused), 3) if predicted_unused else None,
            "note": "Descriptive holdout; sparse observations may make this unstable."}
