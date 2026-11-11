import asyncio
import hashlib
import tempfile
import unittest
from pathlib import Path
from aiohttp.test_utils import TestClient, TestServer
from receiver import Receiver

class TransferTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.approved = True
        self.copied = []
        self.notices = []
        async def approve(alias, files): return self.approved
        async def copy(paths, files): self.copied.append([p.read_bytes() for p in paths])
        async def inform(*args): self.notices.append(args)
        self.receiver = Receiver(Path(self.tmp.name), 'test', approve, copy, inform)
        self.client = TestClient(TestServer(self.receiver.app()))
        await self.client.start_server()
    async def asyncTearDown(self):
        await self.client.close()
        self.tmp.cleanup()
    def metadata(self, name='test.txt', content=b'hello', **extra):
        return {'info': {'alias': 'Phone'}, 'files': {'a': dict(id='a', fileName=name, size=len(content), fileType='text/plain', sha256=hashlib.sha256(content).hexdigest(), **extra)}}
    async def prepare(self, metadata=None):
        return await self.client.post('/api/localsend/v2/prepare-upload', json=metadata or self.metadata())
    async def send(self, session, content=b'hello', token=None):
        return await self.client.post('/api/localsend/v2/upload', params={'sessionId':session['sessionId'], 'fileId':'a', 'token': token or session['files']['a']}, data=content)
    async def test_accept_save_clipboard_and_no_overwrite(self):
        Path(self.tmp.name, 'test.txt').write_text('existing')
        session = await (await self.prepare()).json()
        self.assertEqual((await self.send(session)).status, 200)
        self.assertEqual(Path(self.tmp.name, 'test.txt').read_text(), 'existing')
        self.assertEqual(Path(self.tmp.name, 'test (1).txt').read_bytes(), b'hello')
        self.assertEqual(self.copied, [[b'hello']])
        self.assertIsNone(self.receiver.session)
    async def test_reject_creates_nothing(self):
        self.approved = False
        self.assertEqual((await self.prepare()).status, 403)
        self.assertEqual(list(Path(self.tmp.name).iterdir()), [])
        self.assertEqual(self.copied, [])
    async def test_bad_token_does_not_save(self):
        session = await (await self.prepare()).json()
        self.assertEqual((await self.send(session, token='wrong')).status, 403)
        self.assertFalse(Path(self.tmp.name, 'test.txt').exists())
    async def test_corrupt_or_oversize_files_not_published(self):
        session = await (await self.prepare()).json()
        self.assertEqual((await self.send(session, b'wrong')).status, 422)
        self.assertEqual((await self.send(session, b'too many bytes')).status, 413)
        self.assertFalse(Path(self.tmp.name, 'test.txt').exists())
        self.assertEqual(self.copied, [])
    async def test_paths_cannot_escape_downloads(self):
        for name in ['../escape', '/tmp/escape', 'folder/../../escape', 'C:\\escape']:
            self.assertEqual((await self.prepare(self.metadata(name))).status, 400)
    async def test_cancel_invalidates_tokens(self):
        session = await (await self.prepare()).json()
        self.assertEqual((await self.client.post('/api/localsend/v2/cancel', params={'sessionId': session['sessionId']})).status, 200)
        self.assertEqual((await self.send(session)).status, 403)
        self.assertEqual(list(Path(self.tmp.name).iterdir()), [])
    async def test_multifile_copies_only_after_all_complete(self):
        data = self.metadata()
        data['files']['b'] = dict(id='b', fileName='second.txt', fileType='text/plain', size=0)
        session = await (await self.prepare(data)).json()
        self.assertEqual((await self.send(session)).status, 200)
        self.assertEqual(self.copied, [])
        response = await self.client.post('/api/localsend/v2/upload', params={'sessionId':session['sessionId'], 'fileId':'b', 'token': session['files']['b']}, data=b'')
        self.assertEqual(response.status, 200)
        self.assertEqual(self.copied, [[b'hello', b'']])
    async def test_session_blocks_other_requests(self):
        await self.prepare()
        self.assertEqual((await self.prepare()).status, 409)

    async def test_nested_folders_preserved(self):
        session = await (await self.prepare(self.metadata('photos/test.txt'))).json()
        self.assertEqual((await self.send(session)).status, 200)
        self.assertEqual(Path(self.tmp.name, 'photos/test.txt').read_bytes(), b'hello')
    async def test_symlink_directory_not_followed(self):
        with tempfile.TemporaryDirectory() as outside:
            Path(self.tmp.name, 'photos').symlink_to(outside, target_is_directory=True)
            session = await (await self.prepare(self.metadata('photos/test.txt'))).json()
            self.assertEqual((await self.send(session)).status, 500)
            self.assertEqual(list(Path(outside).iterdir()), [])
            self.assertEqual(self.copied, [])

if __name__ == '__main__': unittest.main()
