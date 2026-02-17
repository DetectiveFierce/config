#!/usr/bin/env bash
set -euo pipefail

# Prefer vendored hypr-alttab for consistent behavior across machines.
# Try repo path first (works even before re-stowing), then ~/.config.
for vendored_alttab in "$HOME/config/hypr/bin/hypr-alttab" "$HOME/.config/hypr/bin/hypr-alttab"; do
  if [ -x "$vendored_alttab" ]; then
    "$vendored_alttab" --switch && exit 0
  fi
done

# Fall back to system hypr-alttab if installed.
if command -v hypr-alttab >/dev/null 2>&1; then
  hypr-alttab --switch && exit 0
fi

# Last resort: simple text-based window switcher via fuzzel.
for cmd in hyprctl fuzzel jq; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    exit 1
  fi
done

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
