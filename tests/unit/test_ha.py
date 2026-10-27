import copy
import importlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.collections'))
ha = importlib.import_module('ansible_collections.degitag.proxmox.plugins.modules.ha_rules')


class Exit(BaseException):
    def __init__(self, value):
        self.value = value


class Module:
    def __init__(self, profiles, check=False):
        self.params = {'api': {}, 'profiles': profiles}
        self.check_mode = check

    def exit_json(self, **kwargs):
        raise Exit(kwargs)

    def fail_json(self, **kwargs):
        raise Exit(dict(kwargs, failed=True))


class API:
    def __init__(self):
        self.rules = {name: {'rule': name, 'type': 'node-affinity', 'strict': 0,
                            'nodes': 'pve01:2,pve02:1', 'resources': 'vm:9000'} for name in ('one', 'two')}
        self.digest = 0
        self.writes = []

    def get(self, path):
        for rule in self.rules.values():
            rule['digest'] = str(self.digest)
        if path.endswith('/rules'):
            return copy.deepcopy(list(self.rules.values()))
        return copy.deepcopy(self.rules[path.rsplit('/', 1)[-1]])

    def request(self, method, path, data):
        if method == 'PUT':
            if data['digest'] != str(self.digest):
                raise RuntimeError('stale cluster digest')
            self.rules[path.rsplit('/', 1)[-1]].update(data)
        else:
            self.rules[data['rule']] = copy.deepcopy(data)
        self.digest += 1
        self.writes.append((method, data))


class HATests(unittest.TestCase):
    def test_ha_runtime_rejects_stale_manager_and_missing_quorum(self):
        with self.assertRaisesRegex(ValueError, 'inactive or stale'):
            ha.validate_runtime([{'type': 'quorum', 'quorate': 1},
                                 {'type': 'master', 'timestamp': 1}], ['pve'], now=1000)
        with self.assertRaisesRegex(ValueError, 'quorate'):
            ha.validate_runtime([], ['pve'], now=1000)

    def test_ha_runtime_requires_recent_local_manager(self):
        status = [{'type': 'quorum', 'quorate': 1}, {'type': 'master', 'timestamp': 990}]
        with self.assertRaisesRegex(ValueError, 'Local HA manager'):
            ha.validate_runtime(status, ['pve'], now=1000)
        ha.validate_runtime(status + [{'type': 'lrm', 'node': 'pve', 'timestamp': 990}], ['pve'], now=1000)

    def execute(self, module, api):
        with patch.object(ha, 'AnsibleModule', return_value=module), patch.object(ha, 'ProxmoxAPI', return_value=api):
            with self.assertRaises(Exit) as result:
                ha.main()
        return result.exception.value

    def profiles(self):
        return {name: {'nodes': ['pve02:1', 'pve01:2'], 'strict': False,
                       'resources': ['vm:3011']} for name in ('one', 'two')}

    def test_union_keeps_foreign_members_and_refreshes_digest(self):
        api = API()
        result = self.execute(Module(self.profiles()), api)
        self.assertTrue(result['changed'])
        self.assertEqual(len(api.writes), 2)
        self.assertEqual(api.rules['one']['resources'], 'vm:3011,vm:9000')
        api.writes = []
        result = self.execute(Module(self.profiles()), api)
        self.assertFalse(result['changed'])
        self.assertEqual(api.writes, [])

    def test_unmanaged_profile_keeps_node_settings(self):
        api = API()
        profiles = self.profiles()
        profiles['one'].update(manage=False, nodes=[], strict=True)
        self.execute(Module({'one': profiles['one']}), api)
        self.assertEqual(api.rules['one']['nodes'], 'pve01:2,pve02:1')
        self.assertEqual(api.rules['one']['strict'], 0)

    def test_check_mode_no_writes(self):
        api = API()
        result = self.execute(Module(self.profiles(), check=True), api)
        self.assertTrue(result['changed'])
        self.assertEqual(api.writes, [])

    def test_empty_profiles_do_not_contact_api(self):
        with patch.object(ha, 'AnsibleModule', return_value=Module({})), patch.object(ha, 'ProxmoxAPI') as client:
            with self.assertRaises(Exit) as result:
                ha.main()
            self.assertFalse(result.exception.value['changed'])
            client.assert_not_called()


if __name__ == '__main__':
    unittest.main()
