#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/fonts"

mkdir -p "$TARGET_DIR"

mapfile -d '' FONT_FILES < <(
  find "$SCRIPT_DIR" -maxdepth 1 -type f \
    \( -iname '*.ttf' -o -iname '*.otf' -o -iname '*.ttc' -o -iname '*.otc' \) \
    -print0 | sort -z
)

if [ "${#FONT_FILES[@]}" -eq 0 ]; then
  echo "No font files found in $SCRIPT_DIR"
  exit 1
fi

for font in "${FONT_FILES[@]}"; do
  install -m 0644 "$font" "$TARGET_DIR/"
done

echo "Installed ${#FONT_FILES[@]} font file(s) to $TARGET_DIR"

if command -v fc-cache >/dev/null 2>&1; then
  fc-cache -f "$TARGET_DIR"
  echo "Font cache refreshed."
else
  echo "fc-cache not found; skip cache refresh."
fi
