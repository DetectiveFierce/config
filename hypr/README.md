# Hypr Layout

Deployable parts of `hypr/` map to `~/.config/hypr/` through Dotter's explicit
source-to-target configuration.

## Structure

- `hypr/hyprland.conf`: main Hyprland config.
- `hypr/hyprlock.conf`: lock-screen configuration.
- `hypr/scripts/`: Hyprland-specific helpers only.
- `hypr/profiles/`: machine-specific monitor, workspace, and hardware-key snippets.
- `hypr/assets/`: Hyprland-specific image assets.
- `hypr/bin/`: vendored helper binaries (currently `hypr-alttab`).
- Shared commands and wallpapers live under `bin/` and `wallpapers/` in the repo.
  Awww runs as the single wallpaper renderer, and a user timer invokes
  `wm-wallpaper-switcher` every 10 minutes.

## Monitor Profiles

`hypr/hyprland.conf` loads the local, untracked selector:

`source = $HOME/.config/hypr/machine.conf`

Select laptop mode in `machine.conf` with:

`source = $HOME/.config/hypr/profiles/laptop.conf`

Select desktop mode with:

`source = $HOME/.config/hypr/profiles/desktop.conf`

Each profile owns only the hardware-specific brightness bindings. The desktop
profile uses DDC/CI for external displays; the laptop profile uses the internal
backlight. Common media keys remain in `hyprland.conf`.

Like Niri's `machine.kdl`, `machine.conf` is deployed but ignored by Git so a
pull cannot change another machine's active profile. Then reload:

```bash
hyprctl reload
```

For matching this desktop monitor topology in Niri, see `niri/README.md`.

## Compatibility

- `hypr/hypr-cwd-launch` is kept as a shim to `~/.local/bin/wm-cwd-launch`.

## Desktop shell

- Hyprland starts DankMaterialShell through `dms.service`, the same user unit niri uses.
- Restart the shell with `systemctl --user restart dms.service`.
