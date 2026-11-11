# Desktop toasts

This is the source of truth for the desktop toast design, countdown border,
positioning, and LocalSend receive service. Both native app notifications and
DMS's internal system/Bluetooth/reload toasts use the same card component.

The design follows the supplied LocalSend mockup: dark green background,
IBM Plex Sans and Mono, a small source label without “now,” readable message
and filename text, and a full-width Accept/Reject footer for file requests.
The existing slide-down position and keyboard shortcuts are preserved.

## Install and everyday commands

On this Arch/Niri machine, the dependencies are DMS, Quickshell, GNU `patch`,
Python 3.12 or newer, `uv`, `wl-clipboard`, `libnotify`, `xdg-user-dirs`,
`iproute2`, Fontconfig, and Qt 6's QML test runner/QtTest module. The test
runner is `/usr/lib/qt6/bin/qmltestrunner`; `/usr/bin/qmltestrunner` may be
Qt 5 and is incompatible with these tests.

From the configuration checkout:

```sh
python3 toasts/manage.py install
```

Installation builds and tests the UI, deploys symlinks into this checkout,
installs the bundled fonts, creates the receiver's locked Python environment,
and enables its user service. It restarts DMS and LocalSend to use the result.
Files replaced during the initial migration are preserved under
`~/.local/state/dms-toasts/migration-backups/`.

`./dotfiles bootstrap` also installs this entry, using `--no-restart` so
bootstrapping does not restart an existing desktop. The selected build is
then used at the next DMS start/login. Dotter deploys `toasts/` to
`~/.config/dms-toasts`; both paths refer to these same repository files.

| Command | Purpose |
| --- | --- |
| `dms-toasts doctor` | Check source location, DMS version, active build integrity, deployment links, services, and unapplied changes. |
| `dms-toasts test` | Run builder/recovery, receive-protocol, and Qt hover/border tests. |
| `dms-toasts build` | Create a generated UI without changing the running desktop. |
| `dms-toasts apply` | Build, test, activate, restart DMS, and check that its UI becomes ready. |
| `dms-toasts repair` | Generate a fresh copy even if an existing cached build was edited or damaged, then test and activate it. |
| `dms-toasts rollback` | Switch to the previous generated UI and restart DMS. Repository source is not reverted. |
| `dms-toasts install` | Repair/redeploy links, fonts, locked receiver dependencies, and service installation. |

`install`, `apply`, `repair`, and `rollback` accept `--no-restart`. Use this
when arranging changes for a later login. Edits in this repo do **not**
immediately reload the shell; run `apply` when ready. Generated builds disable
hot reload to avoid a partially saved edit replacing the desktop.

## Where to make changes

| Source | Responsibility |
| --- | --- |
| `overlays/Widgets/ToastCard.qml` | Shared layout, colors, font sizes, source/message/filename hierarchy, and action footer. |
| `overlays/Widgets/CountdownBorder.qml` | Border thickness, green color, rounded geometry, and clockwise drawing. |
| `overlays/Common/CountdownClock.qml` | Remaining time, pause/resume, and holds shared by every screen showing that toast. |
| `overlays/Modules/Toast.qml` | Internal system/Bluetooth toast window, hover, details/copy controls, and slide animation. |
| `patches/01-BarWidgetService.patch` and `04-DankBarContent.patch` | Measure the gap between left-side bar controls and the centered app title. |
| `patches/02-NotificationService.patch` | Give each native notification the shared clock and expire pending file requests when it finishes. |
| `patches/03-ToastService.patch` | Connect the internal toast queue and its lifetimes to the shared clock. |
| `patches/05-NotificationPopup.patch` | Render native notifications using the shared card, positioning, hover holds, and file-request key handling. |
| `patches/07-shell.patch` and `overlays/scripts/toast-reload-notice.py` | Suppress Quickshell's separate debug popup and route reload feedback through the shared toast after the new UI is ready. |
| `localsend/receiver.py` | Receive-only HTTPS/UDP LocalSend v2 implementation, consent, Downloads, and clipboard. |
| `localsend/requirements.in` / `requirements.lock` | Direct Python dependencies and complete hash-verified resolution. |
| `upstream.json` | Pinned upstream release URL/archive hash and the expected hash of every upstream file changed or replaced. |
| `manage.py` | Build, deploy, integrity checks, health check, repair, rollback, and tests. |

Edit these sources, run `dms-toasts test`, then `dms-toasts apply`. For font
or receiver dependency changes, rerun `install`. Avoid editing files inside
the generated build: `doctor` detects such edits and `repair` replaces them.

## Position, animation, and countdown

The bar publishes the actual midpoint of the empty horizontal space between
the right edge of its launcher/workspace section and the left edge of its
centered title section. Toasts center on that point on each configured output.
They slide down from above the screen and settle 6 logical pixels from the
top, overlapping both the bar and the app. They do not reserve workspace.
Normal toasts do not take keyboard focus.

The countdown is a 3-pixel `#A6E22E` perimeter, replacing the old static thick
outline. Its path starts at the top midpoint and continues clockwise through
the straight edges and rounded corners. Drawing skips the elapsed fraction of
the **total path length**, so the disappearing end moves at a consistent speed
rather than speeding up on corners. At zero remaining time no green perimeter
is drawn. A small gutter around the bright Accept button keeps its fill from
concealing the disappearing border.

The same clock drives dismissal and border progress. Hovering adds a hold to
the toast's clock; leaving removes it. Holds are keyed by screen, so a hovered
copy pauses the copies on every monitor. The exact remaining time is retained:
leaving does not restart the animation. Multiple holds, such as a context menu,
can coexist. The application's supplied timeout and existing DMS defaults
remain authoritative; an explicitly untimed notification keeps a full border.

Internal toast details can be expanded and copied. Expanding details holds
the clock until collapsed. Source labels omit relative timestamps everywhere.

## LocalSend

`localsend-receiver.service` starts with the graphical session, restarts on
failure, and stops with the session. It advertises the PC on UDP multicast
`224.0.0.167:53317` and receives encrypted transfers on TCP 53317.

When a request arrives:

1. The sender, file information, and Accept/Reject actions appear in the toast.
2. Enter **or Space** accepts; Escape rejects. The action toast temporarily
   captures keyboard focus; closing it returns focus to the application.
3. Accepted files save to the XDG Downloads directory. Nested paths are
   preserved, collisions get numbered suffixes, and symlinks cannot redirect
   writes outside Downloads. Tokens, expected sizes, and supplied checksums
   are checked before publishing each file.
4. After the whole transfer finishes, a single image/text file up to 64 MiB is
   copied as image/text content. Other transfers copy a file URI list for
   file-manager paste. All received files remain in Downloads.

The request timeout is 90 seconds of **unpaused** desktop time. Python waits
for the notification action/expiry, rather than imposing an independent
wall-clock deadline that would defeat hover pause. A notification-service
restart rejects an outstanding request. The TLS identity remains in the
existing `~/.local/state/localsend-service/` directory and is not in Git.

This receiver occupies the same port as the regular LocalSend app. To send
from the PC using the installed GUI:

```sh
systemctl --user stop localsend-receiver
flatpak run org.localsend.localsend_app
# Quit the GUI before resuming the background receiver:
systemctl --user start localsend-receiver
```

## Reproducibility and recovery

Only patches, overlay components, fonts/licenses, locked dependencies, and
management source are in Git. The entire upstream shell is **not** vendored.
`upstream.json` currently pins the official DMS 1.6.3 QML archive. Its SHA-256
is checked, as is the original content of every file we patch or replace.
Patches require exact context (`--fuzz=0`). A drifted upstream file, corrupt
archive, or rejected hunk stops the build before activation.

Runtime locations honor XDG variables; the defaults are:

```text
~/.cache/dms-toasts/                    verified upstream archive
~/.local/state/dms-toasts/releases/     generated UI builds and BUILD.json hashes
~/.local/state/dms-toasts/current       atomic link to the selected build
~/.local/state/dms-toasts/previous      prior build for rollback
~/.local/state/dms-toasts/localsend-venv/ locked receive-service Python runtime
~/.local/share/fonts/dms-toasts         link to repo fonts and OFL licenses
```

The builder works in a temporary directory, publishes a complete build, then
atomically changes `current`. `apply` checks that DMS's D-Bus service and QML
IPC become ready; failure restores the previous build. At first activation,
with no previous build, failure falls back to stock DMS. The launcher also
tries the previous validated build if the selected build's source files are
corrupt; with neither available, it starts stock DMS rather than leaving an
empty desktop. Cached builds start offline without downloading or rebuilding.

Use these checks first if something breaks:

```sh
dms-toasts doctor
journalctl --user -u dms.service -n 100
journalctl --user -u localsend-receiver.service -n 100
dms-toasts test
dms-toasts repair
# Or restore the previous UI:
dms-toasts rollback
```

The initial ad hoc copies under `~/.local/share/dms-toast-custom` and
`~/.local/share/localsend-service` are no longer used. They can be kept as
migration backups; this entry works without them.

## Updating upstream DMS

Package updates do not silently replace this UI with unreviewed upstream QML.
`doctor` reports when the installed DMS version differs from the UI pin.
Because frontend/backend compatibility can change, update the pin deliberately:

1. Download the new official `dms-qml.tar.gz` release and independently verify
   its published checksum. Update the version, URL, and checksum in
   `upstream.json`.
2. Extract the new original source into a temporary folder. Review changes in
   every patched/replaced file, especially notification timers and bar geometry.
   Rebase the affected patches and regenerate their expected base hashes.
   Do not just change hashes to bypass an unexplained mismatch. Review the
   upstream `Modules/Toast.qml` against our replacement for new functionality.
3. Run `build` and `test`. A build failure leaves the current desktop untouched.
4. Run `apply`, test a real file request, and check ordinary/Bluetooth toasts.
   Keep the previous build until the upgrade is verified.

To update Python dependencies, edit `requirements.in`, regenerate the lock,
then run `install` and repeat the tests:

```sh
uv pip compile --python-version 3.12 --generate-hashes \
  toasts/localsend/requirements.in -o toasts/localsend/requirements.lock
dms-toasts install
``` Keep dependency changes separate from an upstream UI
rebase so failures are easier to locate.

## Tests

The repository pre-push checks also run this suite.

`dms-toasts test` runs thirteen manager tests (including archive drift, patch
failure, atomic activation, startup delay, and rollback), ten receiver tests,
and the Qt 6 hover/border suite. The Qt suite copies the **current repo
components** into a temporary isolated test directory; there is no stale test
copy of the production QML. It injects mouse motion, holds a toast beyond its
original lifetime, resumes it, and checks border pixels and zero-time expiry.

For optional end-to-end testing on this actual desktop:

```sh
~/.local/state/dms-toasts/localsend-venv/bin/python toasts/tests/check_live_keyboard.py
```

That check shows test requests, injects Escape/Enter/Space, verifies actual
Downloads and clipboard behavior, removes test files, and attempts to restore
the previous clipboard. Do not run it while using the keyboard for other work.
It uses Niri's layer inspection and the main desktop output `HDMI-A-1` for its
screenshot; adjust that test-only output name on a different machine.
