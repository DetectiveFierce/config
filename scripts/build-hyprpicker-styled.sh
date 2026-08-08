#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PATCH_FILE="$REPO_ROOT/patches/hyprpicker-square-loupe.patch"
HYPRPICKER_COMMIT="8c163ce9b8a40f85babe4dd6e23a238787351164"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
DEP_ROOT="$DATA_HOME/dotfiles-deps/hyprpicker-styled"
BIN_DIR="$DEP_ROOT/bin"
PICKER="$BIN_DIR/hyprpicker-styled"
STAMP="$DEP_ROOT/build.stamp"

for dep in cmake git ninja pkg-config; do
  if ! command -v "$dep" >/dev/null 2>&1; then
    echo "error: $dep is required to build the styled color picker." >&2
    exit 1
  fi
done

patch_hash="$(sha256sum "$PATCH_FILE" | cut -d' ' -f1)"
source_dir="$DEP_ROOT/source-$patch_hash"
build_dir="$DEP_ROOT/build-$patch_hash"
expected_stamp="$HYPRPICKER_COMMIT $patch_hash"
if [[ -x "$PICKER" && -f "$STAMP" ]] &&
  [[ "$(<"$STAMP")" == "$expected_stamp" ]]; then
  echo "Styled Hyprpicker is current: $PICKER"
  exit 0
fi

mkdir -p "$DEP_ROOT" "$BIN_DIR"
if [[ ! -d "$source_dir/.git" ]]; then
  git clone --quiet https://github.com/hyprwm/hyprpicker.git "$source_dir"
  git -C "$source_dir" checkout --quiet --detach "$HYPRPICKER_COMMIT"
  git -C "$source_dir" apply "$PATCH_FILE"
fi

cmake -S "$source_dir" -B "$build_dir" -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build "$build_dir"
install -m 0755 "$build_dir/hyprpicker" "$PICKER"
printf '%s\n' "$expected_stamp" > "$STAMP"

echo "Built styled Hyprpicker: $PICKER"
