#!/usr/bin/env python3

import argparse
import re
from pathlib import Path


CSS_TARGETS = (
    "gtk-3.0/gtk.css",
    "gtk-3.0/gtk-dark.css",
    "gtk-4.0/gtk.css",
    "gtk-4.0/gtk-dark.css",
)
URL_PATTERN = re.compile(r"url\(([^)]+)\)")
IMPORT_PATTERN = re.compile(
    r'@import\s+(?:url\(\s*)?["\']([^"\']+)["\']\s*\)?\s*;'
)
COMMENT_PATTERN = re.compile(r"/\*.*?\*/", re.S)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate that every local asset referenced from GTK CSS exists."
    )
    parser.add_argument(
        "theme_dir",
        nargs="?",
        default="Hate of Nature GTK Theme",
        help="Generated theme directory to inspect.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    theme_dir = Path(args.theme_dir).resolve()
    if not theme_dir.is_dir():
        raise SystemExit(f"error: theme directory not found: {theme_dir}")

    issues = []
    seen_urls = 0
    seen_imports = 0
    for rel_path in CSS_TARGETS:
        css_path = theme_dir / rel_path
        if not css_path.is_file():
            continue
        content = COMMENT_PATTERN.sub("", css_path.read_text(encoding="utf-8"))
        for line_no, line in enumerate(content.splitlines(), 1):
            for raw_url in URL_PATTERN.findall(line):
                seen_urls += 1
                asset = raw_url.strip().strip("\"'")
                if not asset or asset.startswith("data:") or "://" in asset:
                    continue
                resolved = (css_path.parent / asset).resolve()
                if not resolved.exists():
                    issues.append(
                        f"{css_path}:{line_no}: missing asset referenced by url({asset})"
                    )
            for raw_import in IMPORT_PATTERN.findall(line):
                seen_imports += 1
                import_target = raw_import.strip()
                if not import_target or import_target.startswith("data:") or "://" in import_target:
                    continue
                resolved = (css_path.parent / import_target).resolve()
                if not resolved.exists():
                    issues.append(
                        f"{css_path}:{line_no}: missing CSS file referenced by @import {import_target}"
                    )

    if seen_urls == 0:
        issues.append("no url() references discovered in generated GTK CSS")

    if issues:
        print("FAIL: missing GTK theme assets")
        for issue in issues:
            print(issue)
        raise SystemExit(1)

    print(
        "PASS: all local GTK asset references resolved "
        f"({seen_urls} url() entries, {seen_imports} @import entries)"
    )


if __name__ == "__main__":
    main()
