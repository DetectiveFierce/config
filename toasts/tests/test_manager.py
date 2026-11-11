import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import tarfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('toast_manager',ROOT/'manage.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class BuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory=Path(self.tmp.name)
        self.root=self.directory/'config'
        self.root.mkdir()
        (self.root/'patches').mkdir()
        (self.root/'overlays').mkdir()
        self.base=self.directory/'base'
        self.base.mkdir()
        before='// upstream\nShellRoot {}\n'
        after='// custom\nShellRoot {}\n'
        (self.base/'shell.qml').write_text(before)
        delta=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/shell.qml',tofile='b/shell.qml'))
        (self.root/'patches/shell.patch').write_text(delta)
        data=dict(upstream=dict(version='1.0',url='https://unused.invalid',sha256='0'*64), patches=[dict(path='shell.qml',patch='patches/shell.patch',base_sha256=hashlib.sha256(before.encode()).hexdigest())])
        (self.root/'upstream.json').write_text(json.dumps(data))
    def release(self,name):
        path=self.directory/name
        path.mkdir()
        (path/'BUILD.json').write_text(json.dumps(dict(inputs=name,files={})))
        return path
    def test_health_check_retries_while_qml_starts(self):
        ready=m.subprocess.CompletedProcess([],0,'hidden\n','')
        with patch.object(m,'run'), patch('time.sleep'), patch.object(m.subprocess,'run',side_effect=[m.subprocess.TimeoutExpired('dms',3),ready]) as call:
            m.check_health()
            self.assertEqual(call.call_count,2)
    def test_activation_failure_restores_previous_build(self):
        state=self.directory/'state'
        good,bad=self.release('good'),self.release('bad')
        m.activate(good,state)
        original_activate=m.activate
        with patch.object(m,'STATE',state), patch.object(m,'build',return_value=bad), patch.object(m,'selftest'), patch.object(m,'activate',side_effect=lambda path:original_activate(path,state)), patch.object(m,'check_health',side_effect=[RuntimeError('UI failed'),None]):
            with self.assertRaisesRegex(RuntimeError,'UI failed'):
                m.apply_changes()
        self.assertEqual(m.active(state),good)
    def test_runtime_uses_previous_if_active_is_damaged(self):
        state=self.directory/'state'
        good,bad=self.release('good'),self.release('bad')
        m.point(state/'current',bad)
        m.point(state/'previous',good)
        (bad/'BUILD.json').write_text('{}')
        self.assertEqual(m.runtime_release(state),good)
    def test_runtime_can_fall_back_to_stock(self):
        state=self.directory/'state'
        self.assertIsNone(m.runtime_release(state))
    def test_repair_bypasses_a_damaged_cached_build(self):
        archive=self.directory/'upstream.tar.gz'
        with tarfile.open(archive,'w:gz') as tar:
            tar.add(self.base,arcname='.')
        state=self.directory/'state'
        with patch.object(m,'archive_for',return_value=archive):
            original=m.build(self.root,state,self.directory/'cache')
            (original/'shell.qml').write_text('damaged')
            with self.assertRaisesRegex(RuntimeError,'Generated file was edited'):
                m.build(self.root,state,self.directory/'cache')
            repaired=m.build(self.root,state,self.directory/'cache',fresh=True)
        self.assertNotEqual(original,repaired)
        self.assertEqual((repaired/'shell.qml').read_text(),'// custom\nShellRoot {}\n')
        m.verify_release(repaired)
    def test_exact_patch_and_overlay(self):
        (self.root/'overlays/Custom.qml').write_text('Item {}\n')
        output=self.directory/'result'
        hashes=m.prepare_tree(self.base,output,self.root)
        self.assertEqual((output/'shell.qml').read_text(),'// custom\nShellRoot {}\n')
        self.assertEqual(hashes['Custom.qml'],m.sha(output/'Custom.qml'))
    def test_upstream_drift_is_refused(self):
        (self.base/'shell.qml').write_text('// changed upstream\nShellRoot {}\n')
        with self.assertRaisesRegex(RuntimeError,'Upstream file changed'):
            m.prepare_tree(self.base,self.directory/'result',self.root)
    def test_wrong_patch_is_refused(self):
        (self.root/'patches/shell.patch').write_text('--- a/shell.qml\n+++ b/shell.qml\n@@ -1 +1 @@\n-impossible context\n+custom\n')
        with self.assertRaisesRegex(RuntimeError,'Patch failed'):
            m.prepare_tree(self.base,self.directory/'result',self.root)
    def test_overlay_edit_changes_build_identity(self):
        initial=m.source_hash(self.root)
        (self.root/'overlays/Custom.qml').write_text('Item {}\n')
        self.assertNotEqual(initial,m.source_hash(self.root))
    def test_atomic_activation_preserves_rollback(self):
        state=self.directory/'state'
        a,b=self.release('a'),self.release('b')
        m.activate(a,state)
        m.activate(b,state)
        self.assertEqual(m.active(state),b)
        self.assertEqual((state/'previous').resolve(),a)
        m.activate((state/'previous').resolve(),state)
        self.assertEqual(m.active(state),a)
        self.assertEqual((state/'previous').resolve(),b)
    def test_modified_build_cannot_replace_current(self):
        state=self.directory/'state'
        good,bad=self.release('good'),self.release('bad')
        m.activate(good,state)
        (bad/'BUILD.json').write_text(json.dumps(dict(inputs='bad',files={'shell.qml':'no-match'})))
        (bad/'shell.qml').write_text('changed')
        with self.assertRaisesRegex(RuntimeError,'Generated file was edited'):
            m.activate(bad,state)
        self.assertEqual(m.active(state),good)
    def test_corrupt_cached_archive_is_refused_without_network(self):
        cache=self.directory/'cache'
        cache.mkdir()
        (cache/('dms-1.0-'+'0'*16+'.tar.gz')).write_bytes(b'not the pinned archive')
        with patch.object(m.urllib.request,'urlopen',side_effect=AssertionError('Must not fetch')):
            with self.assertRaisesRegex(RuntimeError,'Corrupt cached archive'):
                m.archive_for(self.root,cache)
    def test_host_specific_overlay_is_refused(self):
        (self.root/'overlays/Custom.qml').write_text('// /home/someone/private-path\n')
        with self.assertRaisesRegex(RuntimeError,'Host-specific path'):
            m.prepare_tree(self.base,self.directory/'result',self.root)

if __name__=='__main__': unittest.main()
