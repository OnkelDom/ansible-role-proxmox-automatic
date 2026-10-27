#!/usr/bin/python
"""Manage centrally owned firewall groups, addresses and rules."""
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.degitag.proxmox.plugins.module_utils.api import AUTH_SPEC, ProxmoxAPI, segment
from ansible_collections.degitag.proxmox.plugins.module_utils.firewall import FirewallJournal, prepare_rules, reconcile_rules
import ipaddress

DOCUMENTATION = r'''
---
module: firewall
short_description: Manage owned Proxmox security groups and cluster or VM firewall rules
description:
  - Preserves foreign rules and uses stable names in ownership comments.
  - Never changes node firewall settings.
author: Lenmail Maintainers
options:
  api:
    type: dict
    required: true
    description: Proxmox API connection parameters.
  config:
    type: dict
    required: true
    description: Groups, aliases, IP sets, rules and explicitly requested options.
  vmid:
    type: int
    description: VM ID. Omit to manage central cluster objects.
  node:
    type: str
    description: VM node.
  owner:
    type: str
    default: lenmail.proxmox
    description: Stable ownership marker.
  backup_dir:
    type: path
    default: .proxmox-firewall-backups
    description: Controller directory for restricted pre-change API journals.
'''
EXAMPLES = r'''
- name: Define shared policies
  degitag.proxmox.firewall:
    api: "{{ proxmox_api }}"
    config:
      groups:
        - name: management
          rules:
            - name: ssh
              source: +management
              proto: tcp
              dport: '22'
'''
RETURN = r'''
changed:
  description: Whether owned firewall configuration differs.
  type: bool
  returned: always
'''



def assert_unreferenced(api, kind, name):
    paths = ['/cluster/firewall/rules']
    for group in api.get('/cluster/firewall/groups'):
        if kind != 'group' or group['group'] != name:
            paths.append('/cluster/firewall/groups/' + segment(group['group']))
    for node in api.get('/nodes'):
        paths.append('/nodes/' + segment(node['node']) + '/firewall/rules')
    for vm in api.get('/cluster/resources?type=vm'):
        if vm.get('type') in ('qemu', 'lxc'):
            paths.append('/nodes/' + segment(vm['node']) + '/' + vm['type'] + '/' + str(vm['vmid']) + '/firewall/rules')
    identifiers = {name, 'dc/' + name}
    if kind == 'ipset':
        identifiers = {'+' + value for value in identifiers}
    for path in paths:
        for rule in api.get(path):
            if kind == 'group':
                referenced = rule.get('type') == 'group' and rule.get('action') == name
            else:
                addresses = {token.strip(' !') for key in ('source', 'dest') for token in str(rule.get(key, '')).split(',')}
                referenced = bool(addresses & identifiers)
            if referenced:
                raise ValueError('Firewall object is still referenced at ' + path + ': ' + name)

def canonical_cidr(value):
    try:
        network = ipaddress.ip_network(value, strict=False)
        return str(network.network_address) if network.prefixlen == network.max_prefixlen else str(network)
    except ValueError:
        return value


def reconcile_named(api, path, items, owner, key='name', check_mode=False):
    changed = False
    for item in items:
        existing = {v[key]: v for v in api.get(path)}
        name = item['name']
        current = existing.get(name)
        if current and current.get('comment', '').split(' ', 1)[0] != owner:
            raise ValueError(f'Refusing to adopt foreign firewall object {name}')
        if item.get('state', 'present') == 'absent':
            if current:
                assert_unreferenced(api, 'group' if key == 'group' else ('ipset' if path.endswith('/ipset') else 'alias'), name)
                if path.endswith('/ipset'):
                    api.get(path + '/' + segment(name))  # Snapshot membership before an explicit force-delete.
                changed = True
                if key == 'group':
                    changed |= reconcile_rules(api, path + '/' + segment(name), [], owner, check_mode)
                    if any(not r.get('comment', '').startswith(owner + ':') for r in api.get(path + '/' + segment(name))):
                        raise ValueError('Refusing to delete a group containing foreign rules: ' + name)
                if not check_mode:
                    api.request('DELETE', path + '/' + segment(name), {'force': 1} if path.endswith('/ipset') else None)
            continue
        value = {k: v for k, v in item.items() if k not in ('state', 'rules', 'cidrs', 'name')}
        value[key] = name
        value['comment'] = owner + (' ' + item['comment'] if item.get('comment') else '')
        if 'cidr' in value:
            value['cidr'] = canonical_cidr(value['cidr'])
        if not current or any(str(current.get(k, '')) != str(v) for k, v in value.items()):
            changed = True
            if not check_mode:
                if current:
                    if key == 'group':
                        api.request('POST', path, dict(value, rename=name, digest=current['digest']))
                    else:
                        api.request('PUT', path + '/' + segment(name), dict(value, digest=current['digest']))
                else:
                    api.request('POST', path, value)
        if key == 'group':
            if not current and check_mode:
                changed = True
            else:
                changed |= reconcile_rules(api, path + '/' + segment(name), item.get('rules', []), owner, check_mode)
        if 'cidrs' in item:
            if not current and check_mode:
                continue
            entry_path = path + '/' + segment(name)
            members = {v['cidr']: v for v in api.get(entry_path)}
            desired = {canonical_cidr(v['cidr']): dict(v, cidr=canonical_cidr(v['cidr'])) for v in item['cidrs']}
            for cidr in set(members) - set(desired):
                changed = True
                if not check_mode:
                    api.request('DELETE', entry_path + '/' + segment(cidr))
            for cidr, member in desired.items():
                value = dict(member, nomatch=int(member.get('nomatch', False)))
                if cidr not in members or any(str(members[cidr].get(k, 0 if k == 'nomatch' else '')) != str(v) for k, v in value.items()):
                    changed = True
                    if not check_mode:
                        api.request('PUT' if cidr in members else 'POST',
                                    entry_path + ('/' + segment(cidr) if cidr in members else ''), value)
    return changed


def manage(api, config, owner, check_mode=False, node=None, vmid=None):
    # Validate the complete desired payload before the first mutation.
    if set(config) - {'groups', 'aliases', 'ipsets', 'rules', 'options'}:
        raise ValueError('Unknown firewall configuration key')
    prepare_rules(config.get('rules', []), owner)
    for group in config.get('groups', []):
        prepare_rules(group.get('rules', []), owner)
    if set(config.get('options', {})) - {'enable', 'policy_in', 'policy_out'}:
        raise ValueError('Unsupported firewall option')
    base = '/cluster/firewall' if vmid is None else '/nodes/' + segment(node) + '/qemu/' + str(vmid) + '/firewall'
    changed = False
    if vmid is None:
        # References are created before the rules that use them.
        changed |= reconcile_named(api, base + '/aliases', config.get('aliases', []), owner, check_mode=check_mode)
        changed |= reconcile_named(api, base + '/ipset', config.get('ipsets', []), owner, check_mode=check_mode)
        changed |= reconcile_named(api, base + '/groups', config.get('groups', []), owner, key='group', check_mode=check_mode)
    if 'rules' in config:
        changed |= reconcile_rules(api, base + '/rules', config['rules'], owner, check_mode)
    options = config.get('options', {})
    allowed = {'enable', 'policy_in', 'policy_out'}
    if set(options) - allowed:
        raise ValueError('Only enable, policy_in and policy_out may be explicitly managed')
    if options:
        current = api.get(base + '/options')
        if any(str(current.get(k, '')) != str(int(v) if isinstance(v, bool) else v) for k, v in options.items()):
            changed = True
            if not check_mode:
                data = {k: int(v) if isinstance(v, bool) else v for k, v in options.items()}
                data['digest'] = current['digest']
                api.request('PUT', base + '/options', data)
    return changed


def main():
    module = AnsibleModule(argument_spec=dict(AUTH_SPEC, config={'type': 'dict', 'required': True},
                           node={'type': 'str'}, vmid={'type': 'int'},
                           owner={'type': 'str', 'default': 'lenmail.proxmox'},
                           backup_dir={'type': 'path', 'default': '.proxmox-firewall-backups'}), supports_check_mode=True)
    p = module.params
    try:
        journal = FirewallJournal(ProxmoxAPI(p['api']), p['backup_dir'])
        changed = manage(journal, p['config'], p['owner'], module.check_mode, p['node'], p['vmid'])
        module.exit_json(changed=changed, backup_file=journal.path)
    except (ValueError, RuntimeError) as exc:
        module.fail_json(msg=str(exc), backup_file=journal.path if 'journal' in locals() else None)
    except Exception:
        module.fail_json(msg='Firewall reconciliation failed; inspect the journal and API permissions',
                         backup_file=journal.path if 'journal' in locals() else None)


if __name__ == '__main__':
    main()
