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

`source = $HOME/.config/hypr/profiles/laptop.conf`

To switch to laptop mode, replace with:

`source = $HOME/.config/hypr/profiles/laptop.conf`

To switch to desktop mode, replace with:

`source = $HOME/.config/hypr/profiles/desktop.conf`

then reload:

```bash
hyprctl reload
```

For matching this desktop monitor topology in Niri, see `niri/README.md`.

## Compatibility

- `hypr/hypr-cwd-launch` is kept as a shim to `hypr/scripts/cwd-launch.sh`.

## Waybar durability

- `hypr/scripts/waybar-supervisor.sh` keeps Waybar running and relaunches it 1 second after a crash.
- Hyprland autostart uses the supervisor instead of launching `waybar` directly.
- To stop both the bar and the supervisor intentionally, run `pkill -f waybar-supervisor.sh`.
