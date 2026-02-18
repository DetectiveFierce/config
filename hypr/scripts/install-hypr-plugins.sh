#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  install-hypr-plugins.sh [plugin...]

Examples:
  install-hypr-plugins.sh
  install-hypr-plugins.sh hyprexpo hyprbars

Notes:
  - Defaults to "hyprexpo" when no plugin is specified.
  - Builds against the plugin commit pinned for your running Hyprland commit
    when available in hyprpm.toml.
  - Installs .so files to ~/.local/lib (no sudo required).
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

plugins=("$@")
if [[ ${#plugins[@]} -eq 0 ]]; then
  plugins=("hyprexpo")
fi

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1" >&2; exit 1; }; }
need hyprctl
need curl
need awk
need tar
need make

HYPR_VERSION="$(hyprctl version 2>/dev/null || true)"
HYPR_COMMIT="$(sed -nE 's/.* at commit ([0-9a-f]{40}) .*/\1/p' <<<"$HYPR_VERSION" | head -n1)"
if [[ -z "$HYPR_COMMIT" ]]; then
  echo "Could not parse running Hyprland commit from 'hyprctl version'." >&2
  exit 1
fi

MANIFEST_URL="https://raw.githubusercontent.com/hyprwm/hyprland-plugins/main/hyprpm.toml"
MANIFEST="$(curl -fsSL "$MANIFEST_URL")"

PINNED_COMMIT="$(
  awk -v want="$HYPR_COMMIT" '
    match($0, /\["([0-9a-f]{40})", "([0-9a-f]{40})"\]/, m) {
      if (m[1] == want) {
        print m[2]
        exit
      }
    }
  ' <<<"$MANIFEST"
)"

if [[ -n "$PINNED_COMMIT" ]]; then
  REF="$PINNED_COMMIT"
  TARBALL_URL="https://github.com/hyprwm/hyprland-plugins/archive/${REF}.tar.gz"
  echo "Using pinned hyprland-plugins commit: $REF"
else
  REF="main"
  TARBALL_URL="https://github.com/hyprwm/hyprland-plugins/archive/refs/heads/main.tar.gz"
  echo "No pin found for Hyprland commit $HYPR_COMMIT, using hyprland-plugins main."
fi

WORKDIR="$(mktemp -d)"
cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

SRC="$WORKDIR/hyprland-plugins"
mkdir -p "$SRC"
curl -fsSL "$TARBALL_URL" | tar -xz --strip-components=1 -C "$SRC"

mkdir -p "$HOME/.local/lib"

for plugin in "${plugins[@]}"; do
  plugdir="$SRC/$plugin"
  if [[ ! -d "$plugdir" ]]; then
    echo "Plugin directory not found in source tree: $plugin" >&2
    exit 1
  fi

  echo "Building $plugin..."
  make -C "$plugdir" all

  built_so="$plugdir/$plugin.so"
  if [[ ! -f "$built_so" ]]; then
    built_so="$(find "$plugdir" -maxdepth 1 -type f -name '*.so' | head -n1 || true)"
  fi
  if [[ -z "$built_so" || ! -f "$built_so" ]]; then
    echo "Build finished but no .so found for $plugin" >&2
    exit 1
  fi

  dest="$HOME/.local/lib/$plugin.so"
  install -Dm755 "$built_so" "$dest"
  echo "Installed: $dest"
done

echo
echo "Done. Reload Hyprland to pick up plugin changes:"
echo "  hyprctl reload"
