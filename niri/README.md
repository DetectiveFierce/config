# Niri + DMS Setup

This directory is stowed to `~/.config/niri/`.

## 1) Install required packages

Arch Linux (base set used by this config and keybinds):

```bash
sudo pacman -S --needed \
  git stow niri \
  kitty ghostty foot thunar \
  waybar walker hyprlock \
  wl-clipboard cliphist grim slurp hyprpicker \
  playerctl brightnessctl ddcutil
```

Also install the Dank Material Shell application itself from your preferred source.  
This repo provides its config under `DankMaterialShell/` (stowed to `~/.config/DankMaterialShell/`).

## 2) Import and apply the config

```bash
git clone https://github.com/DetectiveFierce/config.git ~/config
cd ~/config
./dotfiles doctor
./dotfiles apply --backup
```

`--backup` moves conflicting local files to:

```text
~/.local/state/dotfiles/backups/<timestamp>/
```

Verify symlinks:

```bash
ls -l ~/.config/niri/config.kdl
ls -l ~/.config/DankMaterialShell/settings.json
```

Reload Niri config after edits:

```bash
niri msg action reload-config
```

## 3) Match Niri outputs to the Hyprland desktop monitor layout

Hyprland desktop layout source:

`~/.config/hypr/profiles/desktop.conf`

Current profile values:

```ini
monitor=HDMI-A-2,1920x1080,0x0,1
monitor=HDMI-A-1,1920x1080,1920x0,1
monitor=DP-1,2560x1600@60,1120x1080,2
```

Niri equivalent block:

```kdl
output "HDMI-A-2" {
    mode "1920x1080"
    scale 1
    transform "normal"
    position x=0 y=0
}

output "HDMI-A-1" {
    mode "1920x1080"
    scale 1
    transform "normal"
    position x=1920 y=0
}

output "DP-1" {
    mode "2560x1600@60"
    scale 2
    transform "normal"
    position x=1120 y=1080
}
```

Apply it by replacing the `output` section in `~/.config/niri/config.kdl` (or the repo copy at `niri/config.kdl`), then run:

```bash
niri msg action reload-config
```

If output names differ on your machine, check them with:

```bash
niri msg outputs
```
