#!/usr/bin/env bash
set -euo pipefail

# Use the same icon theme as fuzzel for consistent app icons in Alt-Tab.
FUZZEL_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/fuzzel/fuzzel.ini"
ICON_THEME=""
if [ -r "$FUZZEL_CONFIG" ]; then
  ICON_THEME="$(
    awk -F= '
      /^[[:space:]]*\[main\][[:space:]]*$/ { in_main=1; next }
      /^[[:space:]]*\[/ { if (in_main) exit }
      in_main && /^[[:space:]]*icon-theme[[:space:]]*=/ {
        val=$2
        sub(/^[[:space:]]+/, "", val)
        sub(/[[:space:]]+$/, "", val)
        gsub(/"/, "", val)
        print val
        exit
      }
    ' "$FUZZEL_CONFIG"
  )"
fi

ORIG_XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
ORIG_XDG_DATA_DIRS="${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
ALIAS_DATA_HOME="${XDG_CACHE_HOME:-$HOME/.cache}/hypr-alttab-desktop-data"
ALIAS_APP_DIR="$ALIAS_DATA_HOME/applications"
ALIAS_STAMP="$ALIAS_DATA_HOME/.wmclass-aliases.stamp"
ALIAS_TTL_SECONDS=600

desktop_app_dirs() {
  local -a dirs=()
  local -a xdg_dirs=()
  local d

  dirs+=("${XDG_DATA_HOME:-$HOME/.local/share}/applications")

  IFS=: read -r -a xdg_dirs <<< "${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
  for d in "${xdg_dirs[@]}"; do
    [ -n "$d" ] && dirs+=("$d/applications")
  done

  dirs+=("$HOME/.local/share/flatpak/exports/share/applications")
  dirs+=("/var/lib/flatpak/exports/share/applications")

  printf '%s\n' "${dirs[@]}"
}

build_wmclass_aliases() {
  local now=0
  local last=0
  local app_dir desktop_file wmclass alias_file

  mkdir -p "$ALIAS_APP_DIR"

  now="$(date +%s)"
  if [ -e "$ALIAS_STAMP" ]; then
    last="$(stat -c %Y "$ALIAS_STAMP" 2>/dev/null || echo 0)"
  fi
  if (( now - last < ALIAS_TTL_SECONDS )); then
    return
  fi

  while IFS= read -r app_dir; do
    [ -d "$app_dir" ] || continue
    while IFS= read -r -d '' desktop_file; do
      wmclass="$(
        awk -F= '
          tolower($1) == "startupwmclass" {
            val=$2
            sub(/^[[:space:]]+/, "", val)
            sub(/[[:space:]]+$/, "", val)
            gsub(/"/, "", val)
            print val
            exit
          }
        ' "$desktop_file" 2>/dev/null
      )"

      [ -n "$wmclass" ] || continue
      alias_file="$ALIAS_APP_DIR/${wmclass}.desktop"
      if [ ! -e "$alias_file" ]; then
        ln -s "$desktop_file" "$alias_file" 2>/dev/null || cp -f "$desktop_file" "$alias_file" 2>/dev/null || true
      fi
    done < <(find -L "$app_dir" -maxdepth 1 -type f -name '*.desktop' -print0 2>/dev/null)
  done < <(desktop_app_dirs)

  touch "$ALIAS_STAMP"
}

build_wmclass_aliases

run_alttab() {
  local cmd="$1"
  local -a env_overrides=()

  env_overrides+=("XDG_DATA_HOME=$ALIAS_DATA_HOME")
  env_overrides+=("XDG_DATA_DIRS=$ORIG_XDG_DATA_HOME:$ORIG_XDG_DATA_DIRS")

  if [ -n "$ICON_THEME" ]; then
    env_overrides+=("GTK_ICON_THEME=$ICON_THEME")
    env "${env_overrides[@]}" "$cmd" --switch
  else
    env "${env_overrides[@]}" "$cmd" --switch
  fi
}

# Prefer vendored hypr-alttab for consistent behavior across machines.
for vendored_alttab in "$HOME/.config/hypr/bin/hypr-alttab"; do
  if [ -x "$vendored_alttab" ]; then
    run_alttab "$vendored_alttab" && exit 0
  fi
done

# Fall back to system hypr-alttab if installed.
if command -v hypr-alttab >/dev/null 2>&1; then
  run_alttab hypr-alttab && exit 0
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
