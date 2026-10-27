import hashlib
import importlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.collections'))
upload = importlib.import_module('ansible_collections.degitag.proxmox.plugins.modules.iso_upload')


class Exit(BaseException):
    def __init__(self, value):
        self.value = value


class Module:
    def __init__(self, path, check=False):
        self.check_mode = check
        digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        self.params = {'api': {}, 'path': str(path), 'node': 'pve01', 'storage': 'local',
                       'name': 'ks-3011-' + digest + '.iso', 'timeout': 600}

    def exit_json(self, **kwargs):
        raise Exit(kwargs)

    def fail_json(self, **kwargs):
        raise Exit(dict(kwargs, failed=True))


class API:
    def __init__(self):
        self.volumes = []
        self.writes = []
        self.waited = []
        self.fail_task = False

    def get(self, path):
        return self.volumes

    def request(self, method, path, data, files):
        self.writes.append((method, path))
        self.upload_stream = files['filename'][1]
        self.uploaded = self.upload_stream.read()
        return 'UPID:test'

    def wait(self, *args):
        self.waited.append(args)
        if self.fail_task:
            raise RuntimeError('Proxmox task did not finish successfully')


class UploadTests(unittest.TestCase):
    def execute(self, module, api):
        with patch.object(upload, 'AnsibleModule', return_value=module), patch.object(upload, 'ProxmoxAPI', return_value=api):
            with self.assertRaises(Exit) as result:
                upload.main()
        return result.exception.value

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'installer.iso'
        self.path.write_bytes(b'installer-fixture')

    def test_upload_waits_and_closes_stream(self):
        api = API()
        result = self.execute(Module(self.path), api)
        self.assertTrue(result['changed'])
        self.assertEqual(api.uploaded, b'installer-fixture')
        self.assertTrue(api.upload_stream.closed)
        self.assertEqual(api.waited, [('pve01', 'UPID:test', 600)])

    def test_existing_fingerprint_is_reused(self):
        module = Module(self.path)
        api = API()
        api.volumes = [{'volid': 'local:iso/' + module.params['name'], 'size': self.path.stat().st_size}]
        result = self.execute(module, api)
        self.assertFalse(result['changed'])
        self.assertEqual(api.writes, [])

    def test_wrong_remote_size_refuses_overwrite(self):
        module = Module(self.path)
        api = API()
        api.volumes = [{'volid': 'local:iso/' + module.params['name'], 'size': 1}]
        result = self.execute(module, api)
        self.assertTrue(result['failed'])
        self.assertEqual(api.writes, [])

    def test_check_mode_has_no_upload(self):
        api = API()
        result = self.execute(Module(self.path, check=True), api)
        self.assertTrue(result['changed'])
        self.assertEqual(api.writes, [])

    def test_failed_task_is_not_reported_as_success(self):
        api = API()
        api.fail_task = True
        result = self.execute(Module(self.path), api)
        self.assertTrue(result['failed'])
        self.assertNotIn('volid', result)


if __name__ == '__main__':
    unittest.main()
