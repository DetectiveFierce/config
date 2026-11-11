#!/bin/sh
set -eu
# Resolve the repository from this script so the deployment works on any host.
repo=$(cd "$(dirname "$0")/.." && pwd)
home=$HOME
uid=$(id -u)
if [ "$uid" = 0 ]; then
    echo 'Run this as your desktop user, not root.' >&2
    exit 2
fi
make -C "$repo/storage-advisor/native" TARGET_UID="$uid"
install -d "$home/.local/bin" "$home/.config/DankMaterialShell/plugins" "$home/.config/systemd/user"
ln -sfn "$repo/bin/storage-advisor" "$home/.local/bin/storage-advisor"
ln -sfn "$repo/DankMaterialShell/plugins/StorageAdvisor" "$home/.config/DankMaterialShell/plugins/StorageAdvisor"
for unit in "$repo"/systemd-user/storage-advisor*; do
    ln -sfn "$unit" "$home/.config/systemd/user/${unit##*/}"
done
systemctl --user daemon-reload
systemctl --user enable --now storage-advisor-activity.service storage-advisor-analyze.timer storage-advisor-full.timer
pkexec /usr/bin/env STORAGE_ADVISOR_UID="$uid" STORAGE_ADVISOR_HOME="$home" \
    /bin/sh "$repo/storage-advisor/native/install-root.sh"
dms restart
