#!/usr/bin/python
"""Reconcile exactly one native PVE OTLP metric-server through pvesh."""
from __future__ import annotations
import base64
import json
import os
from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r"""
---
module: metric_server
short_description: Manage a native Proxmox OpenTelemetry metric server
version_added: 0.2.0
description:
  - Runs on a PVE 9 node with root privileges and uses the cluster API through pvesh.
  - Reconciles only the named entry, preserves other metric servers and supports check mode.
options:
  name:
    description: Cluster-wide metric server identifier.
    type: str
    required: true
  state:
    description: Desired entry state.
    type: str
    choices: [present, absent]
    default: present
  server:
    description: Receiver hostname.
    type: str
    default: ''
  port:
    description: Explicit OTLP HTTP port; avoids protocol-dependent PVE defaults.
    type: int
    default: 443
  protocol:
    description: Transport protocol.
    type: str
    choices: [https, http]
    default: https
  path:
    description: Full OTLP metrics path.
    type: str
    default: /v1/metrics
  headers:
    description: HTTP headers, encoded for PVE and never returned.
    type: dict
    default: {}
  resource_attributes:
    description: Additional resource attributes; use monitoring.cluster for unique cluster identity.
    type: dict
    default: {}
  disabled:
    description: Keep the entry configured but stop sending.
    type: bool
    default: false
  compression:
    description: HTTP compression.
    type: str
    choices: [gzip, none]
    default: gzip
  timeout:
    description: Send timeout in seconds.
    type: int
    default: 5
  allow_insecure_http:
    description: Explicit opt-in for isolated HTTP testing; HTTPS always verifies certificates.
    type: bool
    default: false
attributes:
  check_mode:
    support: full
author: Lenmail Maintainers
"""
EXAMPLES = r"""
- name: Configure once per PVE cluster
  degitag.proxmox.metric_server:
    name: monitoring-otlp
    server: metrics.example.invalid
    headers: "{{ vault_pve_otlp_headers }}"
    resource_attributes:
      monitoring.cluster: cluster-a
  become: true
"""
RETURN = r"""
changed_fields:
  description: Names of reconciled properties, without their values.
  returned: always
  type: list
  elements: str
"""


def encode(value):
    return base64.b64encode(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).decode()


def main():
    module = AnsibleModule(argument_spec={
        'name': {'type': 'str', 'required': True},
        'state': {'choices': ['present', 'absent'], 'default': 'present'},
        'server': {'default': ''}, 'port': {'type': 'int', 'default': 443},
        'protocol': {'choices': ['http', 'https'], 'default': 'https'},
        'path': {'default': '/v1/metrics'},
        'headers': {'type': 'dict', 'default': {}, 'no_log': True},
        'resource_attributes': {'type': 'dict', 'default': {}},
        'disabled': {'type': 'bool', 'default': False},
        'compression': {'choices': ['gzip', 'none'], 'default': 'gzip'},
        'timeout': {'type': 'int', 'default': 5},
        'allow_insecure_http': {'type': 'bool', 'default': False},
    }, supports_check_mode=True)
    v = module.params
    import re
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', v['name']):
        module.fail_json(msg='Invalid metric server identifier')
    if not os.path.isfile('/usr/share/perl5/PVE/Status/OpenTelemetry.pm'):
        module.fail_json(msg='PVE native OpenTelemetry plugin is required (PVE 9)')
    pvesh = module.get_bin_path('pvesh', required=True)

    def request(action, path, args=None):
        command = [pvesh, action, path] + (args or [])
        if action == 'get':
            command += ['--output-format', 'json']
        rc, out, _ = module.run_command(command)
        if rc:
            module.fail_json(msg='PVE metric-server API request failed; inspect PVE task logs (response suppressed to protect headers)')
        return json.loads(out) if action == 'get' else None

    root = '/cluster/metrics/server'
    entries = request('get', root)
    exists = any(e.get('id') == v['name'] for e in entries)
    path = root + '/' + v['name']
    current = request('get', path) if exists else {}
    if exists and current.get('type') != 'opentelemetry':
        module.fail_json(msg='Refusing to replace a different metric-server plugin')
    if v['state'] == 'absent':
        if exists and not module.check_mode:
            request('delete', path)
        module.exit_json(changed=exists, changed_fields=['state'] if exists else [])
    if not v['server'] or not 1 <= v['port'] <= 65535 or not 1 <= v['timeout'] <= 10:
        module.fail_json(msg='Server, valid port and timeout 1..10 are required')
    if v['protocol'] == 'http' and not v['allow_insecure_http']:
        module.fail_json(msg='HTTP requires an explicit isolated-test opt-in')
    desired = {
        'server': v['server'], 'port': v['port'], 'disable': int(v['disabled']),
        'otel-protocol': v['protocol'], 'otel-path': v['path'],
        'otel-verify-ssl': 1, 'otel-compression': v['compression'],
        'otel-timeout': v['timeout'], 'otel-headers': encode(v['headers']),
        'otel-resource-attributes': encode(v['resource_attributes']),
    }
    def equal(key, value):
        old = current.get(key, {'disable': 0}.get(key))
        if key in ['otel-headers', 'otel-resource-attributes'] and old:
            try:
                return json.loads(base64.b64decode(old)) == json.loads(base64.b64decode(value))
            except (ValueError, TypeError):
                return False
        return str(old) == str(value)
    changes = [k for k, value in desired.items() if not equal(k, value)]
    if changes and not module.check_mode:
        args = []
        for key, value in desired.items():
            args += ['--' + key, str(value)]
        if not exists:
            args += ['--type', 'opentelemetry']
        elif current.get('digest'):
            args += ['--digest', current['digest']]
        request('set' if exists else 'create', path, args)
    module.exit_json(changed=bool(changes), changed_fields=changes)


if __name__ == '__main__':
    main()
