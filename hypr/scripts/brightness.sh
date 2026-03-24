#!/usr/bin/env bash
set -euo pipefail

direction="${1:-}"
if [[ "$direction" != "up" && "$direction" != "down" ]]; then
  exit 2
fi

# Prefer native laptop backlight when available.
if command -v brightnessctl >/dev/null 2>&1 && [[ -d /sys/class/backlight ]] && compgen -G "/sys/class/backlight/*" >/dev/null; then
  if [[ "$direction" == "up" ]]; then
    exec brightnessctl set +10%
  else
    exec brightnessctl set 10%-
  fi
fi

# Fallback to external monitor brightness over DDC/CI.
if command -v ddcutil >/dev/null 2>&1; then
  if [[ "$direction" == "up" ]]; then
    exec ddcutil setvcp 10 + 15 --display "${DDCUTIL_DISPLAY:-1}"
  else
    exec ddcutil setvcp 10 - 15 --display "${DDCUTIL_DISPLAY:-1}"
  fi
fi

exit 1
