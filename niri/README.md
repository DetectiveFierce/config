# Niri + DMS Setup

This directory is stowed to `~/.config/niri/`.

## 1) Install required packages

Arch Linux (base set used by this config and keybinds):

```bash
sudo pacman -S --needed \
  git stow niri \
  kitty ghostty foot thunar \
  waybar walker hyprlock \
  wl-clipboard cliphist grim slurp imagemagick \
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
niri msg action load-config-file
```

## 3) Device-specific monitor layouts

Shared Niri settings live in `config.kdl`. Monitor layouts are split by device:

- `outputs/laptop.kdl` contains the laptop panel settings.
- `outputs/desktop.kdl` contains the desktop monitor topology.

Both files are included by `config.kdl`. Niri ignores definitions for outputs
that are not connected, so pulling on either device does not require changing a
profile selector or modifying a tracked file. If a connector name changes, run
`niri msg outputs` on that device and update only its output file.

### Desktop layout details

Hyprland desktop layout source:

`~/.config/hypr/profiles/desktop.conf`

Current profile values:

```ini
monitor=HDMI-A-2,1920x1080,0x0,1
monitor=HDMI-A-1,1920x1080,1920x0,1
monitor=DP-1,2560x1600@60,1120x1080,2
```

Niri equivalent (`outputs/desktop.kdl`):

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

After changing either output profile, run:

```bash
niri msg action load-config-file
```

Check output names and available modes with:

```bash
niri msg outputs
```

## 4) Pull updates on another device

```bash
cd ~/config
git pull --ff-only
./dotfiles apply
niri validate
niri msg action load-config-file
```

`./dotfiles apply` is needed when a pull adds new files, because it creates the
new symlinks under `~/.config`. Existing symlinked files update immediately.

Files created locally by niri-settings (`basicsettings.kdl` and `keybinds.kdl`)
are optional includes and stay outside Git. Shared workflow overrides live in
`shared/workflow.kdl`, loaded after those includes so both machines get the
same key behavior.
