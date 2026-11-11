#!/bin/sh
set -eu
src=/home/shared-psychosis/config/storage-advisor/native
dst=/usr/local/libexec/storage-advisor
install -d -m 0755 -o root -g root "$dst"
install -m 0755 -o root -g root "$src/root_collector.py" "$dst/root_collector.py"
install -m 0755 -o root -g root "$src/guarded_action.py" "$dst/guarded_action.py"
install -m 0755 -o root -g root "$src/build/exec_collector" "$dst/exec_collector"
install -m 0644 -o root -g root "$src/build/exec.bpf.o" "$dst/exec.bpf.o"
install -m 0644 -o root -g root "$src/storage-advisor-root.service" /etc/systemd/system/storage-advisor-root.service
systemctl daemon-reload
systemctl enable --now storage-advisor-root.service
systemctl restart storage-advisor-root.service
