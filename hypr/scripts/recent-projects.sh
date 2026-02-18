#!/usr/bin/env bash
set -euo pipefail

mode="${1:-editor}"

collect_projects() {
  if command -v zoxide >/dev/null 2>&1; then
    zoxide query -l 2>/dev/null || true
  fi

  local root
  for root in "$HOME/code" "$HOME/Code" "$HOME/projects" "$HOME/src"; do
    [ -d "$root" ] || continue
    find "$root" -mindepth 1 -maxdepth 4 -type d -name .git -printf '%h\n' 2>/dev/null || true
  done
}

choose_entry() {
  if command -v fzf >/dev/null 2>&1; then
    fzf --reverse --prompt "Project > "
  elif command -v fuzzel >/dev/null 2>&1; then
    fuzzel --dmenu --prompt "Project > "
  elif command -v wofi >/dev/null 2>&1; then
    wofi --dmenu -i -p "Project > "
  elif command -v rofi >/dev/null 2>&1; then
    rofi -dmenu -i -p "Project > "
  else
    hyprctl notify -1 3000 "rgb(ff5555)" "No picker found (install fzf, fuzzel, wofi, or rofi)." >/dev/null 2>&1 || true
    return 1
  fi
}

open_editor() {
  local dir="$1"
  if command -v cursor >/dev/null 2>&1; then
    exec cursor "$dir"
  elif command -v zeditor >/dev/null 2>&1; then
    exec zeditor "$dir"
  elif command -v kitty >/dev/null 2>&1; then
    exec kitty --directory "$dir" -e nvim .
  fi
  hyprctl notify -1 3000 "rgb(ff5555)" "No editor found (cursor, zeditor, or kitty+nvim)." >/dev/null 2>&1 || true
  exit 1
}

selection="$(
  collect_projects \
    | awk 'NF' \
    | awk '!seen[$0]++' \
    | choose_entry || true
)"
[ -z "${selection:-}" ] && exit 0
[ -d "$selection" ] || exit 0

case "$mode" in
  editor)
    open_editor "$selection"
    ;;
  fm|filemanager|thunar)
    exec thunar "$selection"
    ;;
  *)
    open_editor "$selection"
    ;;
esac
