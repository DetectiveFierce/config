# Hypr Layout

`hypr/` maps to `~/.config/hypr/` via Stow.

## Structure

- `hypr/hyprland.conf`: main Hyprland config.
- `hypr/hyprlock.conf`, `hypr/hyprpaper.conf`: lock + wallpaper daemon config.
- `hypr/scripts/`: launchers and helper scripts used by keybinds/autostart.
- `hypr/profiles/`: monitor/workspace profile snippets.
- `hypr/assets/`: wallpapers and image assets.
- `hypr/bin/`: vendored helper binaries (currently `hypr-alttab`).
- `hypr/archive/`: historical backups/reference configs.

## Monitor Profiles

`hypr/hyprland.conf` loads this by default:

`source = $HOME/.config/hypr/profiles/desktop.conf`

To switch to laptop mode, replace with:

`source = $HOME/.config/hypr/profiles/laptop.conf`

then reload:

```bash
hyprctl reload
```

## Compatibility

- `hypr/hypr-cwd-launch` is kept as a shim to `hypr/scripts/cwd-launch.sh`.
