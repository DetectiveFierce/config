#!/usr/bin/python
"""Wait for the replacement shell to be ready before showing reload feedback."""
import subprocess
import time
# The successful-reload signal belongs to the outgoing QML generation.
# An independent process survives its destruction and contacts the new shell.
time.sleep(2)
for _ in range(20):
    try:
        result = subprocess.run(['/usr/bin/dms', 'ipc', 'toast', 'info', 'Configuration reloaded'], capture_output=True, text=True, timeout=3)
        if 'TOAST_INFO_SUCCESS' in result.stdout:
            break
    except subprocess.TimeoutExpired:
        pass
    time.sleep(.3)
