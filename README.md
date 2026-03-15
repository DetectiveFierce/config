# Dotfiles

Personal config files managed with [GNU Stow](https://www.gnu.org/software/stow/) through a single control script: `./dotfiles`.

## Source of truth

This repository is the canonical source for your user config files.

- Edit files in this repo (for example, `$HOME/config`)
- Apply symlinks into `$HOME` with `./dotfiles apply`
- Track all changes with Git in this repo

```text
~/config/
├── alacritty/          -> ~/.config/alacritty/
├── Antigravity/        -> ~/.config/Antigravity/
├── Cursor/             -> ~/.config/Cursor/
├── foot/               -> ~/.config/foot/
├── fuzzel/             -> ~/.config/fuzzel/
├── ghostty/            -> ~/.config/ghostty/
├── hypr/               -> ~/.config/hypr/
├── hypr-dock/          -> ~/.config/hypr-dock/
├── kitty/              -> ~/.config/kitty/
├── niri/               -> ~/.config/niri/
├── nvim/               -> ~/.config/nvim/
├── rstudio/            -> ~/.config/rstudio/
├── walker/             -> ~/.config/walker/
├── waybar/             -> ~/.config/waybar/
├── vicinae/
│   ├── .config/vicinae/          -> ~/.config/vicinae/
│   └── .local/share/vicinae/     -> ~/.local/share/vicinae/
├── zed/                -> ~/.config/zed/
└── zsh/
    └── .zshrc          -> ~/.zshrc
```

## Packages

XDG targets (`~/.config/<name>/...`):

- `alacritty`
- `Antigravity`
- `Cursor`
- `foot`
- `fuzzel`
- `ghostty`
- `hypr`
- `hypr-dock`
- `kitty`
- `niri`
- `nvim`
- `rstudio`
- `walker`
- `waybar`
- `zed`

Home target (`~/...`):

- `zsh`
- `vicinae`

Theme targets (`~/.local/share/themes/<name>/...`):

- `GTK Theme` -> `Dark-Green-Jungle`
- `Hate of Nature GTK Theme` -> `Hate-of-Nature`

## Commands

```bash
# Check prerequisites and detect stow conflicts
./dotfiles doctor

# Show per-package managed/unmanaged/missing status
./dotfiles status

# First-time setup (safe): backup conflicts, then symlink
./dotfiles apply --backup

# Normal re-apply after edits
./dotfiles apply

# Preview without changing files
./dotfiles apply --dry-run

# Remove all managed symlinks
./dotfiles remove

# Validate before pushing to main
./scripts/pre-push-checks.sh

# Rebuild Hate-of-Nature from the Catppuccin Mocha base theme (auto-download fallback)
./scripts/build-hate-of-nature-gtk-theme.sh

# Run the full Hate-of-Nature build-and-validate suite
./scripts/test-hate-of-nature-gtk-theme.sh

# Audit built GTK colors against the approved Hate-of-Nature palette
./scripts/test-hate-of-nature-gtk-theme-colors.pl

# Verify app/widget selector coverage for key GTK surfaces
./scripts/test-hate-of-nature-gtk-theme-selector-coverage.pl

# Include GTK assets in the audit and print all color groups
./scripts/test-hate-of-nature-gtk-theme-colors.pl --include-assets --max-colors 0
```

## First-time migration (recommended)

If files already exist in `~/.config` or `~`, run:

```bash
./dotfiles apply --backup
```

Conflicting files are moved to:

```text
~/.local/state/dotfiles/backups/<timestamp>/
```

Then Stow creates symlinks back into this repo.

## Legacy wrappers

These still work, but now delegate to `./dotfiles`:

- `./stow-all.sh` -> `./dotfiles apply`
- `./unstow-all.sh` -> `./dotfiles remove`

## Notes

- `./dotfiles apply --adopt` is available if you explicitly want Stow to adopt target files into the repo.
- Hypr monitor profiles live in `hypr/profiles/` and are sourced from `hypr/hyprland.conf`.
- Hypr directory layout is documented in `hypr/README.md`.
