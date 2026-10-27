import copy
import importlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.collections'))
firewall = importlib.import_module('ansible_collections.degitag.proxmox.plugins.modules.firewall')
lifecycle = importlib.import_module('ansible_collections.degitag.proxmox.plugins.modules.vm_lifecycle')
api_module = importlib.import_module('ansible_collections.degitag.proxmox.plugins.module_utils.api')


class Exit(BaseException):
    def __init__(self, value):
        self.value = value


class FakeModule:
    check_mode = False

    def __init__(self, operation='inspect', check=False):
        self.check_mode = check
        self.params = {'api': {}, 'vmid': 3011, 'name': 'web.example.com', 'node': 'pve01',
                       'operation': operation, 'boot_disk': 'virtio0', 'detach': True, 'reinstall': False,
                       'media': {'ide2': 'local:iso/install.iso,media=cdrom'}}

    def exit_json(self, **kwargs):
        raise Exit(kwargs)

    def fail_json(self, **kwargs):
        raise Exit(dict(kwargs, failed=True))


class VMAPI:
    def __init__(self):
        self.resources = [{'vmid': 3011, 'name': 'web.example.com', 'node': 'pve02', 'type': 'qemu', 'status': 'stopped'}]
        self.config = {'digest': 'digest', 'description': 'operator notes\nlenmail.proxmox:installing',
                       'boot': 'order=ide2;virtio0', 'ide2': 'local:iso/install.iso,media=cdrom',
                       'ide3': 'local:iso/foreign.iso,media=cdrom',
                       'net0': 'virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0,tag=30,mtu=1500'}
        self.writes = []

    def get(self, path):
        if path.endswith('/status/current'):
            return {'status': self.resources[0]['status']}
        return copy.deepcopy(self.resources if path.startswith('/cluster/resources') else self.config)

    def request(self, method, path, data):
        self.writes.append((method, path, data))


class ModuleTests(unittest.TestCase):
    def run_lifecycle(self, module, api):
        with patch.object(lifecycle, 'AnsibleModule', return_value=module), patch.object(lifecycle, 'ProxmoxAPI', return_value=api):
            with self.assertRaises(Exit) as result:
                lifecycle.main()
        return result.exception.value

    def test_identity_collision_does_not_mutate(self):
        api = VMAPI()
        api.resources[0]['name'] = 'someone-else'
        result = self.run_lifecycle(FakeModule('prepare'), api)
        self.assertTrue(result['failed'])
        self.assertEqual(api.writes, [])

    def test_reinstall_guard_uses_fresh_status_instead_of_cluster_cache(self):
        class StaleClusterAPI(VMAPI):
            def get(self, path):
                if path.endswith('/status/current'):
                    return {'status': 'running'}
                return super().get(path)
        api = StaleClusterAPI()
        module = FakeModule('prepare')
        module.params['reinstall'] = True
        result = self.run_lifecycle(module, api)
        self.assertTrue(result['failed'])
        self.assertEqual(api.writes, [])

    def test_complete_preserves_notes_foreign_media_and_disks(self):
        api = VMAPI()
        result = self.run_lifecycle(FakeModule('complete'), api)
        self.assertTrue(result['changed'])
        data = api.writes[0][2]
        self.assertEqual(data['delete'], 'ide2')
        self.assertEqual(data['description'], 'operator notes\nlenmail.proxmox:ready')
        self.assertEqual(data['boot'], 'order=virtio0')
        self.assertNotIn('virtio0', data)
        self.assertNotIn('ide3', data)
        self.assertIn('/nodes/pve02/', api.writes[0][1])

    def test_media_resume_and_detach_accept_proxmox_derived_size(self):
        api = VMAPI()
        api.resources[0]['status'] = 'running'
        api.config['ide2'] += ',size=790626304'
        result = self.run_lifecycle(FakeModule('prepare'), api)
        self.assertFalse(result.get('failed', False))
        self.assertNotIn('ide2', api.writes[0][2])
        api.writes.clear()
        self.run_lifecycle(FakeModule('complete'), api)
        self.assertEqual(api.writes[0][2]['delete'], 'ide2')

    def test_media_match_requires_same_volume(self):
        self.assertFalse(lifecycle.media_matches('local:iso/foreign.iso,media=cdrom,size=100K',
                                               'local:iso/install.iso,media=cdrom'))

    def test_existing_vm_without_our_marker_not_adopted(self):
        api = VMAPI()
        api.config['description'] = 'operator notes'
        result = self.run_lifecycle(FakeModule('complete'), api)
        self.assertFalse(result['changed'])
        self.assertEqual(api.writes, [])

    def test_nic_firewall_preserves_mac_and_vlan(self):
        api = VMAPI()
        self.run_lifecycle(FakeModule('nic_firewall'), api)
        value = api.writes[0][2]['net0']
        self.assertEqual(value, api.config['net0'] + ',firewall=1')

    def test_nic_firewall_canonical_option_order_is_idempotent(self):
        api = VMAPI()
        api.config['net0'] = 'virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0,firewall=1,tag=30'
        result = self.run_lifecycle(FakeModule('nic_firewall'), api)
        self.assertFalse(result['changed'])
        self.assertEqual(api.writes, [])

    def test_check_mode_lifecycle_has_no_writes(self):
        api = VMAPI()
        result = self.run_lifecycle(FakeModule('complete', check=True), api)
        self.assertTrue(result['changed'])
        self.assertEqual(api.writes, [])

    def test_running_foreign_install_requires_stop(self):
        api = VMAPI()
        api.resources[0]['status'] = 'running'
        api.config['description'] = ''
        result = self.run_lifecycle(FakeModule('prepare'), api)
        self.assertTrue(result['failed'])
        self.assertEqual(api.writes, [])

    def test_pending_stopped_resume_prefers_system_disk(self):
        api = VMAPI()
        self.run_lifecycle(FakeModule('prepare'), api)
        self.assertEqual(api.writes[0][2]['boot'], 'order=virtio0;ide2')

    def test_explicit_reinstall_requires_stop_even_with_pending_marker(self):
        api = VMAPI()
        api.resources[0]['status'] = 'running'
        module = FakeModule('prepare')
        module.params['reinstall'] = True
        result = self.run_lifecycle(module, api)
        self.assertTrue(result['failed'])
        self.assertEqual(api.writes, [])

    def test_foreign_security_group_is_not_adopted(self):
        class GroupAPI:
            def get(self, path):
                return [{'group': 'web', 'comment': 'operator'}]
        with self.assertRaisesRegex(ValueError, 'foreign'):
            firewall.reconcile_named(GroupAPI(), '/groups', [{'name': 'web'}], 'lenmail.proxmox', key='group')

    def test_ipset_host_prefix_is_idempotent_against_proxmox_readback(self):
        class IPSetAPI:
            def get(self, path):
                if path.endswith('/ipset'):
                    return [{'name': 'clients', 'comment': 'lenmail.proxmox'}]
                return [{'cidr': '192.0.2.10'}, {'cidr': '2001:db8::10'}]

            def request(self, *args):
                raise AssertionError('Equivalent host CIDRs must not cause writes')
        self.assertFalse(firewall.reconcile_named(IPSetAPI(), '/ipset',
                         [{'name': 'clients', 'cidrs': [{'cidr': '192.0.2.10/32'}, {'cidr': '2001:db8::10/128'}]}],
                         'lenmail.proxmox'))

    def test_new_security_group_check_mode_does_not_query_missing_rules(self):
        class GroupAPI:
            def get(self, path):
                self_path = path
                if self_path != '/groups':
                    raise AssertionError('Must not read missing group rules during check mode')
                return []
        self.assertTrue(firewall.reconcile_named(GroupAPI(), '/groups', [{'name': 'web', 'rules': []}],
                                                'lenmail.proxmox', key='group', check_mode=True))

    def test_password_auth_uses_cookie_and_csrf(self):
        with patch.object(api_module.requests, 'Session') as session:
            response = session.return_value.request.return_value
            response.ok = True
            response.json.return_value = {'data': {'ticket': 'ticket', 'CSRFPreventionToken': 'csrf'}}
            session.return_value.headers = {}
            api = api_module.ProxmoxAPI({'host': 'pve.invalid', 'user': 'svc@pam', 'password': 'secret',
                                        'validate_certs': True, 'timeout': 5})
            session.return_value.cookies.set.assert_called_once_with('PVEAuthCookie', 'ticket')
            self.assertEqual(api.session.headers['CSRFPreventionToken'], 'csrf')
            self.assertNotIn('Authorization', api.session.headers)

    def test_delete_sends_digest_as_query_without_request_body(self):
        with patch.object(api_module.requests, 'Session') as session:
            response = session.return_value.request.return_value
            response.ok = True
            response.json.return_value = {'data': None}
            api = api_module.ProxmoxAPI({'host': 'pve.invalid', 'user': 'svc@pam',
                                        'token_id': 'test', 'token_secret': 'test',
                                        'validate_certs': True, 'timeout': 5})
            api.request('DELETE', '/cluster/firewall/groups/test/0', {'digest': 'version'})
            kwargs = session.return_value.request.call_args.kwargs
            self.assertEqual(kwargs['params'], {'digest': 'version'})
            self.assertNotIn('data', kwargs)


if __name__ == '__main__':
    unittest.main()
