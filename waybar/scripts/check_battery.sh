#!/usr/bin/env bash
set -euo pipefail

CRIT=${1:-15}
FILE="${HOME}/.config/waybar/scripts/notified"

find_battery() {
  local battery
  for battery in /sys/class/power_supply/BAT*; do
    if [[ -d "$battery" ]]; then
      printf '%s\n' "$battery"
      return 0
    fi
  done
  return 1
}

if ! bat="$(find_battery)"; then
  rm -f "$FILE"
  exit 0
fi

stat="$(<"$bat/status")"
perc="$(<"$bat/capacity")"

if [[ "$perc" -le "$CRIT" && "$stat" == "Discharging" ]]; then
  if [[ ! -f "$FILE" ]]; then
    notify-send --urgency=critical --icon=dialog-warning "Battery Low" "Current charge: $perc%"
    touch "$FILE"
  fi
elif [[ -f "$FILE" ]]; then
  rm -f "$FILE"
fi
