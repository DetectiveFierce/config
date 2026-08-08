# Dotfiles

This repository is the canonical source for the user configuration on this
machine. [Dotter](https://github.com/SuperCuber/dotter) deploys repository
files as symlinks; Git is the only synchronization mechanism.

## Layout

Repository paths describe ownership and purpose, not the target filesystem.
The explicit source-to-target map lives in `.dotter/global.toml`, which keeps
XDG-only scaffolding out of the working tree:

```text
config/
├── niri/             primary compositor configuration
├── hypr/             secondary compositor compatibility
├── bin/              shared commands -> ~/.local/bin
├── wallpapers/       wallpapers -> ~/.local/share/wallpapers
├── systemd-user/     services -> ~/.config/systemd/user
├── vicinae/          settings -> ~/.config/vicinae
├── vicinae-themes/   themes -> ~/.local/share/vicinae/themes
├── nvim/             personal Neovim configuration
├── zsh/              shell configuration
├── DankMaterialShell/
├── scripts/          validation and theme tooling
└── .dotter/          deployment map and machine selection
```

Directories inside an application folder are retained when they are part of
that application's real configuration structure. Pure target-path scaffolding
is represented only in Dotter's map.

## How it works

Dotter separates the repository layout from the paths applications require:

1. `.dotter/global.toml` defines the tracked packages and maps every source
   file or directory to its destination. For example, `wallpapers/` maps to
   `~/.local/share/wallpapers`, and `bin/` maps to `~/.local/bin`.
2. `.dotter/local.toml` selects packages for the current machine and adds the
   ignored Niri and Hypr machine selectors. Create it from
   `.dotter/local.toml.example`; do not commit it.
3. `dotter deploy` creates symbolic links at the destination paths. The files
   themselves stay in this repository, so edits made through `~/.config`,
   `~/.local`, or `~/config` all update the same source files.
4. `.dotter/cache.toml` records what Dotter deployed so it can reconcile moved
   or removed mappings and undeploy them later. The cache is machine-local and
   ignored by Git.

Application-owned subdirectories such as `niri/binds/` remain intact because
they make the configuration easier to navigate. Destination-only scaffolding,
such as `.local/share/wallpapers`, exists only in the Dotter map.

## First-time setup

Install Dotter (`dotter-rs` on Arch), then:

```bash
git clone https://github.com/DetectiveFierce/config.git ~/config
cd ~/config
cp .dotter/local.toml.example .dotter/local.toml
printf 'include "machine-profiles/desktop.kdl"\n' > niri/machine.kdl
printf 'source = $HOME/.config/hypr/profiles/desktop.conf\n' > hypr/machine.conf
dotter deploy --dry-run
dotter deploy
./dotfiles bootstrap
./dotfiles doctor
./scripts/pre-push-checks.sh
```

Use the `laptop` profiles instead on a laptop. The local Dotter file and both
machine selectors are intentionally ignored by Git.

If the first deploy finds pre-existing files or links, inspect the dry-run.
Back up anything not already represented in this repository before using
`dotter deploy --force` to replace it.

## Daily commands

```bash
dotter deploy --dry-run       # preview deployment
dotter deploy                 # apply newly added or moved files
dotter undeploy --dry-run     # preview removal
dotter undeploy               # remove managed links
./dotfiles doctor             # validate config and dependencies
./dotfiles bootstrap          # reconcile pinned dependencies and services
./scripts/check-niri.sh       # niri-specific validation
./scripts/pre-push-checks.sh  # complete repository validation
```

The compatibility helper also provides `./dotfiles apply`, `remove`, and
`status`; each delegates to Dotter. It never pulls or pushes this repository.

## Editing and adding dotfiles

To change an existing setting, edit either its repository source or its
deployed symlink. For example, these edit the same file:

```bash
$EDITOR ~/config/niri/config.kdl
$EDITOR ~/.config/niri/config.kdl
```

To add a managed file:

1. Put it in a short, descriptive repository path under the application that
   owns it.
2. Add its source and destination to `[default.files]` in
   `.dotter/global.toml`. A directory mapping deploys all files below it.
3. Run `dotter deploy --dry-run`, inspect the plan, then run `dotter deploy`.
4. Run `./scripts/pre-push-checks.sh` before committing and pushing.

To move or remove a managed file, update both the repository and the Dotter
map, then deploy again. Dotter uses its cache to remove the obsolete link.

Before publishing changes:

```bash
git status --short
git diff --check
dotter deploy --dry-run
./scripts/pre-push-checks.sh
git add -A
git commit -m "describe the configuration change"
git push
```

## Ownership

- Dotter uses symbolic targets, so editing either a deployed path or its source
  in this repository changes the same file immediately.
- `niri/` is authoritative. DMS-generated fragments are tracked under
  `niri/dms/`; local niri-settings output remains excluded.
- `hypr/` is maintained as a secondary compatibility configuration.
- Oh My Zsh and the styled Hyprpicker build are pinned third-party dependencies
  installed outside this repository by `./dotfiles bootstrap`.
- Machine selectors (`niri/machine.kdl` and `hypr/machine.conf`) remain local.

## Wallpaper flow

`wallpaper-daemon.service` keeps one Awww renderer alive for the graphical
session. `wallpaper-switch.timer` invokes a short one-shot service every 10
minutes. The selector advances through the sorted files in
`${XDG_DATA_HOME:-$HOME/.local/share}/wallpapers` and wraps at the end.

DMS's wallpaper surface is disabled to avoid competing renderers, but its
wallpaper state is updated after each switch so theme integration stays in
sync. Run `wm-wallpaper-switcher --next` for a manual advance.

## Synchronization

```bash
cd ~/config
git pull --ff-only
dotter deploy
./dotfiles doctor
./scripts/check-niri.sh
```

Existing symlinked files update immediately after a pull. Deploy again when a
commit adds or moves files. Review and commit changes normally; there is no
automatic Git commit, pull, or push process.

See `niri/README.md` and `niri/KEYMAP.md` for compositor structure and keys.
