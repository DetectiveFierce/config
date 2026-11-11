#!/usr/bin/env python3
"""Reproducible DMS toast builds, installation, validation and rollback."""
from __future__ import annotations
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parent
STATE = Path(os.environ.get('XDG_STATE_HOME', Path.home()/'.local/state'))/'dms-toasts'
CACHE = Path(os.environ.get('XDG_CACHE_HOME', Path.home()/'.cache'))/'dms-toasts'
DATA = Path(os.environ.get('XDG_DATA_HOME', Path.home()/'.local/share'))
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))


def log(message):
    print(f'[dms-toasts] {message}', file=sys.stderr, flush=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest(root=ROOT):
    return json.loads((root/'upstream.json').read_text())


def source_hash(root=ROOT):
    digest = hashlib.sha256()
    files = [root/'upstream.json']
    for directory in ('patches', 'overlays'):
        files.extend(p for p in (root/directory).rglob('*') if p.is_file())
    for path in sorted(files):
        digest.update(str(path.relative_to(root)).encode()+b'\0'+path.read_bytes())
    return digest.hexdigest()


def run(*args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)


def archive_for(root=ROOT, cache=CACHE):
    upstream = manifest(root)['upstream']
    cache.mkdir(parents=True, exist_ok=True)
    path = cache/f"dms-{upstream['version']}-{upstream['sha256'][:16]}.tar.gz"
    if not path.exists():
        log(f"Downloading pinned DMS {upstream['version']}")
        fd, temporary = tempfile.mkstemp(dir=cache, suffix='.download')
        os.close(fd)
        try:
            with urllib.request.urlopen(upstream['url'], timeout=60) as source, open(temporary,'wb') as output:
                shutil.copyfileobj(source, output)
            if sha(temporary) != upstream['sha256']:
                raise RuntimeError('Upstream archive checksum mismatch; nothing was installed')
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)
    if sha(path) != upstream['sha256']:
        raise RuntimeError(f'Corrupt cached archive: {path}. Remove it and build again.')
    return path


def prepare_tree(base, output, root=ROOT):
    """Copy upstream, verify every edited file, then apply exact-context patches."""
    data = manifest(root)
    shutil.copytree(base, output)
    for entry in data['patches'] + data.get('replacements', []):
        target = output/entry['path']
        if not target.is_file() or sha(target) != entry['base_sha256']:
            raise RuntimeError(f"Upstream file changed: {entry['path']}. Rebase its patch; refusing a partial build.")
    for entry in data['patches']:
        try:
            run('patch', '--batch', '--forward', '--fuzz=0', '-p1', '-d', output,
                '-i', root/entry['patch'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"Patch failed: {entry['patch']}\n{error.stdout.decode(errors='replace')}") from error
    for source in (root/'overlays').rglob('*'):
        if source.is_file():
            target = output/source.relative_to(root/'overlays')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    # Generated runtime has no host-specific paths or connections to the development snapshot.
    checked = [output/e['path'] for e in data['patches']+data.get('replacements', [])]
    checked += [output/p.relative_to(root/'overlays') for p in (root/'overlays').rglob('*') if p.is_file()]
    for target in checked:
        if re.search(rb'/home/[^/\s]+/', target.read_bytes()):
            raise RuntimeError(f'Host-specific path in runtime source: {target}')
    return {str(path.relative_to(output)): sha(path) for path in checked}


def build(root=ROOT, state=STATE, cache=CACHE, fresh=False):
    state.mkdir(parents=True, exist_ok=True)
    with (state/'build.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        identity = source_hash(root)
        release = state/'releases'/(identity[:20]+('-repair-'+uuid.uuid4().hex[:8] if fresh else ''))
        if release.exists():
            verify_release(release, identity)
            return release
        release.parent.mkdir(parents=True, exist_ok=True)
        archive = archive_for(root, cache)
        with tempfile.TemporaryDirectory(dir=release.parent, prefix='.build-') as temporary:
            temporary = Path(temporary)
            base = temporary/'upstream'
            base.mkdir()
            with tarfile.open(archive) as source:
                source.extractall(base, filter='data')
            tree = temporary/'shell'
            hashes = prepare_tree(base, tree, root)
            if source_hash(root) != identity:
                raise RuntimeError('Repo source changed during build; rerun without concurrent edits')
            metadata = dict(inputs=identity, upstream=manifest(root)['upstream']['version'], files=hashes)
            (tree/'BUILD.json').write_text(json.dumps(metadata,indent=2)+'\n')
            os.replace(tree, release)
        log(f'Built {release}')
        return release


def verify_release(path, expected=None):
    data = json.loads((path/'BUILD.json').read_text())
    if expected and data['inputs'] != expected:
        raise RuntimeError(f'Build identity mismatch in {path}')
    for name, checksum in data['files'].items():
        if not (path/name).is_file() or sha(path/name) != checksum:
            raise RuntimeError(f'Generated file was edited: {path/name}; rebuild from repo sources instead')
    return data


def point(link, destination):
    link.parent.mkdir(parents=True, exist_ok=True)
    temporary = link.with_name(link.name+'.new')
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(destination)
    os.replace(temporary, link)


def active(state=STATE):
    path = state/'current'
    return path.resolve() if path.is_symlink() and path.exists() else None


def activate(release, state=STATE):
    verify_release(release)
    old = active(state)
    if old != release:
        if old:
            point(state/'previous', old)
        point(state/'current', release)
    return old


def venv_python():
    return STATE/'localsend-venv/bin/python'


def install_dependencies():
    lock = ROOT/'localsend/requirements.lock'
    marker = STATE/'localsend-venv/requirements.sha256'
    if not venv_python().exists():
        run('uv', 'venv', '--python', '3.12', STATE/'localsend-venv')
    if not marker.exists() or marker.read_text().strip() != sha(lock):
        run('uv', 'pip', 'sync', '--python', venv_python(), '--require-hashes', lock)
        marker.write_text(sha(lock)+'\n')


def safe_link(source, destination):
    """Keep an undoable copy of any pre-migration file before installing a symlink."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() and destination.resolve() == source.resolve():
        return
    if destination.exists() or destination.is_symlink():
        try:
            relative = destination.relative_to(Path.home())
        except ValueError:
            relative = Path('external')/(hashlib.sha256(str(destination).encode()).hexdigest()[:16]+'-'+destination.name)
        backup = STATE/'migration-backups'/relative
        if backup.exists() or backup.is_symlink():
            raise RuntimeError(f'Refusing to replace {destination}; migration backup already exists: {backup}')
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(destination), backup)
    destination.symlink_to(source)


def check_health():
    # Type=dbus waits for the desktop notification service. IPC additionally checks QML readiness.
    run('systemctl', '--user', 'restart', 'dms.service', timeout=30)
    import time
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        try:
            result = subprocess.run(['dms','ipc','toast','status'],capture_output=True,text=True,timeout=3)
            if result.returncode == 0 and (result.stdout.strip() == 'hidden' or result.stdout.strip().startswith('visible:')):
                return
        except subprocess.TimeoutExpired:
            pass  # D-Bus can be ready before async QML/IPC startup finishes.
        time.sleep(.25)
    raise RuntimeError('DMS notification UI did not become ready')


def apply_changes(restart=True, tests=True, fresh=False):
    release = build(fresh=fresh)
    if tests:
        selftest()
    old = activate(release)
    try:
        if restart:
            check_health()
    except (Exception, KeyboardInterrupt):
        if old != release:
            if old:
                point(STATE/'current',old)
                log(f'Activation failed; restoring {old}')
            else:
                (STATE/'current').unlink(missing_ok=True)
                log('First activation failed; starting stock DMS until repaired')
            with contextlib.suppress(Exception):
                check_health()
        raise
    log(f'Active: {release}')


def install(restart=True):
    for command in ('dms','qs','patch','uv','wl-copy','notify-send','xdg-user-dir','ip'):
        if not shutil.which(command):
            raise RuntimeError(f'Missing required command: {command}')
    STATE.mkdir(parents=True, exist_ok=True)
    install_dependencies()
    # Build and test before touching the running service or deployment links.
    build()
    selftest()
    repo = ROOT.parent
    safe_link(ROOT, CONFIG/'dms-toasts')
    safe_link(repo/'bin/dms-toasts', Path.home()/'.local/bin/dms-toasts')
    safe_link(repo/'systemd-user/dms.service.d/toast-layout.conf', CONFIG/'systemd/user/dms.service.d/toast-layout.conf')
    safe_link(repo/'systemd-user/localsend-receiver.service', CONFIG/'systemd/user/localsend-receiver.service')
    safe_link(ROOT/'fonts', DATA/'fonts/dms-toasts')
    if shutil.which('fc-cache'):
        run('fc-cache', DATA/'fonts/dms-toasts')
    run('systemctl','--user','daemon-reload')
    apply_changes(restart=restart, tests=False)
    run('systemctl','--user','enable','localsend-receiver.service')
    if restart:
        run('systemctl','--user','restart','localsend-receiver.service')
    log('Installed. Migration backups are in '+str(STATE/'migration-backups'))


def selftest():
    run(sys.executable, '-B', '-m', 'unittest', 'discover', '-s', ROOT/'tests', '-p', 'test_*.py', '-v')
    if not venv_python().exists():
        raise RuntimeError('Receiver dependencies missing; run dms-toasts install')
    run(venv_python(), '-B', '-m', 'unittest', 'discover', '-s', ROOT/'localsend', '-p', 'test_*.py', '-v')
    runner = next((p for p in ('/usr/lib/qt6/bin/qmltestrunner','/usr/lib64/qt6/bin/qmltestrunner') if Path(p).is_file()), None)
    if runner is None:
        raise RuntimeError('Qt 6 qmltestrunner is required for the hover/border tests (Qt 5 is incompatible)')
    with tempfile.TemporaryDirectory(prefix='dms-toast-test-') as directory:
        directory = Path(directory)
        for source in ('Common/CountdownClock.qml','Widgets/ToastCard.qml','Widgets/CountdownBorder.qml'):
            shutil.copyfile(ROOT/'overlays'/source, directory/Path(source).name)
        shutil.copyfile(ROOT/'tests/tst_hover.qml',directory/'tst_hover.qml')
        env = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software')
        run(runner, '-input', directory, '-o', '-,txt',env=env,timeout=15)


def doctor():
    data = manifest()
    print('Repo:', ROOT)
    print('Pinned upstream:',data['upstream']['version'])
    result = subprocess.run(['dms','version'],capture_output=True,text=True)
    print('Installed DMS:',result.stdout.strip())
    if not re.search(r'\bv'+re.escape(data['upstream']['version'])+r'\b', result.stdout):
        log('Version differs from the pin. Read the upstream upgrade procedure before rebuilding against another release.')
    current = active()
    if not current:
        raise RuntimeError('No active generated UI; run dms-toasts install')
    verify_release(current)
    print('Active:',current)
    print('Repo changes awaiting apply:',source_hash() != json.loads((current/'BUILD.json').read_text())['inputs'])
    for path in (CONFIG/'dms-toasts', CONFIG/'systemd/user/dms.service.d/toast-layout.conf',CONFIG/'systemd/user/localsend-receiver.service'):
        print('Link:',path,'->',path.resolve())
    run('systemctl','--user','is-active','dms','localsend-receiver')


def runtime_release(state=STATE):
    candidates = [active(state), (state/'previous').resolve() if (state/'previous').exists() else None]
    for candidate in candidates:
        if candidate:
            try:
                verify_release(candidate)
                return candidate
            except Exception as error:
                log(str(error))
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['install','build','apply','run','receive','test','doctor','rollback','repair'])
    parser.add_argument('--no-restart',action='store_true',help='Install/apply without restarting desktop services')
    args=parser.parse_args()
    if args.command == 'install': install(not args.no_restart)
    elif args.command == 'build': print(build())
    elif args.command == 'apply': apply_changes(not args.no_restart)
    elif args.command == 'repair': apply_changes(not args.no_restart, fresh=True)
    elif args.command == 'test': selftest()
    elif args.command == 'doctor': doctor()
    elif args.command == 'rollback':
        previous = STATE/'previous'
        if not previous.exists(): raise RuntimeError('No previous generated build is available')
        target = previous.resolve()
        activate(target)
        if not args.no_restart: check_health()
        log(f'Rolled back to {target}; repo source was not changed')
    elif args.command == 'receive':
        if not venv_python().exists(): raise RuntimeError('Run dms-toasts install to create receiver dependencies')
        os.execv(str(venv_python()),[str(venv_python()),'-B',str(ROOT/'localsend/receiver.py')])
    elif args.command == 'run':
        current = active()
        env = dict(os.environ)
        env.pop('DMS_SHELL_DIR',None)
        chosen = runtime_release()
        if chosen:
            env['DMS_SHELL_DIR'] = str(chosen)
            env['DMS_DISABLE_HOT_RELOAD'] = '1'
            if chosen != current:
                log('Starting previous validated UI; run dms-toasts repair to fix the active build')
        else:
            log('No validated UI available; starting stock DMS. Run dms-toasts install/repair.')
        os.execvpe('dms',['dms','run','--session'],env)


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        log(str(error) or 'Interrupted')
        sys.exit(1)
