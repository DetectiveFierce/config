import datetime as dt
import json
import os
import sqlite3
import subprocess
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

from storage_advisor import actions, common, recommend
from storage_advisor.activityd import ActivityDaemon
from storage_advisor.db import SCHEMA, artifact


class AdvisorSafetyTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def test_coverage_requires_sixty_calendar_days_and_both_collectors(self):
        today = dt.date.today()
        for offset in range(60):
            day = (today - dt.timedelta(days=offset)).isoformat()
            for source in ("exec", "niri"):
                self.db.executemany("INSERT INTO coverage VALUES(?,?,?)",
                                    [(day, source, minute) for minute in range(1296)])
        self.assertGreaterEqual(recommend.covered_days(self.db), 54)
        self.db.execute("DELETE FROM coverage WHERE source='niri' AND day=?",
                        ((today - dt.timedelta(days=59)).isoformat(),))
        self.assertEqual(recommend.covered_days(self.db), 0)

    def test_overlap_needs_behavior_and_capability_evidence(self):
        today = dt.date.today()
        for offset in range(60):
            day = (today - dt.timedelta(days=offset)).isoformat()
            for minute in range(1296):
                self.db.execute("INSERT INTO coverage VALUES(?,?,?)", (day, "exec", minute))
                self.db.execute("INSERT INTO coverage VALUES(?,?,?)", (day, "niri", minute))
        artifact(self.db, "app:old.desktop", "app", "old.desktop", "old", 0,
                 {"name": "Old PDF viewer", "comment": "View PDFs", "categories": "Office;",
                  "mimes": ["application/pdf"], "default": False, "exec": "/usr/bin/old"})
        artifact(self.db, "app:new.desktop", "app", "new.desktop", "new", 0,
                 {"name": "New PDF viewer", "comment": "View PDFs", "categories": "Office;",
                  "mimes": ["application/pdf"], "default": False, "exec": "/usr/bin/new"})
        self.db.execute("INSERT INTO activity VALUES(?,?,?,?,?)",
                        (today.isoformat(), "session:new", "focus", 6, 1000))
        with patch.object(recommend, "app_embeddings",
                          lambda descriptions: {key: [1.0, 0.0] for key in descriptions}):
            self.assertEqual(recommend.app_substitutes(self.db), 1)
        suggestion = self.db.execute("SELECT * FROM suggestions WHERE kind='app_overlap'").fetchone()
        self.assertIn("90%", suggestion["claim"])
        self.assertEqual(json.loads(suggestion["evidence"])["shared_mimes"], ["application/pdf"])

    def test_rejected_candidate_stays_suppressed_until_evidence_changes(self):
        args = dict(kind="test", group="files", target="file:test", title="Test",
                    claim="claim", evidence={}, action={}, bytes_saved=1,
                    risk="low", confidence="high", fingerprint="first")
        recommend._emit(self.db, **args)
        sid = common.stable_id("test", "file:test")
        actions.reject(self.db, sid)
        recommend._emit(self.db, **args)
        self.assertEqual(self.db.execute("SELECT status FROM suggestions").fetchone()[0], "rejected")
        recommend._emit(self.db, **{**args, "fingerprint": "second"})
        self.assertEqual(self.db.execute("SELECT status FROM suggestions").fetchone()[0], "new")

    def test_changed_duplicate_refuses_execution(self):
        remove = self.root / "remove.pdf"
        keep = self.root / "keep.pdf"
        remove.write_bytes(b"same")
        keep.write_bytes(b"same")
        from storage_advisor.similarity import exact_digest
        digest = exact_digest(remove)
        with patch.object(common, "HOME", self.root), patch.object(actions, "HOME", self.root), \
             patch.object(actions, "settings", lambda: {"execution_enabled": True}):
            recommend._emit(self.db, kind="exact_duplicate", group="files",
                            target=f"file:{remove}", title="Duplicate", claim="claim",
                            evidence={}, action={"type": "trash_file", "path": str(remove),
                                                 "keep": str(keep), "digest": digest},
                            bytes_saved=0, risk="medium", confidence="high", fingerprint="f")
            sid = common.stable_id("exact_duplicate", f"file:{remove}")
            token = actions.preview(self.db, sid)["token"]
            remove.write_bytes(b"changed")
            with self.assertRaises(actions.ActionError):
                actions.execute(self.db, sid, token)
            self.assertTrue(remove.exists())

    def test_hardlink_refuses_duplicate_preview(self):
        remove = self.root / "remove.pdf"
        keep = self.root / "keep.pdf"
        remove.write_bytes(b"same")
        os.link(remove, keep)
        with patch.object(common, "HOME", self.root), patch.object(actions, "HOME", self.root):
            with self.assertRaisesRegex(actions.ActionError, "Unsafe duplicate"):
                actions._current_plan({"action": {"type": "trash_file",
                                                   "path": str(remove), "keep": str(keep)}})

    def test_package_recovery_excludes_live_hardlink(self):
        shared = self.root / "shared"
        other = self.root / "other"
        unique = self.root / "unique"
        shared.write_bytes(b"x" * 4096)
        os.link(shared, other)
        unique.write_bytes(b"x" * 4096)
        def fake_run(argv, timeout=30):
            self.assertEqual(argv[:2], ["pacman", "-Qlq"])
            return os_result(argv, 0, f"{shared}\n{unique}\n")
        with patch.object(actions, "run", fake_run):
            self.assertEqual(actions.package_reclaimable_bytes(["example"]),
                             unique.stat().st_blocks * 512)

    def test_generated_directory_nested_change_refuses_execution(self):
        project = self.root / "project"
        build = project / "build"
        build.mkdir(parents=True)
        (project / ".gitignore").write_text("build/\n")
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        child = build / "result.bin"
        child.write_bytes(b"first")
        with patch.object(actions, "HOME", self.root), \
             patch.object(actions, "settings", lambda: {"execution_enabled": True}):
            recommend._emit(self.db, kind="project_generated", group="storage",
                            target=f"dir:{build}", title="Build", claim="claim",
                            evidence={}, action={"type": "trash_directory", "path": str(build),
                                                 "project": str(project)}, bytes_saved=0,
                            risk="medium", confidence="high", fingerprint="f")
            sid = common.stable_id("project_generated", f"dir:{build}")
            token = actions.preview(self.db, sid)["token"]
            child.write_bytes(b"modified")
            with self.assertRaisesRegex(actions.ActionError, "changed"):
                actions.execute(self.db, sid, token)
            self.assertTrue(child.exists())

    def test_steam_manifest_change_refuses_handoff(self):
        steam_root = self.root / ".local/share/Steam/steamapps"
        game = steam_root / "common" / "Example"
        game.mkdir(parents=True)
        (game / "game.bin").write_bytes(b"data")
        manifest = steam_root / "appmanifest_123.acf"
        manifest.write_text('"appid" "123"\n')
        original_run = actions.run
        def fake_run(argv, timeout=30):
            if argv[0] == "du":
                return os_result(argv, 0, f"4096\t{game}\n")
            return original_run(argv, timeout)
        with patch.object(actions, "HOME", self.root), \
             patch.object(actions, "settings", lambda: {"execution_enabled": True}), \
             patch.object(actions, "run", fake_run):
            recommend._emit(self.db, kind="steam_game", group="software",
                            target="steam:123", title="Game", claim="claim", evidence={},
                            action={"type": "steam_uninstall", "appid": "123",
                                    "install_dir": str(game)}, bytes_saved=4096,
                            risk="medium", confidence="medium", fingerprint="f")
            sid = common.stable_id("steam_game", "steam:123")
            token = actions.preview(self.db, sid)["token"]
            manifest.write_text('"appid" "123"\n"changed" "yes"\n')
            with self.assertRaisesRegex(actions.ActionError, "changed"):
                actions.execute(self.db, sid, token)
            self.assertTrue(game.exists())

    def test_container_reference_blocks_image_removal(self):
        iid = "sha256:" + "a" * 64
        suggestion = {"action": {"type": "docker_image_remove", "image_id": iid}}
        def fake_run(argv, timeout=30):
            if argv[:3] == ["docker", "image", "inspect"]:
                return os_result(argv, 0, json.dumps([{"RepoTags": []}]))
            if argv[:3] == ["docker", "container", "ls"]:
                return os_result(argv, 0, "container-id\n")
            if argv[:3] == ["docker", "container", "inspect"]:
                return os_result(argv, 0, json.dumps([{"Image": iid}]))
            raise AssertionError(argv)
        with patch.object(actions, "run", fake_run):
            with self.assertRaisesRegex(actions.ActionError, "container references"):
                actions._current_plan(suggestion)

    def test_background_exec_does_not_become_personal_use(self):
        daemon = ActivityDaemon.__new__(ActivityDaemon)
        daemon.db = self.db
        daemon.pending = defaultdict(lambda: [0, 0])
        daemon.process_parent = {}
        daemon.process_exe = {}
        daemon.focused_pid = 100
        daemon.handle_root(json.dumps({"kind": "exec", "pid": 200, "ppid": 1,
                                       "exe": "/usr/bin/indexer"}).encode())
        daemon.handle_root(json.dumps({"kind": "exec", "pid": 201, "ppid": 100,
                                       "exe": "/usr/bin/viewer"}).encode())
        kinds = {(aid, kind): counts[0] for (_, aid, kind), counts in daemon.pending.items()}
        self.assertEqual(kinds[("exe:/usr/bin/indexer", "exec_background")], 1)
        self.assertEqual(kinds[("exe:/usr/bin/viewer", "exec_foreground")], 1)


def os_result(args, code, stdout):
    from subprocess import CompletedProcess
    return CompletedProcess(args, code, stdout, "")


if __name__ == "__main__":
    unittest.main()
