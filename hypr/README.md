# Hypr Layout

`hypr/` maps to `~/.config/hypr/` via Stow.

## Structure

- `hypr/hyprland.conf`: main Hyprland config.
- `hypr/hyprlock.conf`, `hypr/hyprpaper.conf`: lock + wallpaper daemon config.
- `hypr/scripts/`: launchers and helper scripts used by keybinds/autostart.
- `hypr/profiles/`: machine-specific monitor, workspace, and hardware-key snippets.
- `hypr/assets/`: wallpapers and image assets.
- `hypr/bin/`: vendored helper binaries (currently `hypr-alttab`).
- `hypr/archive/`: historical backups/reference configs.

## Monitor Profiles

`hypr/hyprland.conf` loads the local, untracked selector:

`source = $HOME/.config/hypr/machine.conf`

Select laptop mode in `machine.conf` with:

`source = $HOME/.config/hypr/profiles/laptop.conf`

Select desktop mode with:

`source = $HOME/.config/hypr/profiles/desktop.conf`

Each profile also owns the unmodified function/media keys. The desktop profile
uses DDC/CI for external-display brightness; the laptop profile uses the
internal backlight.

Like Niri's `machine.kdl`, `machine.conf` is stowed but ignored by Git so a
pull cannot change another machine's active profile. Then reload:

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
