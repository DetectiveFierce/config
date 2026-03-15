#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


GTK_THEME_FILES = {
    "3.0": ("gtk-3.0/gtk.css", "gtk-3.0/gtk-dark.css"),
    "4.0": ("gtk-4.0/gtk.css", "gtk-4.0/gtk-dark.css"),
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate generated GTK CSS with the real GTK parser."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["Hate of Nature GTK Theme"],
        help="Theme directories or raw CSS files to validate.",
    )
    return parser.parse_args()


def expand_targets(raw_paths):
    targets = {"3.0": [], "4.0": []}
    for raw in raw_paths:
        path = Path(raw).resolve()
        if not path.exists():
            raise SystemExit(f"error: path not found: {raw}")
        if path.is_dir():
            for version, rel_paths in GTK_THEME_FILES.items():
                for rel_path in rel_paths:
                    candidate = path / rel_path
                    if candidate.is_file():
                        targets[version].append(candidate)
            continue

        if path.suffix.lower() not in {".css", ".scss"}:
            raise SystemExit(f"error: unsupported CSS input: {path}")

        # Raw CSS inputs are validated against both GTK3 and GTK4.
        targets["3.0"].append(path)
        targets["4.0"].append(path)

    return {
        version: dedupe(paths)
        for version, paths in targets.items()
        if paths
    }


def dedupe(paths):
    seen = set()
    result = []
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        result.append(path)
    return result


def forbidden_tokens(paths):
    issues = []
    for path in paths:
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "!important" in line:
                issues.append(f"{path}:{line_no}: forbidden token !important")
    return issues


def run_gtk_parser(version, paths):
    child = """
import sys
import gi
version = sys.argv[1]
paths = sys.argv[2:]
gi.require_version("Gtk", version)
from gi.repository import Gtk

provider = Gtk.CssProvider()
for path in paths:
    provider.load_from_path(path)
"""
    env = os.environ.copy()
    env.pop("GTK_THEME", None)
    env["G_MESSAGES_DEBUG"] = ""
    completed = subprocess.run(
        [sys.executable, "-c", child, version, *[str(path) for path in paths]],
        capture_output=True,
        text=True,
        env=env,
    )

    stderr = completed.stderr.strip()
    stdout = completed.stdout.strip()
    messages = []
    if stdout:
        messages.append(stdout)
    if stderr:
        messages.append(stderr)

    if completed.returncode != 0 or messages:
        header = f"GTK {version} parser reported errors"
        detail = "\n".join(messages) if messages else "(no stderr captured)"
        return f"{header}\n{detail}"
    return None


def main():
    args = parse_args()
    targets = expand_targets(args.paths)
    if not targets:
        raise SystemExit("error: no CSS targets found")

    issues = []
    all_paths = [path for paths in targets.values() for path in paths]
    issues.extend(forbidden_tokens(all_paths))

    for version, paths in sorted(targets.items()):
        parser_issue = run_gtk_parser(version, paths)
        if parser_issue:
            issues.append(parser_issue)

    if issues:
        print("FAIL: GTK parser validation failed")
        for issue in issues:
            print(issue)
        raise SystemExit(1)

    print("PASS: GTK parser accepted all CSS targets without warnings")


if __name__ == "__main__":
    main()
