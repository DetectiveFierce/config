#!/usr/bin/env bash
set -euo pipefail

action="${1:-}"
step="${BRIGHTNESS_STEP:-10}"

case "$action" in
  up|down|sync)
    ;;
  *)
    exit 2
    ;;
esac

have_dms_ipc() {
  command -v dms >/dev/null 2>&1 && dms ipc brightness status >/dev/null 2>&1
}

list_hdmi_displays() {
  ddcutil detect 2>/dev/null | awk '
    /^Display [0-9]+$/ { display=$2; bus=""; connector="" }
    /I2C bus:/ {
      bus=$3
      sub(".*/i2c-", "", bus)
    }
    /DRM_connector:/ {
      connector=$2
      sub(/^card[0-9]+-/, "", connector)
      if (connector ~ /^HDMI-A-/ && bus != "") {
        printf "%s %s %s\n", display, bus, connector
      }
    }
  ' | sort -k3,3V
}

get_percent_for_bus() {
  local bus="${1:?missing bus}"

  ddcutil getvcp 10 --bus "$bus" 2>/dev/null \
    | sed -nE 's/.*current value = *([0-9]+), max value = *([0-9]+).*/\1 \2/p' \
    | awk '{ if ($2 > 0) printf "%d\n", ($1 * 100) / $2 }'
}

clamp_percent() {
  local value="${1:-0}"

  if (( value < 0 )); then
    printf '0\n'
  elif (( value > 100 )); then
    printf '100\n'
  else
    printf '%s\n' "$value"
  fi
}

notify_brightness() {
  local percent="${1:-}"
  local notify_id_file notify_id new_id
  local replace_args=()

  [[ "$percent" =~ ^[0-9]+$ ]] || return 0
  command -v notify-send >/dev/null 2>&1 || return 0

  notify_id_file="${XDG_RUNTIME_DIR:-/tmp}/brightness-osd.id"
  if [[ -f "$notify_id_file" ]]; then
    notify_id="$(<"$notify_id_file")"
    if [[ "$notify_id" =~ ^[0-9]+$ ]]; then
      replace_args=(--replace-id="$notify_id")
    fi
  fi

  if new_id="$(
    notify-send \
      --print-id \
      --app-name="brightness-osd" \
      --transient \
      --expire-time=1200 \
      --hint="int:value:${percent}" \
      "Brightness" \
      "${percent}%" \
      "${replace_args[@]}"
  )"; then
    printf '%s\n' "$new_id" >"$notify_id_file"
  fi
}

mapfile -t hdmi_displays < <(list_hdmi_displays)

if [[ "${#hdmi_displays[@]}" -eq 0 ]]; then
  exit 1
fi

target=-1
for entry in "${hdmi_displays[@]}"; do
  read -r _display bus _connector <<<"$entry"
  current="$(get_percent_for_bus "$bus")"
  [[ -n "$current" ]] || continue
  if (( current > target )); then
    target="$current"
  fi
done

if (( target < 0 )); then
  exit 1
fi

case "$action" in
  up)
    target="$(clamp_percent "$(( target + step ))")"
    ;;
  down)
    target="$(clamp_percent "$(( target - step ))")"
    ;;
  sync)
    target="$(clamp_percent "$target")"
    ;;
esac

used_dms=0
for index in "${!hdmi_displays[@]}"; do
  read -r display bus _connector <<<"${hdmi_displays[$index]}"
  device="ddc:i2c-$bus"

  if (( index == 0 )) && have_dms_ipc; then
    dms ipc brightness set "$target" "$device" >/dev/null
    used_dms=1
    continue
  fi

  ddcutil setvcp 10 "$target" --display "$display" >/dev/null
done

if (( used_dms == 0 )); then
  notify_brightness "$target"
fi
