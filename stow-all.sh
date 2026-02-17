#!/bin/bash
# Stow all dotfiles from ~/config to their target locations
# Run this script to re-apply all symlinks after changes

set -e

DOTFILES_DIR="$HOME/config"
XDG_PACKAGES="alacritty foot ghostty hypr hypr-dock kitty niri nvim rstudio walker waybar zed Antigravity Cursor"

echo "Stowing dotfiles from $DOTFILES_DIR..."

cd "$DOTFILES_DIR"

# Stow each XDG config package to its target in ~/.config
for pkg in $XDG_PACKAGES; do
  if [ -d "$pkg" ]; then
    mkdir -p "$HOME/.config/$pkg"
    stow -v -t "$HOME/.config/$pkg" -d . -S "$pkg" --no-folding 2>/dev/null || \
      echo "  (already stowed or conflict: $pkg)"
  fi
done

# Stow zsh files to home directory
if [ -d "zsh" ]; then
  cd zsh
  stow -v -t "$HOME" . 2>/dev/null || echo "  (already stowed or conflict: zsh)"
  cd ..
fi

echo ""
echo "✓ All dotfiles stowed successfully!"
echo ""
echo "Symlink summary:"
echo "  ~/.config/* → ~/config/*"
echo "  ~/.zshrc    → ~/config/zsh/.zshrc"
