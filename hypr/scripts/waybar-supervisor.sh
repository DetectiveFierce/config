#!/usr/bin/env bash
set -u

# Hyprland sessions can miss /usr/sbin on PATH, where some packaged binaries live.
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"

lockfile="${XDG_RUNTIME_DIR:-/tmp}/waybar-supervisor.lock"
restart_delay_seconds=1
stop_requested=0
child_pid=""

exec 9>"$lockfile"
if ! flock -n 9; then
  exit 0
fi

# If Waybar was launched directly before this supervisor took over, replace it
# so we end up with a single supervised bar process.
pkill -x waybar 2>/dev/null || true

stop_supervisor() {
  stop_requested=1
  if [[ -n "$child_pid" ]] && kill -0 "$child_pid" 2>/dev/null; then
    kill "$child_pid" 2>/dev/null || true
  fi
}

trap stop_supervisor INT TERM HUP

while true; do
  # The session GTK theme currently emits GTK3 parser errors. Pin Waybar to a
  # stable theme and let its own CSS handle the actual bar styling.
  GTK_THEME=Adwaita:dark waybar &
  child_pid=$!

  if wait "$child_pid"; then
    exit_code=0
  else
    exit_code=$?
  fi
  child_pid=""

  if (( stop_requested )); then
    break
  fi

  printf 'waybar exited with status %s, restarting in %ss\n' "$exit_code" "$restart_delay_seconds" >&2
  sleep "$restart_delay_seconds"
done
