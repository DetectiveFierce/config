#!/bin/sh
set -eu
repo=/home/shared-psychosis/config
home=/home/shared-psychosis
if [ "$(id -u)" != 1000 ] || [ "$HOME" != "$home" ]; then
    echo 'This deployment is scoped to the shared-psychosis workstation.' >&2
    exit 2
fi
make -C "$repo/storage-advisor/native" TARGET_UID=1000
install -d "$home/.local/bin" "$home/.config/DankMaterialShell/plugins" "$home/.config/systemd/user"
ln -sfn "$repo/bin/storage-advisor" "$home/.local/bin/storage-advisor"
ln -sfn "$repo/DankMaterialShell/plugins/StorageAdvisor" "$home/.config/DankMaterialShell/plugins/StorageAdvisor"
for unit in "$repo"/systemd-user/storage-advisor*; do
    ln -sfn "$unit" "$home/.config/systemd/user/${unit##*/}"
done
systemctl --user daemon-reload
systemctl --user enable --now storage-advisor-activity.service storage-advisor-analyze.timer storage-advisor-full.timer
pkexec /bin/sh "$repo/storage-advisor/native/install-root.sh"
dms restart
