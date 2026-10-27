import base64
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('metric_server', ROOT / 'plugins/modules/metric_server.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Finished(BaseException):
    def __init__(self, result):
        self.result = result


class Fake:
    def __init__(self, existing=None, check=False, **changes):
        self.check_mode = check
        self.current = existing
        self.writes = []
        self.params = dict(name='monitoring-otlp', state='present', server='receiver', port=443,
                           protocol='https', path='/v1/metrics', headers={'Authorization': 'secret'},
                           resource_attributes={'monitoring.cluster': 'cluster'}, disabled=False,
                           compression='gzip', timeout=5, allow_insecure_http=False) | changes

    def get_bin_path(self, *args, **kwargs):
        return '/usr/bin/pvesh'

    def run_command(self, command):
        if command[1] == 'get':
            if command[2].endswith('/server'):
                data = [{'id': 'monitoring-otlp'}] if self.current else []
            else:
                data = self.current
            return 0, json.dumps(data), ''
        self.writes.append(command)
        return 0, '', ''

    def exit_json(self, **result):
        raise Finished(result)

    def fail_json(self, **result):
        raise Finished(dict(failed=True, **result))


def run(fake):
    with patch.object(module, 'AnsibleModule', return_value=fake), patch.object(module.os.path, 'isfile', return_value=True):
        try:
            module.main()
        except Finished as done:
            return done.result


class MetricServerTests(unittest.TestCase):
    def test_pve_omitted_false_default_and_header_order_are_idempotent(self):
        current = {'type': 'opentelemetry', 'server': 'receiver', 'port': 443, 'otel-protocol': 'https',
                   'otel-path': '/v1/metrics', 'otel-verify-ssl': 1, 'otel-compression': 'gzip',
                   'otel-timeout': 5, 'otel-headers': module.encode({'Authorization': 'secret'}),
                   'otel-resource-attributes': module.encode({'monitoring.cluster': 'cluster'})}
        fake = Fake(current)
        result = run(fake)
        assert not result['changed'] and not fake.writes
        assert 'secret' not in str(result)


    def test_check_mode_and_other_plugin_collision_do_not_mutate(self):
        fake = Fake(check=True)
        assert run(fake)['changed'] and not fake.writes
        fake = Fake({'type': 'influxdb'}, state='absent')
        assert run(fake)['failed'] and not fake.writes


    def test_http_requires_explicit_test_opt_in(self):
        fake = Fake(protocol='http')
        assert run(fake)['failed'] and not fake.writes
