#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NIRI_DIR="$ROOT_DIR/niri"

echo "==> niri syntax"
niri validate -c "$NIRI_DIR/config.kdl"

echo "==> generated integration policy"
if rg -n 'include .*basicsettings\.kdl|include .*keybinds\.kdl' "$NIRI_DIR" --glob '*.kdl'; then
  echo "error: tracked niri config includes local niri-settings output." >&2
  exit 1
fi

dms_fragments=(alttab.kdl binds.kdl colors.kdl cursor.kdl layout.kdl outputs.kdl windowrules.kdl wpblur.kdl)
for fragment in "${dms_fragments[@]}"; do
  if [[ ! -f "$NIRI_DIR/dms/$fragment" ]]; then
    echo "error: missing tracked DMS fragment: dms/$fragment" >&2
    exit 1
  fi
  if ! rg -Fq "include \"dms/$fragment\"" "$NIRI_DIR/config.kdl"; then
    echo "error: DMS fragment is not included: dms/$fragment" >&2
    exit 1
  fi
done

echo "==> portable paths"
if rg -n '/home/[^/]+|\.config/hypr/scripts' "$NIRI_DIR" "$ROOT_DIR/bin"; then
  echo "error: niri or shared helpers contain a host-specific path." >&2
  exit 1
fi
if rg -n 'spawn "wm-[^"]+"' "$NIRI_DIR" --glob '*.kdl'; then
  echo "error: niri starts a shared helper through its boot-time PATH." >&2
  echo '       use spawn-sh with $HOME/.local/bin/<helper> instead.' >&2
  exit 1
fi

echo "==> effective binding uniqueness"
bind_files=("$NIRI_DIR"/binds/*.kdl)
bind_files+=("$NIRI_DIR/dms/binds.kdl")
if [[ -r "$NIRI_DIR/machine.kdl" ]]; then
  machine_rel="$(sed -nE 's/^[[:space:]]*include[[:space:]]+"([^"]+)".*/\1/p' "$NIRI_DIR/machine.kdl" | head -n 1)"
  if [[ -n "$machine_rel" && -r "$NIRI_DIR/$machine_rel" ]]; then
    bind_files+=("$NIRI_DIR/$machine_rel")
  fi
fi

duplicates="$({
  awk '
    /^[[:space:]]*\/\// { next }
    /^[[:space:]]*[^[:space:]{}]+([[:space:]]+[^{}]*)?[[:space:]]*\{/ {
      line=$0
      sub(/^[[:space:]]*/, "", line)
      split(line, fields, /[[:space:]]+/)
      key=fields[1]
      if (key ~ /\+/ || key ~ /^XF86/ || key ~ /^F[0-9]+$/ || key == "Print") print key
    }
  ' "${bind_files[@]}"
} | sort | uniq -d)"
if [[ -n "$duplicates" ]]; then
  printf 'error: duplicate effective bindings:\n%s\n' "$duplicates" >&2
  exit 1
fi

echo "==> shared helper syntax"
while IFS= read -r -d '' script; do
  bash -n "$script"
done < <(find "$ROOT_DIR/bin" -maxdepth 1 -type f -print0 | sort -z)

active_config="${XDG_CONFIG_HOME:-$HOME/.config}/niri/config.kdl"
if [[ -e "$active_config" ]] &&
  [[ "$(readlink -f "$active_config")" == "$(readlink -f "$NIRI_DIR/config.kdl")" ]]; then
  echo "==> live helper deployment"
  helper_deployment_failed=0
  while IFS= read -r -d '' source_helper; do
    helper_name="${source_helper##*/}"
    deployed_helper="$(command -v "$helper_name" 2>/dev/null || true)"

    if [[ -z "$deployed_helper" ]]; then
      echo "error: active niri config cannot find helper: $helper_name" >&2
      helper_deployment_failed=1
      continue
    fi

    if [[ "$(readlink -f "$deployed_helper")" != "$(readlink -f "$source_helper")" ]]; then
      echo "error: active helper is not repository-backed: $deployed_helper" >&2
      helper_deployment_failed=1
    fi
  done < <(find "$ROOT_DIR/bin" -maxdepth 1 -type f -name 'wm-*' -print0 | sort -z)

  if [[ "$helper_deployment_failed" -ne 0 ]]; then
    echo "error: run ./dotfiles apply to reconcile the live helper links." >&2
    exit 1
  fi
fi

echo "Niri checks passed."
