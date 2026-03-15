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

IGNORE_REFS = {"import", "define-color", "binding-set", "keyframes"}
IMPORT_PATTERN = re.compile(
    r'@import\s+(?:url\(\s*)?["\']([^"\']+)["\']\s*\)?\s*;'
)
DEFINE_PATTERN = re.compile(r"@define-color\s+([A-Za-z0-9_-]+)")
REFERENCE_PATTERN = re.compile(r"(?<![A-Za-z0-9_-])@([A-Za-z_][A-Za-z0-9_-]*)")
COMMENT_PATTERN = re.compile(r"/\*.*?\*/", re.S)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Check GTK symbolic color references inside generated CSS."
    )
    parser.add_argument(
        "theme_dir",
        nargs="?",
        default="Hate of Nature GTK Theme",
        help="Generated theme directory to inspect.",
    )
    return parser.parse_args()


def collect_definitions(content):
    return set(DEFINE_PATTERN.findall(content))


def collect_references(content):
    references = set()
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("@define-color") or stripped.startswith("@import"):
            continue
        references.update(REFERENCE_PATTERN.findall(line))
    return {ref for ref in references if ref not in IGNORE_REFS}


def strip_comments(content):
    return COMMENT_PATTERN.sub("", content)


def collect_imports(css_path, content):
    imports = []
    for match in IMPORT_PATTERN.finditer(content):
        target = match.group(1).strip()
        if not target or "://" in target or target.startswith("data:"):
            continue
        imports.append((css_path.parent / target).resolve())
    return imports


def load_css_closure(root_css):
    stack = [root_css.resolve()]
    loaded = []
    seen = set()
    missing_imports = []

    while stack:
        css_path = stack.pop()
        if css_path in seen:
            continue
        seen.add(css_path)
        if not css_path.is_file():
            missing_imports.append(css_path)
            continue
        content = strip_comments(css_path.read_text(encoding="utf-8"))
        loaded.append((css_path, content))
        stack.extend(collect_imports(css_path, content))

    return loaded, missing_imports


def main():
    args = parse_args()
    theme_dir = Path(args.theme_dir).resolve()
    if not theme_dir.is_dir():
        raise SystemExit(f"error: theme directory not found: {theme_dir}")

    issues = []
    files_checked = 0
    for rel_path in CSS_TARGETS:
        css_path = theme_dir / rel_path
        if not css_path.is_file():
            continue
        loaded_css, missing_imports = load_css_closure(css_path)
        files_checked += len(loaded_css)
        for missing_import in missing_imports:
            issues.append(f"{css_path}: missing imported CSS file {missing_import}")
        merged_content = "\n".join(content for _, content in loaded_css)
        definitions = collect_definitions(merged_content)
        references = collect_references(merged_content)
        if not definitions:
            issues.append(f"{css_path}: no @define-color declarations discovered")
            continue
        if not references:
            issues.append(f"{css_path}: no symbolic color references discovered")
            continue
        missing = sorted(ref for ref in references if ref not in definitions)
        for ref in missing:
            issues.append(f"{css_path}: missing @define-color for @{ref}")

    if issues:
        print("FAIL: unresolved GTK symbolic color references")
        for issue in issues:
            print(issue)
        raise SystemExit(1)

    print(f"PASS: all GTK symbolic color references resolved across {files_checked} files")


if __name__ == "__main__":
    main()
