#!/usr/bin/env bash
set -euo pipefail

# Hyprland sessions can miss /usr/sbin on PATH, where some packaged binaries live.
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"

vicinae_cmd=""
if command -v vicinae >/dev/null 2>&1; then
  vicinae_cmd="$(command -v vicinae)"
elif command -v vicinae-bin >/dev/null 2>&1; then
  vicinae_cmd="$(command -v vicinae-bin)"
fi

if [[ -n "$vicinae_cmd" ]]; then
  if "$vicinae_cmd" toggle >/dev/null 2>&1; then
    exit 0
  fi

  exec "$vicinae_cmd" server --open
elif command -v fuzzel >/dev/null 2>&1; then
  exec fuzzel
elif command -v wofi >/dev/null 2>&1; then
  exec wofi --show drun -i
elif command -v rofi >/dev/null 2>&1; then
  exec rofi -show drun -i
elif command -v walker >/dev/null 2>&1; then
  exec walker
fi

hyprctl notify -1 3000 "rgb(ff5555)" "No app launcher found (install vicinae, fuzzel, wofi, rofi, or walker)." >/dev/null 2>&1 || true
exit 1
