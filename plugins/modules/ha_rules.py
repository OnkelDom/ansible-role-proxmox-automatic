#!/usr/bin/python
"""Reconcile shared node affinity while retaining existing resource members."""
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.degitag.proxmox.plugins.module_utils.api import AUTH_SPEC, ProxmoxAPI, segment
import time

DOCUMENTATION = r'''
---
module: ha_rules
short_description: Reconcile shared Proxmox HA node affinity rules without removing existing members
description:
  - Reads existing resources and unions them with requested members.
author: Lenmail Maintainers
options:
  api:
    type: dict
    required: true
    description: Proxmox API parameters.
  profiles:
    type: dict
    required: true
    description: Rule names mapped to nodes, strict and resources.
  validate_only:
    type: bool
    default: false
    description: Check current quorum and HA heartbeats without changing rules.
  runtime_nodes:
    type: list
    elements: str
    default: []
    description: Nodes whose local HA managers must have a recent heartbeat.
'''
EXAMPLES = r'''
- name: Reconcile shared HA rules
  degitag.proxmox.ha_rules:
    api: "{{ proxmox_api }}"
    profiles:
      prefer-pve01:
        nodes: ['pve01:2', 'pve02:1']
        strict: false
        resources: ['vm:3011']
'''
RETURN = r'''
changed:
  description: Whether shared profiles changed.
  type: bool
  returned: always
'''


def validate_runtime(status, nodes, now=None):
    now = time.time() if now is None else now
    def recent(item):
        return -60 <= now - item.get('timestamp', 0) <= 120
    if not any(item.get('type') == 'quorum' and item.get('quorate') for item in status):
        raise ValueError('HA requires a quorate cluster')
    if not any(item.get('type') == 'master' and recent(item) for item in status):
        raise ValueError('HA manager is inactive or stale; repair HA separately or set proxmox_ha.enabled=false')
    for node in nodes:
        if not any(item.get('type') == 'lrm' and item.get('node') == node and recent(item) for item in status):
            raise ValueError('Local HA manager is inactive or stale on ' + node)


def main():
    module = AnsibleModule(argument_spec=dict(AUTH_SPEC, profiles={'type': 'dict', 'required': True},
                           validate_only={'type': 'bool', 'default': False},
                           runtime_nodes={'type': 'list', 'elements': 'str', 'default': []}), supports_check_mode=True)
    try:
        if not module.params['profiles']:
            module.exit_json(changed=False)
        api = ProxmoxAPI(module.params['api'])
        if module.params.get('validate_only', False):
            validate_runtime(api.get('/cluster/ha/status/current'), module.params.get('runtime_nodes', []))
            module.exit_json(changed=False)
        path = '/cluster/ha/rules'
        existing = {r['rule']: r for r in api.get(path)}
        changed = False
        for name, profile in module.params['profiles'].items():
            old = api.get(path + '/' + segment(name)) if name in existing else {}
            if old and old.get('type') != 'node-affinity':
                raise ValueError('Existing HA rule has a different type: ' + name)
            if not profile.get('manage', True) and not old:
                raise ValueError('Referenced unmanaged HA rule does not exist: ' + name)
            resources = sorted((set(old.get('resources', '').split(',')) | set(profile['resources'])) - {''})
            wanted = {'type': 'node-affinity', 'nodes': ','.join(sorted(profile['nodes'])),
                      'strict': int(profile['strict']), 'resources': ','.join(resources)}
            if profile.get('comment') is not None:
                wanted['comment'] = profile['comment']
            if not profile.get('manage', True):
                wanted = {'resources': ','.join(resources)}
            if any(str(old.get(k, '')) != str(v) for k, v in wanted.items()):
                changed = True
                if not module.check_mode:
                    if old:
                        wanted['digest'] = old['digest']
                        api.request('PUT', path + '/' + segment(name), wanted)
                    else:
                        api.request('POST', path, dict(wanted, rule=name))
        module.exit_json(changed=changed)
    except (RuntimeError, ValueError) as exc:
        module.fail_json(msg=str(exc))
    except Exception:
        module.fail_json(msg='HA reconciliation failed; check API version and permissions')


if __name__ == '__main__':
    main()
