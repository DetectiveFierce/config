# Storage Advisor

Local, review-first cleanup suggestions for this Arch/Niri workstation. No cloud
API or recurring AI agent is used. The collector records executable names and
daily activity totals, never command arguments or file contents.

The CLI is `~/.local/bin/storage-advisor`. Run `analyze --full` once to build
the inventory, then `list`. `preview ID` returns a current action plan;
`execute ID --token TOKEN` requires the short-lived token returned by preview.
Execution begins disabled until the first live report has been checked. The
DMS popup shows the plan and requires a second explicit confirmation.
After reviewing that report, `storage-advisor settings --enable-execution`
enables the confirmation button. `--disable-execution` closes it again.

The database lives in `$XDG_STATE_HOME/storage-advisor/advisor.db` (normally
`~/.local/state/storage-advisor/advisor.db`). `activityd` receives privileged
collector events on a user-owned Unix socket and consumes Niri's event stream.
Run `./deploy.sh` for service and DMS setup. Deployment of the privileged
collector and the root-owned final action guard requires an interactive
administrator authentication. The root service ships pinned BPF bytecode
and a root-owned Python bridge; it reads only the user-owned watchlist.

The first report includes cache, duplicate, and dependency suggestions. An
"unused" claim needs 60 calendar days with at least 90% simultaneous process
and Niri coverage, so it cannot be made on day one. A missing collector event
is not evidence of disuse. `status` shows collection coverage and scan health.
`backtest` evaluates a 60-day training window against the next 60 covered
days; until then it reports that reliability is unmeasured.

The pinned public MiniLM model lives under `~/.local/share/storage-advisor`.
Run `python3 setup_model.py` only when setting up or changing it. The download
requires no account; the analysis helper forces offline mode and receives only
short desktop-entry descriptions. It is loaded only when app-overlap analysis
becomes eligible. Similarity alone never authorizes removal.

The daily timer checks the selected Daily or Weekly setting. The weekly timer
always runs a full inventory at idle priority; on-demand analysis is
incremental. Raw events are aggregated in memory and daily counters are kept
for at most one year. No arguments, clipboard data, browser history, or file
contents enter the database. File comparison reads eligible files transiently.

The first full inventory on this machine scans large files in the ordinary
home document/media folders, Git projects, packages, Docker, Steam, Flatpak,
desktop entries, MIME defaults, user/system services, and Niri configuration.
Known sensitive and live application paths are excluded. The installed
package cache may be much larger than the subset that paccache identifies for
retirement; Docker virtual image size is never counted as unique recovery.

Restore paths are shown in each fresh preview. Moving a personal file or
generated directory to Trash does not recover disk blocks until Trash is
emptied. The action log is available through `history` and in the DMS popup.
Steam game removal, once eligible, opens Steam's own uninstall dialog; the
advisor records a handoff until the manifest disappears. Shader caches and
compatibility data are measured separately and are not added to game savings.
