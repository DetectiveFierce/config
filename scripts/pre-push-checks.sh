#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> dotfiles doctor (advisory)"
if ./dotfiles doctor; then
  :
else
  echo "  [warn] dotfiles doctor reported host conflicts."
  echo "         Set STRICT_DOTFILES_DOCTOR=1 to make this fatal."
  if [[ "${STRICT_DOTFILES_DOCTOR:-0}" == "1" ]]; then
    exit 1
  fi
fi

echo
echo "==> bash syntax checks"
shell_scripts=(
  "./dotfiles"
  "./stow-all.sh"
  "./unstow-all.sh"
  "./hypr/hypr-cwd-launch"
  "./scripts/pre-push-checks.sh"
)
while IFS= read -r -d '' script; do
  shell_scripts+=("$script")
done < <(find ./hypr/scripts -maxdepth 1 -type f -print0 | sort -z)

for script in "${shell_scripts[@]}"; do
  bash -n "$script"
  printf '  [ok] %s\n' "$script"
done

if command -v shellcheck >/dev/null 2>&1; then
  echo
  echo "==> shellcheck"
  shellcheck "${shell_scripts[@]}"
else
  echo
  echo "==> shellcheck"
  echo "  [skip] shellcheck not installed"
fi

echo
echo "All pre-push checks passed."
