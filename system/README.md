# System configuration inventory

`~/config` is the canonical repository for portable, user-level configuration.
Root-owned configuration stays in `/etc`; this document records its ownership
and review procedure rather than copying volatile or machine-specific state
into Dotter.

## Do not version here

Never copy the following into this repository:

- `/etc/ssh/ssh_host_*` host keys
- `/etc/mullvad-vpn/` account or settings data
- `/etc/machine-id`, password databases, generated certificate bundles, or
  package-manager keyrings
- libvirt VM definitions and storage state unless a separate, reviewed export
  workflow is created

## Root-owned configuration to review

| Area | Canonical live path | Notes |
| --- | --- | --- |
| Package management | `/etc/pacman.conf`, `/etc/pacman.d/mirrorlist`, `/etc/makepkg.conf` | Maintain locally; review `.pacnew` files after upgrades. |
| Boot and hardware | `/etc/mkinitcpio.conf`, `/etc/modprobe.d/`, `/etc/modules-load.d/`, `/etc/default/udev-rtirq`, `/etc/default/cpufrequtils` | Machine-specific; validate before changing. |
| Network | `/etc/systemd/network/*.network` | Machine-specific interface definitions; do not duplicate credentials. |
| System services | `/etc/systemd/system/` and enabled unit links | Record intentional enables/overrides; use `systemctl` to change them. |
| Kernel tuning | `/etc/sysctl.d/99-sysctl.conf` | Machine-specific. |
| Locale and console | `/etc/locale.conf`, `/etc/locale.gen`, `/etc/vconsole.conf`, `/etc/X11/xorg.conf.d/00-keyboard.conf` | Review during locale or keyboard changes. |

## Maintenance procedure

1. After a package upgrade, run `pacdiff` and review every `.pacnew` or
   `.pacsave` file deliberately. Do not overwrite a live file blindly.
2. For a root-config change, back up the live file, make and validate the
   change with the appropriate service/tool, then update this inventory if the
   ownership or procedure changes.
3. Keep portable application and compositor settings in the mapped paths in
   `~/config/.dotter/global.toml`; deploy only through `dotter deploy --dry-run`
   followed by `dotter deploy` after inspecting the plan.

## Current review queue

The next package-configuration review should cover:

- `/etc/pacman.conf.pacnew`
- `/etc/pacman.d/mirrorlist.pacnew`
- `/etc/mkinitcpio.conf.pacnew`
- `/etc/locale.gen.pacnew`
- `/etc/makepkg.conf.d/fortran.conf.pacnew`
- `/etc/xdg/walker/config.toml.pacnew`
- four `/etc/libvirt/nwfilter/*.pacnew` files
