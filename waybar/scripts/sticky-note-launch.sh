#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_SCRIPT="$SCRIPT_DIR/sticky_note.py"

if pgrep -f "python3 .*sticky_note.py" >/dev/null; then
    hyprctl dispatch focuswindow "title:Sticky Note" >/dev/null 2>&1 || true
    exit 0
fi

nohup python3 "$APP_SCRIPT" >/tmp/sticky-note.log 2>&1 &
