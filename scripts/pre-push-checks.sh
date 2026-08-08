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
  "./hypr/hypr-cwd-launch"
  "./scripts/build-hate-of-nature-gtk-theme.sh"
  "./scripts/pre-push-checks.sh"
  "./scripts/check-niri.sh"
)
while IFS= read -r -d '' script; do
  shell_scripts+=("$script")
done < <(find ./hypr/scripts -maxdepth 1 -type f -print0 | sort -z)
while IFS= read -r -d '' script; do
  shell_scripts+=("$script")
done < <(find ./bin -maxdepth 1 -type f -print0 | sort -z)

for script in "${shell_scripts[@]}"; do
  bash -n "$script"
  printf '  [ok] %s\n' "$script"
done

echo
echo "==> niri configuration"
./scripts/check-niri.sh

echo
echo "==> perl syntax checks"
perl -c "./scripts/test-hate-of-nature-gtk-theme-colors.pl"
perl -c "./scripts/normalize-hate-of-nature-gtk-theme-colors.pl"
perl -c "./scripts/test-hate-of-nature-gtk-theme-light-backgrounds.pl"
perl -c "./scripts/test-hate-of-nature-gtk-theme-selector-coverage.pl"

echo
echo "==> python syntax checks"
python3 - <<'PY'
import os
import py_compile
import tempfile

targets = [
    "./scripts/test-hate-of-nature-gtk-theme-parse.py",
    "./scripts/test-hate-of-nature-gtk-theme-assets.py",
    "./scripts/test-hate-of-nature-gtk-theme-symbols.py",
]

for target in targets:
    fd, cfile = tempfile.mkstemp(suffix=".pyc")
    os.close(fd)
    try:
        py_compile.compile(target, cfile=cfile, doraise=True)
    finally:
        if os.path.exists(cfile):
            os.unlink(cfile)
PY

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
echo "==> comprehensive GTK theme suite"
./scripts/test-hate-of-nature-gtk-theme.sh

echo
echo "All pre-push checks passed."
