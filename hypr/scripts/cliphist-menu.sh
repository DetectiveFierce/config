#!/usr/bin/env bash
set -euo pipefail

if ! command -v cliphist >/dev/null 2>&1 || ! command -v wl-copy >/dev/null 2>&1; then
  hyprctl notify -1 3000 "rgb(ff5555)" "Clipboard tools missing: install cliphist and wl-clipboard." >/dev/null 2>&1 || true
  exit 1
fi

choose_entry() {
  if command -v fuzzel >/dev/null 2>&1; then
    fuzzel --dmenu --prompt "Clipboard > "
  elif command -v wofi >/dev/null 2>&1; then
    wofi --dmenu -i -p "Clipboard > "
  elif command -v rofi >/dev/null 2>&1; then
    rofi -dmenu -i -p "Clipboard > "
  else
    hyprctl notify -1 3000 "rgb(ff5555)" "No launcher found (install fuzzel, wofi, or rofi)." >/dev/null 2>&1 || true
    return 1
  fi
}

selection="$(cliphist list | choose_entry || true)"
[ -z "${selection:-}" ] && exit 0

printf '%s' "$selection" | cliphist decode | wl-copy
