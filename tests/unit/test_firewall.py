import importlib.util
from pathlib import Path
import unittest
from copy import deepcopy

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('firewall_utils', ROOT / 'plugins/module_utils/firewall.py')
fw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fw)


class FakeAPI:
    """Model Proxmox prepend + moveto API semantics, including digest requirements."""
    def __init__(self, rules):
        self.rules = deepcopy(rules)
        self.writes = []
        self.reindex()

    def reindex(self):
        for index, rule in enumerate(self.rules):
            rule.update(pos=index, digest='digest')

    def get(self, path):
        if path.rsplit('/', 1)[-1].isdigit():
            return deepcopy(self.rules[int(path.rsplit('/', 1)[-1])])
        return deepcopy(self.rules)

    def request(self, method, path, data):
        self.writes.append((method, path, data))
        if method == 'POST':
            self.rules.insert(0, deepcopy(data))
        elif method == 'DELETE':
            assert data['digest'] == 'digest'
            del self.rules[int(path.rsplit('/', 1)[-1])]
        elif method == 'PUT':
            assert data['digest'] == 'digest'
            old = int(path.rsplit('/', 1)[-1])
            if 'moveto' in data:
                target = data['moveto']
                entry = self.rules.pop(old)
                self.rules.insert(target - 1 if target > old else target, entry)
            else:
                self.rules[old].update({k: v for k, v in data.items() if k not in ('digest', 'delete')})
                for key in data.get('delete', '').split(','):
                    self.rules[old].pop(key, None)
        self.reindex()


class FirewallTests(unittest.TestCase):
    def test_foreign_rules_preserved_and_second_run_unchanged(self):
        foreign = {'type': 'in', 'action': 'DROP', 'source': '203.0.113.0/24', 'enable': 1, 'comment': 'operator rule'}
        api = FakeAPI([foreign])
        rules = [{'name': 'https', 'proto': 'tcp', 'dport': '443'}, {'name': 'management', 'type': 'group', 'action': 'management'}]
        self.assertTrue(fw.reconcile_rules(api, '/rules', rules, 'test'))
        self.assertEqual(fw.clean(api.rules[0]), fw.clean(foreign))
        self.assertEqual([r['comment'] for r in api.rules[1:]], ['test:https', 'test:management'])
        api.writes = []
        self.assertFalse(fw.reconcile_rules(api, '/rules', rules, 'test'))
        self.assertEqual(api.writes, [])

    def test_reorder_update_and_remove_owned_rule(self):
        old = fw.prepare_rules([{'name': 'one', 'dport': '80'}, {'name': 'retired'}], 'test')
        api = FakeAPI(old)
        wanted = [{'name': 'two', 'proto': 'tcp', 'dport': '443'}, {'name': 'one', 'proto': 'tcp', 'dport': '8080'},
                  {'name': 'retired', 'state': 'absent'}]
        self.assertTrue(fw.reconcile_rules(api, '/rules', wanted, 'test'))
        self.assertEqual([r['comment'] for r in api.rules], ['test:two', 'test:one'])
        self.assertEqual(api.rules[1]['dport'], '8080')

    def test_check_mode_predicts_without_writes(self):
        api = FakeAPI([])
        self.assertTrue(fw.reconcile_rules(api, '/rules', [{'name': 'ssh'}], 'test', check_mode=True))
        self.assertEqual(api.writes, [])

    def test_empty_list_removes_only_our_rules(self):
        api = FakeAPI([{'comment': 'someone-else:x', 'type': 'in', 'action': 'DROP'},
                       {'comment': 'test:x', 'type': 'in', 'action': 'ACCEPT'}])
        fw.reconcile_rules(api, '/rules', [], 'test')
        self.assertEqual(len(api.rules), 1)
        self.assertEqual(api.rules[0]['comment'], 'someone-else:x')

    def test_update_keeps_rule_present_and_clears_removed_optional_fields(self):
        api = FakeAPI(fw.prepare_rules([{'name': 'https', 'proto': 'tcp', 'dport': '443', 'source': '192.0.2.0/24'}], 'test'))
        fw.reconcile_rules(api, '/rules', [{'name': 'https', 'proto': 'tcp', 'dport': '8443'}], 'test')
        self.assertNotIn('source', api.rules[0])
        self.assertEqual(api.rules[0]['dport'], '8443')
        self.assertFalse(any(method == 'DELETE' for method, _, _ in api.writes))

    def test_duplicate_rule_names_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unique'):
            fw.prepare_rules([{'name': 'ssh'}, {'name': 'ssh'}], 'test')


if __name__ == '__main__':
    unittest.main()
