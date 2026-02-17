#!/usr/bin/env bash
set -euo pipefail

# CONFIG
WALL_DIR="$HOME/.config/hypr/wallpaper"
INTERVAL=600  # seconds

detect_backend() {
  if [ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ] || hyprctl monitors -j >/dev/null 2>&1; then
    echo "hyprland"
    return
  fi

  if [ -n "${NIRI_SOCKET:-}" ] || niri msg outputs -j >/dev/null 2>&1; then
    echo "niri"
    return
  fi

  echo "unknown"
}

if [ ! -d "$WALL_DIR" ]; then
  echo "Wallpaper directory not found: $WALL_DIR" >&2
  exit 1
fi

pick_random() {
  find -L "$WALL_DIR" -type f \( \
    -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' \
  \) | shuf -n 1
}

ensure_hyprpaper() {
  if ! pgrep -x hyprpaper >/dev/null 2>&1; then
    hyprpaper &
    sleep 2  # Give hyprpaper time to start
  fi
}

apply_wallpaper_hyprland() {
  local img="$1"
  readarray -t monitors < <(hyprctl monitors -j | jq -r '.[].name')

  if [ ${#monitors[@]} -eq 0 ]; then
    echo "No monitors detected by hyprctl." >&2
    return 1
  fi

  # Use the hyprctl hyprpaper interface.
  hyprctl hyprpaper preload "$img" >/dev/null 2>&1 || true

  local m
  for m in "${monitors[@]}"; do
    hyprctl hyprpaper wallpaper "${m},${img}" >/dev/null 2>&1 || true
  done
}

ensure_swww() {
  if ! pgrep -x swww-daemon >/dev/null 2>&1; then
    swww-daemon --format xrgb >/dev/null 2>&1 &
  fi

  # Wait briefly for swww-daemon to become ready.
  local i
  for i in {1..30}; do
    if swww query >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.2
  done

  echo "swww-daemon did not become ready." >&2
  return 1
}

apply_wallpaper_niri() {
  local img="$1"
  swww img --resize crop --transition-type simple --transition-step 120 "$img" >/dev/null 2>&1
}

apply_wallpaper() {
  local img="$1"
  local backend="$2"

  case "$backend" in
  hyprland)
    apply_wallpaper_hyprland "$img"
    ;;
  niri)
    apply_wallpaper_niri "$img"
    ;;
  *)
    echo "Unsupported backend: $backend" >&2
    return 1
    ;;
  esac
}

BACKEND="$(detect_backend)"
case "$BACKEND" in
hyprland)
  ensure_hyprpaper
  ;;
niri)
  ensure_swww
  ;;
*)
  echo "Could not detect a supported compositor (hyprland or niri)." >&2
  exit 1
  ;;
esac

# Initial set
if img=$(pick_random); then
  apply_wallpaper "$img" "$BACKEND"
else
  echo "No images found in $WALL_DIR" >&2
  exit 1
fi

# Loop
while true; do
  sleep "$INTERVAL"
  if img=$(pick_random); then
    apply_wallpaper "$img" "$BACKEND"
  fi
done
