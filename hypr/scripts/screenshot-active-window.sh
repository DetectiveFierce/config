#!/usr/bin/env bash
set -euo pipefail

window_json="$(hyprctl -j activewindow 2>/dev/null || true)"

geom="$(
  printf '%s' "$window_json" | jq -r '
    if (.at | type) == "array" and (.size | type) == "array" then
      "\(.at[0]),\(.at[1]) \(.size[0])x\(.size[1])"
    elif (.at | type) == "object" and (.size | type) == "object" then
      "\(.at.x),\(.at.y) \(.size.x)x\(.size.y)"
    else
      empty
    end
  ' 2>/dev/null || true
)"

if [ -z "$geom" ]; then
  hyprctl notify -1 2500 "rgb(ff5555)" "Unable to read active window geometry." >/dev/null 2>&1 || true
  exit 1
fi

grim -g "$geom" - | wl-copy
