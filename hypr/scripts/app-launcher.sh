#!/usr/bin/env bash
set -euo pipefail

if command -v fuzzel >/dev/null 2>&1; then
  exec fuzzel
elif command -v wofi >/dev/null 2>&1; then
  exec wofi --show drun -i
elif command -v rofi >/dev/null 2>&1; then
  exec rofi -show drun -i
elif command -v walker >/dev/null 2>&1; then
  exec walker
fi

hyprctl notify -1 3000 "rgb(ff5555)" "No app launcher found (install fuzzel, wofi, rofi, or walker)." >/dev/null 2>&1 || true
exit 1
