#!/bin/bash
# Unstow (remove symlinks) for all dotfiles
# Use this before making structural changes to the dotfiles repo

set -e

DOTFILES_DIR="$HOME/config"
XDG_PACKAGES="alacritty foot ghostty hypr hypr-dock kitty niri nvim rstudio walker waybar zed Antigravity Cursor"

echo "Unstowing dotfiles..."

cd "$DOTFILES_DIR"

# Unstow each XDG config package
for pkg in $XDG_PACKAGES; do
  if [ -d "$pkg" ]; then
    stow -v -D -t "$HOME/.config/$pkg" -d . -S "$pkg" 2>/dev/null || true
  fi
done

# Unstow zsh files
if [ -d "zsh" ]; then
  cd zsh
  stow -v -D -t "$HOME" . 2>/dev/null || true
  cd ..
fi

echo ""
echo "✓ All dotfiles unstowed!"
