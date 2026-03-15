#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_THEME_ARG="${1:-}"
TMP_DIR="$(mktemp -d)"
TMP_THEME="$TMP_DIR/Hate-of-Nature"

cleanup() {
  rm -rf "$TMP_DIR"
}

trap cleanup EXIT

cd "$ROOT_DIR"

echo "==> Build generated theme"
./scripts/build-hate-of-nature-gtk-theme.sh "$SRC_THEME_ARG" "$TMP_THEME" >/dev/null

echo
echo "==> Validate override source with GTK parser"
./scripts/test-hate-of-nature-gtk-theme-parse.py ./scripts/hate-of-nature-gtk-overrides.css

echo
echo "==> Validate generated GTK CSS with GTK parser"
./scripts/test-hate-of-nature-gtk-theme-parse.py "$TMP_THEME"

echo
echo "==> Validate generated GTK symbol references"
./scripts/test-hate-of-nature-gtk-theme-symbols.py "$TMP_THEME"

echo
echo "==> Validate generated GTK asset references"
./scripts/test-hate-of-nature-gtk-theme-assets.py "$TMP_THEME"

echo
echo "==> Validate palette coverage"
perl ./scripts/test-hate-of-nature-gtk-theme-colors.pl --include-assets "$TMP_THEME"

echo
echo "==> Validate bright-background regressions"
perl ./scripts/test-hate-of-nature-gtk-theme-light-backgrounds.pl "$TMP_THEME"

echo
echo "==> Validate selector coverage"
perl ./scripts/test-hate-of-nature-gtk-theme-selector-coverage.pl "$TMP_THEME"

echo
echo "==> Validate theme metadata"
grep -Fx 'Name=Hate-of-Nature' "$TMP_THEME/index.theme" >/dev/null
grep -Fx 'GtkTheme=Hate-of-Nature' "$TMP_THEME/index.theme" >/dev/null
grep -Fx 'MetacityTheme=Hate-of-Nature' "$TMP_THEME/index.theme" >/dev/null
test -f "$TMP_THEME/gtk-3.0/gtk.css"
test -f "$TMP_THEME/gtk-4.0/gtk.css"

echo
echo "PASS: comprehensive Hate-of-Nature GTK theme suite passed"
