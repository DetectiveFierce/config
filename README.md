# Dotfiles

Personal configuration files managed with [GNU Stow](https://www.gnu.org/software/stow/).

## Structure

```
~/config/
├── alacritty/          → ~/.config/alacritty/
├── Antigravity/        → ~/.config/Antigravity/
├── Cursor/             → ~/.config/Cursor/
├── foot/               → ~/.config/foot/
├── ghostty/            → ~/.config/ghostty/
├── hypr/               → ~/.config/hypr/
├── hypr-dock/          → ~/.config/hypr-dock/
├── kitty/              → ~/.config/kitty/
├── niri/               → ~/.config/niri/
├── nvim/               → ~/.config/nvim/
├── rstudio/            → ~/.config/rstudio/
├── walker/             → ~/.config/walker/
├── waybar/             → ~/.config/waybar/
├── zed/                → ~/.config/zed/
└── zsh/
    └── .zshrc          → ~/.zshrc
```

## Quick Start

### Apply All Configs
```bash
./stow-all.sh
```

### Remove All Symlinks
```bash
./unstow-all.sh
```

## Manual Usage

### Stow a Single Package
```bash
cd ~/config

# For XDG configs (apps in ~/.config/)
mkdir -p ~/.config/nvim
stow -t ~/.config/nvim -d . -S nvim --no-folding

# For home directory files
cd zsh && stow -t ~ .
```

### Unstow a Single Package
```bash
cd ~/config
stow -D -t ~/.config/nvim -d . -S nvim

# Or for zsh
cd zsh && stow -D -t ~ .
```

### Add a New Config

1. Create the directory in `~/config/`:
   ```bash
   mkdir -p ~/config/newapp
   ```

2. Add your config files to it

3. Stow it:
   ```bash
   mkdir -p ~/.config/newapp
   stow -t ~/.config/newapp -d ~/config -S newapp --no-folding
   ```

4. Update `stow-all.sh` to include the new package

## How It Works

GNU Stow creates symlinks from target locations back to this repository:

```
~/.config/nvim/init.lua  →  ~/config/nvim/init.lua
~/.zshrc                 →  ~/config/zsh/.zshrc
```

**Editing**: Edit files directly in `~/config/`. Changes appear immediately at the target location via symlinks.

**Version Control**: This directory can be a git repo. All configs are versioned in one place.

## Flags Reference

| Flag | Description |
|------|-------------|
| `-t <dir>` | Target directory for symlinks |
| `-d <dir>` | Directory containing stow packages |
| `-S <pkg>` | Stow (create symlinks for) a package |
| `-D <pkg>` | Delete (remove symlinks for) a package |
| `-v` | Verbose output |
| `--no-folding` | Create individual symlinks, not directory symlinks |

## Included Configs

| App | Description |
|-----|-------------|
| **alacritty** | GPU-accelerated terminal |
| **Antigravity** | VS Code fork - settings, keybindings |
| **Cursor** | AI editor - settings, keybindings, theme |
| **foot** | Wayland terminal |
| **ghostty** | GPU terminal |
| **hypr** | Hyprland window manager |
| **hypr-dock** | hypr-alttab switcher configuration |
| **kitty** | Terminal emulator |
| **niri** | Niri window manager |
| **nvim** | Neovim configuration |
| **rstudio** | RStudio IDE settings, snippets, theme |
| **walker** | Launcher configuration and themes |
| **waybar** | Wayland status bar |
| **zed** | Zed editor |
| **zsh** | Shell config with oh-my-zsh |
