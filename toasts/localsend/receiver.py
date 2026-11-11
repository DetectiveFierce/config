"""LocalSend v2 receiver for a Wayland desktop. No transfer without approval."""
import asyncio
import datetime
import hashlib
import html
import ipaddress
import json
import logging
import os
from pathlib import Path, PurePosixPath
import secrets
import shutil
import socket
import ssl
import struct
import subprocess
import uuid
from aiohttp import web
from dbus_next.aio import MessageBus
from dbus_next import Variant
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

ROOT = Path(__file__).resolve().parent
STATE = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state')) / 'localsend-service'
PORT = 53317
GROUP = '224.0.0.167'
log = logging.getLogger('localsend')

def download_dir():
    result = subprocess.run(['xdg-user-dir', 'DOWNLOAD'], capture_output=True, text=True)
    return Path(result.stdout.strip()) if result.returncode == 0 and result.stdout.strip() else Path.home() / 'Downloads'

def certificate(state):
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    keyfile, certfile = state / 'key.pem', state / 'cert.pem'
    if not keyfile.exists() or not certfile.exists():
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'LocalSend background receiver')])
        now = datetime.datetime.now(datetime.timezone.utc)
        cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
                .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(days=1))
                .not_valid_after(now + datetime.timedelta(days=3650)).sign(key, hashes.SHA256()))
        keyfile.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        keyfile.chmod(0o600)
        certfile.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    cert = x509.load_pem_x509_certificate(certfile.read_bytes())
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(certfile, keyfile)
    return context, cert.fingerprint(hashes.SHA256()).hex()

async def notify(title, body):
    proc = await asyncio.create_subprocess_exec('notify-send', '--app-name=LocalSend', '--icon=folder-download', title, body)
    await proc.wait()

async def ask(alias, files):
    """Desktop action toast, with keyboard handling supplied by our DMS layout."""
    size = sum(f['size'] for f in files.values())
    names = [f['fileName'] for f in files.values()]
    title = f'{alias[:100]} wants to send {"a file" if len(names) == 1 else str(len(names)) + " files"}'
    body = html.escape(names[0][:150])
    if len(names) > 1:
        body += f' + {len(names) - 1} more'
    body += f' · {size / 1024 / 1024:.1f} MB'
    body += '\nEnter / Space: accept · Esc: reject'
    bus = await MessageBus().connect()
    notification_id = None
    try:
        introspection = await bus.introspect('org.freedesktop.Notifications', '/org/freedesktop/Notifications')
        proxy = bus.get_proxy_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications', introspection)
        interface = proxy.get_interface('org.freedesktop.Notifications')
        future = asyncio.get_running_loop().create_future()
        def action(nid, key):
            if nid == notification_id and not future.done():
                future.set_result(key == 'accept')
        def closed(nid, reason):
            if nid == notification_id and not future.done():
                future.set_result(False)
        interface.on_action_invoked(action)
        interface.on_notification_closed(closed)
        owner_proxy = bus.get_proxy_object('org.freedesktop.DBus', '/org/freedesktop/DBus',
            await bus.introspect('org.freedesktop.DBus', '/org/freedesktop/DBus'))
        owner_interface = owner_proxy.get_interface('org.freedesktop.DBus')
        owner = await owner_interface.call_get_name_owner('org.freedesktop.Notifications')
        def owner_changed(name, old, new):
            if name == 'org.freedesktop.Notifications' and new != owner and not future.done():
                future.set_result(False)
        owner_interface.on_name_owner_changed(owner_changed)
        notification_id = await interface.call_notify('LocalSend', 0, 'folder-download', title, body,
            ['reject', 'Reject · Esc', 'accept', 'Accept · Enter / Space'],
            {'urgency': Variant('y', 2), 'transient': Variant('b', True)}, 90000)
        try:
            return await future
        finally:
            await interface.call_close_notification(notification_id)
    except Exception:
        log.exception('Approval notification failed; rejecting transfer')
        return False
    finally:
        bus.disconnect()

async def clipboard(paths, files):
    # Native image/text targets support pasting directly into editors and chat apps.
    # Other transfers use the standard file-manager URI list format.
    kind = 'text/uri-list'
    data = ('\r\n'.join(p.as_uri() for p in paths) + '\r\n').encode()
    if len(paths) == 1:
        mime = next(iter(files.values()))['fileType']
        if mime in ('image/png', 'image/jpeg', 'image/webp', 'image/gif') or mime.startswith('text/'):
            kind = mime if mime.startswith('image/') else 'text/plain;charset=utf-8'
            if paths[0].stat().st_size <= 64 * 1024 * 1024:
                data = paths[0].read_bytes()
            else:
                kind = 'text/uri-list'
    proc = await asyncio.create_subprocess_exec('wl-copy', '--type', kind, stdin=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    _, err = await proc.communicate(data)
    if proc.returncode:
        raise RuntimeError(f'wl-copy exited with status {proc.returncode}')

class Receiver:
    def __init__(self, downloads, fingerprint, approve=ask, copy=clipboard, inform=notify):
        self.downloads = downloads
        self.info = dict(alias=f'{socket.gethostname()} (Downloads)', version='2.1', deviceModel='Linux', deviceType='desktop', fingerprint=fingerprint, port=PORT, protocol='https', download=False)
        self.approve, self.copy, self.inform = approve, copy, inform
        self.session = None
        self.pending = False
        self.transport = None
        self.last_reply = {}

    async def info_route(self, request):
        return web.json_response(self.info)

    def validate(self, data):
        if not isinstance(data, dict) or not isinstance(data.get('info'), dict):
            raise ValueError('Invalid sender')
        files = data.get('files')
        if not isinstance(files, dict) or not 1 <= len(files) <= 10000:
            raise ValueError('Invalid file list')
        for fid, f in files.items():
            if not isinstance(f, dict) or not isinstance(fid, str) or not fid:
                raise ValueError('Invalid file')
            name = f.get('fileName')
            if not isinstance(name, str) or not name or len(name) > 4096 or any(ord(c) < 32 for c in name):
                raise ValueError('Invalid filename')
            path = PurePosixPath(name.replace('\\', '/'))
            if path.is_absolute() or '..' in path.parts or not path.name or ':' in path.parts[0] or path == PurePosixPath('.'):
                raise ValueError('Unsafe filename')
            if type(f.get('size')) is not int or f['size'] < 0:
                raise ValueError('Invalid size')
            if not isinstance(f.get('fileType', ''), str):
                raise ValueError('Invalid type')
            f.setdefault('fileType', 'application/octet-stream')
        return files

    async def prepare(self, request):
        if self.pending or self.session:
            raise web.HTTPConflict(text='Another transfer is active')
        self.pending = True
        try:
            try:
                data = await request.json()
                files = self.validate(data)
            except (ValueError, TypeError, KeyError):
                raise web.HTTPBadRequest(text='Invalid metadata')
            self.downloads.mkdir(parents=True, exist_ok=True)
            if sum(f['size'] for f in files.values()) > shutil.disk_usage(self.downloads).free:
                raise web.HTTPInsufficientStorage(text='Not enough space in Downloads')
            if not await self.approve(str(data['info'].get('alias', 'Unknown device')), files):
                log.info('Transfer rejected')
                raise web.HTTPForbidden(text='Rejected')
            tokens = {fid: secrets.token_urlsafe(32) for fid in files}
            staging = self.downloads / f'.localsend-{uuid.uuid4().hex}'
            staging.mkdir(mode=0o700)
            self.session = dict(id=uuid.uuid4().hex, peer=request.remote, files=files, tokens=tokens, done={}, active=set(), staging=staging, cancelled=False, activity=asyncio.get_running_loop().time())
            log.info('Accepted %d file(s)', len(files))
            return web.json_response(dict(sessionId=self.session['id'], files=tokens))
        finally:
            self.pending = False

    def authorize(self, request):
        s = self.session
        if not s or request.query.get('sessionId') != s['id'] or request.remote != s['peer'] or s['cancelled']:
            raise web.HTTPForbidden(text='Invalid session')
        s['activity'] = asyncio.get_running_loop().time()
        return s

    async def upload(self, request):
        s = self.authorize(request)
        fid = request.query.get('fileId', '')
        token = request.query.get('token', '')
        if fid not in s['tokens'] or not secrets.compare_digest(token, s['tokens'][fid]):
            raise web.HTTPForbidden(text='Invalid token')
        if fid in s['active'] or fid in s['done']:
            raise web.HTTPConflict(text='Already uploaded')
        s['active'].add(fid)
        temp = s['staging'] / uuid.uuid4().hex
        size = 0
        digest = hashlib.sha256()
        try:
            f = s['files'][fid]
            with temp.open('xb') as out:
                async for chunk in request.content.iter_chunked(256 * 1024):
                    if s['cancelled']:
                        raise web.HTTPConflict(text='Cancelled')
                    size += len(chunk)
                    s['activity'] = asyncio.get_running_loop().time()
                    if size > f['size']:
                        raise web.HTTPRequestEntityTooLarge(max_size=f['size'], actual_size=size)
                    out.write(chunk)
                    digest.update(chunk)
            if size != f['size'] or (f.get('sha256') and digest.hexdigest().lower() != f['sha256'].lower()):
                raise web.HTTPUnprocessableEntity(text='Size or checksum mismatch')
            if s['cancelled']:
                raise web.HTTPConflict(text='Cancelled')
            target = self.publish(temp, f['fileName'])
            s['done'][fid] = target
            log.info('Saved %s', target)
            if len(s['done']) == len(s['files']):
                paths = [s['done'][key] for key in s['files']]
                try:
                    await self.copy(paths, s['files'])
                    await self.inform('LocalSend received', f'{len(paths)} file(s) saved to Downloads and copied to clipboard.')
                except Exception:
                    log.exception('Clipboard update failed')
                    await self.inform('LocalSend received', 'Saved to Downloads. Clipboard update failed; see service logs.')
                self.session = None
                shutil.rmtree(s['staging'], ignore_errors=True)
            return web.Response()
        except OSError:
            log.exception('Could not save transfer')
            raise web.HTTPInternalServerError(text='Could not save file')
        finally:
            s['active'].discard(fid)
            temp.unlink(missing_ok=True)
            if s['cancelled'] and not s['active']:
                shutil.rmtree(s['staging'], ignore_errors=True)

    def publish(self, temp, name):
        # Traverse destination folders using directory handles; reject symlinks.
        # Atomic exclusive links protect existing files, even under collisions.
        parts = PurePosixPath(name.replace('\\', '/')).parts
        directory = self.downloads
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            for part in parts[:-1]:
                try:
                    os.mkdir(part, dir_fd=fd)
                except FileExistsError:
                    pass
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
                directory = directory / part
            original = Path(parts[-1])
            for index in range(100000):
                base = original.name if index == 0 else f'{original.stem} ({index}){original.suffix}'
                try:
                    os.link(temp, base, dst_dir_fd=fd)
                    temp.unlink()
                    return directory / base
                except FileExistsError:
                    continue
            raise OSError('Too many filename collisions')
        finally:
            os.close(fd)

    async def cancel(self, request):
        s = self.authorize(request)
        s['cancelled'] = True
        if not s['active']:
            shutil.rmtree(s['staging'], ignore_errors=True)
        self.session = None
        return web.Response()

    def app(self):
        app = web.Application(client_max_size=4 * 1024 * 1024)
        for version in ('v2',):
            prefix = f'/api/localsend/{version}'
            app.router.add_get(prefix + '/info', self.info_route)
            app.router.add_post(prefix + '/register', self.info_route)
            app.router.add_post(prefix + '/prepare-upload', self.prepare)
            app.router.add_post(prefix + '/upload', self.upload)
            app.router.add_post(prefix + '/cancel', self.cancel)
        return app

    def announce(self, announce=True):
        if self.transport:
            self.transport.sendto(json.dumps(dict(self.info, announce=announce)).encode(), (GROUP, PORT))

    async def maintenance(self):
        while True:
            self.announce()
            now = asyncio.get_running_loop().time()
            self.last_reply = {peer: stamp for peer, stamp in self.last_reply.items() if now - stamp < 5}
            s = self.session
            if s and now - s['activity'] > 300 and not s['active']:
                s['cancelled'] = True
                self.session = None
                shutil.rmtree(s['staging'], ignore_errors=True)
                log.info('Expired idle transfer')
            await asyncio.sleep(30)

class Discovery(asyncio.DatagramProtocol):
    def __init__(self, receiver):
        self.receiver = receiver
    def datagram_received(self, data, addr):
        try:
            message = json.loads(data)
            if message.get('fingerprint') == self.receiver.info['fingerprint'] or not message.get('announce'):
                return
            now = asyncio.get_running_loop().time()
            if now - self.receiver.last_reply.get(addr[0], 0) < 3:
                return
            self.receiver.last_reply[addr[0]] = now
            self.receiver.announce(False)
        except (ValueError, AttributeError):
            pass

async def main():
    context, fingerprint = certificate(STATE)
    receiver = Receiver(download_dir(), fingerprint)
    # Remove only abandoned partial uploads from our private staging directories.
    for partial in receiver.downloads.glob('.localsend-*'):
        if partial.is_dir() and not partial.is_symlink() and len(partial.name) == 43:
            shutil.rmtree(partial, ignore_errors=True)
    runner = web.AppRunner(receiver.app(), access_log=None)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', PORT, ssl_context=context).start()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', PORT))
    addresses = subprocess.check_output(['ip', '-j', '-4', 'addr', 'show'], text=True)
    for interface in json.loads(addresses):
        for address in interface.get('addr_info', []):
            if address.get('scope') != 'global':
                continue
            ip = address['local']
            try:
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(GROUP) + socket.inet_aton(ip))
            except OSError:
                log.warning('Cannot join discovery on %s', ip)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
    sock.setblocking(False)
    transport, _ = await asyncio.get_running_loop().create_datagram_endpoint(lambda: Discovery(receiver), sock=sock)
    receiver.transport = transport
    log.info('Receiving as %s; saving to %s', receiver.info['alias'], receiver.downloads)
    try:
        await receiver.maintenance()
    finally:
        transport.close()
        await runner.cleanup()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    asyncio.run(main())
