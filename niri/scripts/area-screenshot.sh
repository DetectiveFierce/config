#!/usr/bin/env bash
set -euo pipefail

PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"

notify() {
  if command -v notify-send >/dev/null 2>&1; then
    notify-send "$@"
  fi
}

for dep in grim slurp wl-copy; do
  if ! command -v "$dep" >/dev/null 2>&1; then
    notify "Screenshot failed" "Missing dependency: $dep"
    exit 1
  fi
done

geometry="$(slurp -d || true)"
if [[ -z "${geometry:-}" ]]; then
  exit 0
fi

grim -g "$geometry" - | wl-copy --type image/png
notify "Screenshot copied" "$geometry"
