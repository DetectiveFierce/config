#!/usr/bin/python3
"""Root-owned final check for the two actions that require elevation."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


def run(*args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True,
                                     ensure_ascii=False).encode()).hexdigest()


def fail(reason: str) -> int:
    print(reason, file=sys.stderr)
    return 2


def main() -> int:
    if len(sys.argv) != 4:
        return fail("Expected action, target, and preview digest")
    action, target, expected = sys.argv[1:]
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        return fail("Invalid preview digest")
    if action == "pacman_remove":
        if not re.fullmatch(r"[A-Za-z0-9@+._-]+", target):
            return fail("Invalid package")
        preview = run("pacman", "-Rs", "--print-format", "%n", target)
        if preview.returncode:
            return fail("Pacman removal preview failed")
        targets = [line for line in preview.stdout.splitlines() if line]
        versions = {}
        for package in targets:
            version = run("pacman", "-Q", package)
            if version.returncode:
                return fail("Package changed")
            versions[package] = version.stdout.strip()
        if digest({"targets": targets, "versions": versions}) != expected:
            return fail("Package transaction changed after authentication")
        result = run("pacman", "-Rns", "--noconfirm", "--", target, timeout=240)
    elif action == "paccache":
        if target != "3":
            return fail("Only keep-three cache cleanup is supported")
        preview = run("paccache", "-d", "-k", target, "-v")
        if preview.returncode:
            return fail("Paccache preview failed")
        root = Path("/var/cache/pacman/pkg")
        paths = sorted(root / line for line in preview.stdout.splitlines()
                       if line and not line.startswith("==>") and (root / line).parent == root)
        files = [(str(path), path.stat().st_size) for path in paths if path.is_file()]
        if digest(files) != expected:
            return fail("Cache candidates changed after authentication")
        result = run("paccache", "-r", "-k", target, timeout=240)
    else:
        return fail("Unsupported action")
    sys.stdout.write(result.stdout[-2000:])
    sys.stderr.write(result.stderr[-2000:])
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
