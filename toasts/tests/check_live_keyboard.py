"""Manual-on-demand integration check against this desktop's real toast and receiver."""
import asyncio
import json
from pathlib import Path
import subprocess
import uuid
import aiohttp

def layers():
    return json.loads(subprocess.check_output(['niri', 'msg', '-j', 'layers']))
def exclusive():
    return any(x['namespace'] == 'dms:notification-popup' and x['keyboard_interactivity'] == 'Exclusive' for x in layers())
async def main():
    if exclusive():
        raise RuntimeError("Another action toast is active; refusing to inject keys")
    types = subprocess.run(['wl-paste', '--list-types'], capture_output=True, text=True).stdout.splitlines()
    oldtype = 'image/png' if 'image/png' in types else (types[0] if types else None)
    old = subprocess.check_output(['wl-paste', '--no-newline', '--type', oldtype]) if oldtype else b''
    marker = b'LocalSend keyboard integration check\n'
    files = []
    try:
        async with aiohttp.ClientSession() as client:
            for key, expected in [('Escape', 403), ('Return', 200), ('space', 200)]:
                name = f'.localsend-key-test-{uuid.uuid4().hex}.txt'
                metadata = {'info': {'alias': 'Keyboard test'}, 'files': {'check': {'id': 'check', 'fileName': name, 'fileType': 'text/plain', 'size': len(marker)}}}
                task = asyncio.create_task(client.post('https://127.0.0.1:53317/api/localsend/v2/prepare-upload', json=metadata, ssl=False))
                for _ in range(100):
                    if exclusive(): break
                    if task.done(): raise RuntimeError(f'Prepare ended early: {(await task).status}')
                    await asyncio.sleep(.05)
                else: raise RuntimeError('No exclusive file-drop toast appeared; no key sent')
                await asyncio.sleep(.4)
                if key == 'Return':
                    subprocess.run(['grim', '-o', 'HDMI-A-1', '/tmp/localsend-final-keyboard-toast.png'], check=True)
                subprocess.run(['wtype', '-k', key], check=True)
                response = await asyncio.wait_for(task, 5)
                assert response.status == expected, (key, response.status, await response.text())
                if expected == 200:
                    session = await response.json()
                    result = await client.post('https://127.0.0.1:53317/api/localsend/v2/upload', timeout=aiohttp.ClientTimeout(total=8), params={'sessionId': session['sessionId'], 'fileId': 'check', 'token': session['files']['check']}, data=marker, ssl=False)
                    assert result.status == 200, (result.status, await result.text())
                    path = Path(subprocess.check_output(['xdg-user-dir', 'DOWNLOAD'], text=True).strip()) / name
                    files.append(path)
                    assert path.read_bytes() == marker
                    assert subprocess.check_output(['wl-paste', '--no-newline']) == marker
                print(f'{key}: correct decision; Downloads and clipboard verified' if expected == 200 else f'{key}: rejected without saving', flush=True)
                for _ in range(100):
                    if not exclusive(): break
                    await asyncio.sleep(.05)
                assert not exclusive(), 'Toast kept keyboard focus after decision'
                await asyncio.sleep(.4)
    finally:
        for path in files: path.unlink(missing_ok=True)
        current = subprocess.run(['wl-paste', '--no-newline'], capture_output=True).stdout
        if current == marker:
            subprocess.run(['wl-copy', '--type', oldtype], input=old, check=True) if oldtype else subprocess.run(['wl-copy', '--clear'], check=True)
asyncio.run(main())
