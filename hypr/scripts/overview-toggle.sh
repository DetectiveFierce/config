#!/usr/bin/env bash
set -euo pipefail

if hyprctl dispatch hyprexpo:expo toggle >/dev/null 2>&1; then
  exit 0
fi

hyprctl notify -1 2500 "rgb(ffc857)" "hyprexpo plugin is not loaded. Install/copy ~/.local/lib/hyprexpo.so and reload." >/dev/null 2>&1 || true
exit 0
