import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('config_filter', ROOT / 'plugins/filter/config.py')
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)


def inputs():
    return {
        'inventory_hostname': 'web01', 'ansible_host': '203.0.113.99',
        'proxmox_api': {'host': 'pve.invalid', 'user': 'svc@pve', 'token_id': 'svc@pve!deploy', 'token_secret': 'secret'},
        'proxmox_vm': {'name': 'web01.example.com', 'node': 'pve01', 'vmid': 3011,
                       'disks': [{'name': 'virtio0', 'size': 32}],
                       'networks': [{'name': 'net0', 'ip': '192.0.2.11', 'netmask': '255.255.255.0', 'vlanid': 30}]},
        'proxmox_guest': {'users': [{'name': 'admin', 'sudo_commands': 'NOPASSWD: ALL'}]},
    }


class ConfigTests(unittest.TestCase):
    def test_memory_hotplug_requires_numa(self):
        value = inputs()
        self.assertTrue(config.normalize(value)['vm']['hardware']['numa'])
        value['proxmox_vm']['hardware'] = {'numa': False, 'hotplug': 'memory,disk'}
        with self.assertRaisesRegex(Exception, 'Memory hotplug requires NUMA'):
            config.normalize(value)

    def test_legacy_default_vga_maps_to_supported_proxmox_value(self):
        value = inputs()
        value['proxmox_automatic_vga'] = 'default'
        self.assertEqual(config.normalize(value)['vm']['hardware']['vga'], 'std')

    def test_token_auth_does_not_pass_legacy_password_to_proxmoxer(self):
        value = inputs()
        value['proxmox_automatic_api_password'] = '<filleme>'
        self.assertEqual(config.normalize(value)['api']['password'], '')
        self.assertEqual(config.normalize_api(dict(value['proxmox_api'], password='legacy'))['password'], '')

    def test_public_inventory_not_mutated(self):
        value = inputs()
        before = copy.deepcopy(value)
        normalized = config.normalize(value)
        self.assertEqual(value, before)
        self.assertEqual(normalized['vm']['name'], 'web01.example.com')
        self.assertEqual(normalized['guest']['host'], '192.0.2.11')
        self.assertEqual(normalized['api']['token_id'], 'deploy')
        self.assertEqual(normalized['guest']['users'][0]['sudo_commands'], 'ALL')

    def test_legacy_layers_merge_users_by_name(self):
        value = inputs()
        del value['proxmox_guest']
        value.update(proxmox_automatic_users_defaults=[{'name': 'admin', 'shell': '/bin/bash', 'groups': ['wheel']}],
                     proxmox_automatic_users_host_vars=[{'name': 'admin', 'groups': ['sudo']}])
        users = config.normalize(value)['guest']['users']
        self.assertEqual(users, [{'name': 'admin', 'shell': '/bin/bash', 'groups': ['sudo']}])

    def test_absent_users_not_rendered_into_installer(self):
        value = inputs()
        value['proxmox_guest']['users'].append({'name': 'retired', 'state': 'absent'})
        self.assertEqual(len(config.normalize(value)['legacy']['users_merged']), 1)

    def test_vmid_fallback_requires_valid_range(self):
        value = inputs()
        del value['proxmox_vm']['vmid']
        self.assertEqual(config.normalize(value)['vm']['vmid'], 30011)
        value['proxmox_vm']['networks'][0]['vlanid'] = 0
        with self.assertRaisesRegex(Exception, 'VMID'):
            config.normalize(value)

    def test_firewall_requires_management_network(self):
        value = inputs()
        value['proxmox_firewall'] = {'pve_enabled': True}
        with self.assertRaisesRegex(Exception, 'management_sources'):
            config.normalize(value)

    def test_guest_firewall_rejects_injection_and_cross_family_rules(self):
        for rule in [{'name': 'bad', 'dport': '443; drop'},
                     {'name': 'bad', 'source': '+management'},
                     {'name': 'bad', 'source': '192.0.2.0/24', 'dest': '2001:db8::/64'}]:
            with self.subTest(rule=rule), self.assertRaises(Exception):
                config.rule_list([rule], guest=True)

    def test_conflicting_shared_profiles_fail_before_mutation(self):
        one = config.normalize(inputs())
        two = copy.deepcopy(one)
        one['ha'].update(enabled=True, name='shared', nodes='pve01:0,pve02:1')
        two['ha'].update(enabled=True, name='shared', nodes='pve01:1,pve02:0')
        two['vm'].update(vmid=3012, name='web02.example.com')
        with self.assertRaisesRegex(Exception, 'Conflicting shared HA'):
            config.cluster_plan([one, two], one['api']['host'])

    def test_vmid_collision_is_cluster_scoped(self):
        one = config.normalize(inputs())
        two = copy.deepcopy(one)
        with self.assertRaisesRegex(Exception, 'Duplicate VMID'):
            config.cluster_plan([one, two], one['api']['host'])
        two['api']['host'] = 'other.invalid'
        config.cluster_plan([one, two], one['api']['host'])

    def test_cluster_firewall_definitions_must_agree(self):
        one = config.normalize(inputs())
        two = copy.deepcopy(one)
        two['vm'].update(vmid=3012, name='web02.example.com')
        two['cluster_firewall']['options'] = {'policy_in': 'DROP'}
        with self.assertRaisesRegex(Exception, 'Conflicting central firewall'):
            config.cluster_plan([one, two], one['api']['host'])

    def test_unknown_public_keys_and_string_booleans_are_rejected(self):
        value = inputs()
        value['proxmox_vm']['memmory'] = 4096
        with self.assertRaisesRegex(Exception, 'Unsupported proxmox_vm'):
            config.normalize(value)
        value = inputs()
        value['proxmox_firewall'] = {'pve_enabled': 'false'}
        with self.assertRaisesRegex(Exception, 'YAML booleans'):
            config.normalize(value)

    def test_iso_names_and_paths_cannot_be_shell_source(self):
        value = inputs()
        value['proxmox_install'] = {'iso_dir': 'a/$(touch /tmp/unwanted)'}
        with self.assertRaisesRegex(Exception, 'metacharacters'):
            config.normalize(value)


if __name__ == '__main__':
    unittest.main()
