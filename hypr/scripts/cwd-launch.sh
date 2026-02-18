#!/usr/bin/env bash
set -euo pipefail

target="${1:-terminal}"

resolve_cwd() {
  local pid cwd
  pid="$(hyprctl -j activewindow 2>/dev/null | jq -r '.pid // 0' 2>/dev/null || echo 0)"
  if [[ "$pid" =~ ^[0-9]+$ ]] && [ "$pid" -gt 1 ] && [ -e "/proc/$pid/cwd" ]; then
    cwd="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
    if [ -n "${cwd:-}" ] && [ -d "$cwd" ]; then
      printf '%s\n' "$cwd"
      return
    fi
  fi
  printf '%s\n' "$HOME"
}

cwd="$(resolve_cwd)"

launch_terminal() {
  if command -v kitty >/dev/null 2>&1; then
    exec kitty --directory "$cwd"
  elif command -v foot >/dev/null 2>&1; then
    exec foot -D "$cwd"
  elif command -v alacritty >/dev/null 2>&1; then
    exec alacritty --working-directory "$cwd"
  fi
  hyprctl notify -1 3000 "rgb(ff5555)" "No supported terminal found (kitty, foot, or alacritty)." >/dev/null 2>&1 || true
  exit 1
}

case "$target" in
  terminal)
    launch_terminal
    ;;
  cursor)
    if command -v cursor >/dev/null 2>&1; then
      exec cursor "$cwd"
    fi
    if command -v zeditor >/dev/null 2>&1; then
      exec zeditor "$cwd"
    fi
    launch_terminal
    ;;
  thunar|fm|filemanager)
    exec thunar "$cwd"
    ;;
  rstudio)
    exec rstudio "$cwd"
    ;;
  *)
    shift || true
    cd "$cwd"
    exec "$target" "$@"
    ;;
esac
