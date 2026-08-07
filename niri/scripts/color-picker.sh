#!/usr/bin/env bash
set -euo pipefail

PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"

notify() {
  if command -v notify-send >/dev/null 2>&1; then
    notify-send "$@"
  fi
}

for dep in grim slurp magick wl-copy; do
  if ! command -v "$dep" >/dev/null 2>&1; then
    notify "Color picker failed" "Missing dependency: $dep"
    exit 1
  fi
done

point="$(slurp -p -f '%x,%y 1x1' || true)"
if [[ -z "${point:-}" ]]; then
  exit 0
fi

color="$(
  grim -g "$point" - \
    | magick png:- -alpha off -depth 8 -format '%[hex:p{0,0}]' info:-
)"

hex="#${color:0:6}"
printf '%s' "$hex" | wl-copy
notify "Color copied" "$hex"
