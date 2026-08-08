# Niri Configuration

Niri is the primary compositor. Git owns all niri input, appearance, layout,
rules, outputs, and bindings. DMS-generated Niri fragments are also tracked,
so changes made in the DMS GUI update this repository immediately.

## Layout

`config.kdl` is an ordered include index:

- `core/` contains input, layout, appearance, workspaces, and session settings.
- `rules/` contains application and layer rules.
- `binds/` contains the canonical window, application, and system keymaps.
- `outputs/` contains tracked laptop and desktop monitor definitions.
- `machine-profiles/` contains only device-specific hardware bindings.
- `dms/` is the generated override layer owned by the DMS GUI.
- `machine.kdl` is an ignored local selector.

Generated `basicsettings.kdl` and `keybinds.kdl` files from niri-settings remain
local and excluded. In contrast, every `dms/*.kdl` file is included and deployed
back to this repository. Do not edit DMS fragments by hand; use the DMS GUI and
review the resulting `git diff` here.

## Setup

```bash
git clone https://github.com/DetectiveFierce/config.git ~/config
cd ~/config
cp .dotter/local.toml.example .dotter/local.toml
dotter deploy --dry-run
dotter deploy
./dotfiles bootstrap
./dotfiles doctor
./scripts/check-niri.sh
```

Select hardware controls locally:

```kdl
// Desktop
include "machine-profiles/desktop.kdl"

// Laptop
include "machine-profiles/laptop.kdl"
```

Store the selected line in `niri/machine.kdl`; Git intentionally ignores it.
Both output files are always included because niri ignores disconnected
outputs.

## Editing and synchronization

```bash
cd ~/config
git pull --ff-only
dotter deploy
./scripts/check-niri.sh
niri msg action load-config-file
```

Existing linked files update immediately. Re-run `dotter deploy` when a pull adds or
moves files. See `KEYMAP.md` for the shortcut model and run `niri msg outputs`
before changing monitor identities, modes, scales, or positions.

The DMS compositor, display, keybinding, cursor, theme, and window-rule menus
write through `~/.config/niri/dms/*.kdl` symlinks into `niri/dms/`. Run
`./scripts/check-niri.sh` after GUI changes; it validates the complete include
graph and detects conflicts between handwritten and DMS-generated bindings.

Hyprland remains a secondary compatibility configuration. Shared commands live
in `~/.local/bin`; compositor-neutral behavior must not be added under
`hypr/scripts`.
