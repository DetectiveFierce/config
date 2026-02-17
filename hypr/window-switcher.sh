#!/usr/bin/env bash
set -euo pipefail

if ! command -v hyprctl >/dev/null 2>&1; then
  exit 1
fi

if ! command -v fuzzel >/dev/null 2>&1; then
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  exit 1
fi

menu_input="$(hyprctl -j clients | jq -r '
  map(select(.mapped == true and .hidden == false))
  | sort_by(.focusHistoryID)
  | .[]
  | [
      .address,
      ("[" + (.workspace.name // "?") + "] " + (.class // "app") + " - " + ((.title // "") | gsub("[\r\n\t]"; " ")))
    ]
  | @tsv
')"

[ -z "$menu_input" ] && exit 0

selection="$(printf '%s\n' "$menu_input" | fuzzel --dmenu --prompt "Switch window > " --with-nth=2)"
[ -z "$selection" ] && exit 0

address="${selection%%$'\t'*}"
[ -z "$address" ] && exit 0

hyprctl dispatch focuswindow "address:${address}" >/dev/null
