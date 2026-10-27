#!/usr/bin/python
"""Read VM identity and make bounded installer lifecycle transitions."""
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.degitag.proxmox.plugins.module_utils.api import AUTH_SPEC, ProxmoxAPI, segment

DOCUMENTATION = r'''
---
module: vm_lifecycle
short_description: Inspect VM identity and manage installer boot and completion markers
description:
  - Does not create or replace disks.
  - Completion removes only explicitly supplied installer drives.
author: Lenmail Maintainers
options:
  api:
    type: dict
    required: true
    description: Proxmox API parameters.
  vmid:
    type: int
    required: true
    description: VM ID.
  name:
    type: str
    required: true
    description: Expected VM name.
  node:
    type: str
    required: true
    description: Expected node for creation.
  operation:
    type: str
    choices: [inspect, validate_media, prepare, complete, disk_boot, nic_firewall]
    default: inspect
    description: Lifecycle operation.
  media:
    type: dict
    default: {}
    description: Expected installer CD-ROM drives.
  boot_disk:
    type: str
    default: virtio0
    description: Installed system boot disk.
  reinstall:
    type: bool
    default: false
    description: Explicitly prefer the installer over an existing system disk.
  detach:
    type: bool
    default: true
    description: Detach owned installer media at completion.
'''
EXAMPLES = r'''
- name: Inspect VM
  degitag.proxmox.vm_lifecycle:
    api: "{{ proxmox_api }}"
    vmid: 3011
    name: server.example.com
    node: pve01
'''
RETURN = r'''
exists:
  type: bool
  returned: always
  description: Whether the VM exists.
installing:
  type: bool
  returned: when VM exists
  description: Whether the VM carries our pending installation marker.
'''
MARKER = 'lenmail.proxmox:installing'
READY = 'lenmail.proxmox:ready'


def media_matches(current, desired):
    # Proxmox appends derived fields such as size to a configured CD-ROM.
    actual = str(current or '').split(',')
    wanted = str(desired).split(',')
    return actual[0] == wanted[0] and set(wanted[1:]).issubset(actual[1:])


def main():
    spec = dict(AUTH_SPEC, vmid={'type': 'int', 'required': True}, name={'type': 'str', 'required': True},
                node={'type': 'str', 'required': True}, operation={'type': 'str', 'default': 'inspect',
                'choices': ['inspect', 'validate_media', 'prepare', 'complete', 'disk_boot', 'nic_firewall']}, media={'type': 'dict', 'default': {}},
                boot_disk={'type': 'str', 'default': 'virtio0'}, detach={'type': 'bool', 'default': True}, reinstall={'type': 'bool', 'default': False})
    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)
    p = module.params
    try:
        api = ProxmoxAPI(p['api'])
        if p['operation'] == 'validate_media':
            for media in p['media'].values():
                volume = media.split(',')[0]
                storage = volume.split(':', 1)[0]
                volumes = api.get('/nodes/' + segment(p['node']) + '/storage/' + segment(storage) + '/content')
                if not any(v['volid'] == volume for v in volumes):
                    module.fail_json(msg='Required installer volume is missing: ' + volume)
            module.exit_json(changed=False)
        vm = next((v for v in api.get('/cluster/resources?type=vm') if v.get('vmid') == p['vmid']), None)
        if vm is None:
            module.exit_json(changed=False, exists=False, installing=False)
        if vm.get('type') != 'qemu' or vm.get('name') != p['name']:
            module.fail_json(msg='VMID belongs to another VM or container; refusing adoption')
        path = '/nodes/' + segment(vm['node']) + '/qemu/' + str(p['vmid']) + '/config'
        current = api.get(path)
        # Cluster resources can lag behind a just-started or stopped QEMU process.
        vm['status'] = api.get('/nodes/' + segment(vm['node']) + '/qemu/' + str(p['vmid']) + '/status/current')['status']
        if current.get('template'):
            module.fail_json(msg='VMID belongs to a template')
        description = current.get('description', '')
        installing = MARKER in description.splitlines()
        ready = READY in description.splitlines()
        changes = {}
        operation = p['operation']
        if operation == 'prepare':
            if vm.get('status') != 'stopped' and (p['reinstall'] or not installing):
                module.fail_json(msg='Reinstallation requires an explicitly stopped VM')
            if vm.get('status') != 'stopped' and any(not media_matches(current.get(k), v) for k, v in p['media'].items()):
                module.fail_json(msg='Running installer media differs; stop the VM before resuming with changed media')
            changes.update({k: v for k, v in p['media'].items() if not media_matches(current.get(k), v)})
            changes['boot'] = ('order=ide2;' + p['boot_disk']) if p['reinstall'] else ('order=' + p['boot_disk'] + ';ide2')
            lines = [line for line in description.splitlines() if line not in (MARKER, READY)]
            changes['description'] = '\n'.join(lines + [MARKER])
        elif operation == 'disk_boot':
            changes['boot'] = 'order=' + p['boot_disk'] + ';ide2'
        elif operation == 'complete':
            if installing or ready:
                changes['boot'] = 'order=' + p['boot_disk']
                lines = [line for line in description.splitlines() if line not in (MARKER, READY)]
                changes['description'] = '\n'.join(lines + [READY])
                if p['detach']:
                    delete = [drive for drive, value in p['media'].items() if media_matches(current.get(drive), value)]
                    if delete:
                        changes['delete'] = ','.join(delete)
        elif operation == 'nic_firewall':
            for key, value in current.items():
                if key.startswith('net') and key[3:].isdigit():
                    if 'firewall=1' in value.split(','):
                        continue
                    parts = [part for part in value.split(',') if not part.startswith('firewall=')]
                    changes[key] = ','.join(parts + ['firewall=1'])
        changes = {k: v for k, v in changes.items() if str(current.get(k, '')) != str(v)}
        if changes and not module.check_mode:
            changes['digest'] = current['digest']
            api.request('PUT', path, changes)
        module.exit_json(changed=bool(changes), exists=True, installing=installing, ready=ready,
                         node=vm['node'], status=vm['status'])
    except RuntimeError as exc:
        module.fail_json(msg=str(exc))
    except Exception:
        module.fail_json(msg='VM lifecycle inspection or transition failed')


if __name__ == '__main__':
    main()
