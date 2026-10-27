#!/usr/bin/python
"""Content-addressed media upload with task completion and check mode."""
import hashlib
import os
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.degitag.proxmox.plugins.module_utils.api import AUTH_SPEC, ProxmoxAPI, segment

DOCUMENTATION = r'''
---
module: iso_upload
short_description: Upload content-addressed installer media and wait for completion
description:
  - Names must contain a full SHA256 fingerprint to permit safe reuse.
author: Lenmail Maintainers
options:
  api:
    type: dict
    required: true
    description: Proxmox API connection parameters.
  node:
    type: str
    required: true
    description: Target node.
  storage:
    type: str
    required: true
    description: ISO storage.
  path:
    type: path
    required: true
    description: Local ISO path.
  name:
    type: str
    required: true
    description: Remote content-addressed ISO filename.
  timeout:
    type: int
    default: 600
    description: Upload task completion timeout.
'''
EXAMPLES = r'''
- name: Upload installer
  degitag.proxmox.iso_upload:
    api: "{{ proxmox_api }}"
    node: pve01
    storage: local
    path: /srv/iso/installer.iso
    name: "installer-{{ checksum }}.iso"
'''
RETURN = r'''
volid:
  description: Uploaded or reused volume ID.
  type: str
  returned: always
'''


def main():
    spec = dict(AUTH_SPEC, node={'type': 'str', 'required': True},
                storage={'type': 'str', 'required': True}, path={'type': 'path', 'required': True},
                name={'type': 'str', 'required': True}, timeout={'type': 'int', 'default': 600})
    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)
    p = module.params
    try:
        if not os.path.isfile(p['path']):
            module.fail_json(msg='Local ISO does not exist')
        with open(p['path'], 'rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest not in p['name']:
            module.fail_json(msg='ISO filename must include its full SHA256 checksum')
        api = ProxmoxAPI(p['api'])
        base = '/nodes/' + segment(p['node']) + '/storage/' + segment(p['storage'])
        volid = p['storage'] + ':iso/' + p['name']
        found = next((v for v in api.get(base + '/content') if v['volid'] == volid), None)
        if found:
            if int(found.get('size', -1)) != os.path.getsize(p['path']):
                module.fail_json(msg='Fingerprint filename exists with unexpected size; refusing overwrite')
            module.exit_json(changed=False, volid=volid)
        if module.check_mode:
            module.exit_json(changed=True, volid=volid)
        with open(p['path'], 'rb') as media:
            upid = api.request('POST', base + '/upload', {'content': 'iso'},
                               {'filename': (p['name'], media, 'application/octet-stream')})
        if upid:
            api.wait(p['node'], upid, p['timeout'])
        module.exit_json(changed=True, volid=volid)
    except (RuntimeError, OSError, ValueError) as exc:
        module.fail_json(msg=str(exc))
    except Exception:
        module.fail_json(msg='ISO upload failed; check API connectivity and permissions')


if __name__ == '__main__':
    main()
