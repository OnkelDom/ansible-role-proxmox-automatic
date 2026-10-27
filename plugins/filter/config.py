"""Normalize the public API without mutating inventory variables."""
from copy import deepcopy
import ipaddress
import re

from ansible.errors import AnsibleFilterError


def merge(base, overlay):
    result = deepcopy(base)
    for key, value in overlay.items():
        result[key] = merge(result.get(key, {}), value) if isinstance(value, dict) else deepcopy(value)
    return result


def named_layers(layers):
    result = {}
    for layer in layers:
        if not isinstance(layer, list):
            raise AnsibleFilterError("Named configuration layers must be lists of dictionaries")
        for entry in layer:
            if not isinstance(entry, dict) or not entry.get('name'):
                raise AnsibleFilterError("Every disk, network and user requires a name")
            result[entry['name']] = merge(result.get(entry['name'], {}), entry)
    return list(result.values())


def rule_list(rules, guest=False):
    names = set()
    for rule in rules:
        if not isinstance(rule, dict) or not re.fullmatch(r'[A-Za-z0-9_-]+', rule.get('name', '')):
            raise AnsibleFilterError('Firewall rules require a stable alphanumeric name')
        if rule['name'] in names:
            raise AnsibleFilterError('Duplicate firewall rule name: ' + rule['name'])
        names.add(rule['name'])
        if rule.get('state', 'present') not in ('present', 'absent'):
            raise AnsibleFilterError('Firewall state must be present or absent')
        if rule.get('type', 'in') not in ('in', 'out', 'group'):
            raise AnsibleFilterError('Firewall type must be in, out or group')
        if rule.get('type', 'in') == 'group':
            if guest:
                raise AnsibleFilterError('Guest rules cannot reference Proxmox security groups')
            if not rule.get('action'):
                raise AnsibleFilterError('A group reference requires action: <group name>')
        elif rule.get('action', 'ACCEPT') not in ('ACCEPT', 'DROP', 'REJECT'):
            raise AnsibleFilterError('Unsupported firewall action')
        if guest:
            if set(rule) - {'name', 'type', 'action', 'proto', 'source', 'dest', 'dport', 'sport', 'state', 'enable', 'comment'}:
                raise AnsibleFilterError('Unsupported guest firewall field')
            if rule.get('proto', 'tcp') not in ('tcp', 'udp', 'icmp', 'ipv6-icmp'):
                raise AnsibleFilterError('Unsupported guest protocol')
            for key in ('source', 'dest'):
                if rule.get(key):
                    try:
                        ipaddress.ip_network(rule[key], strict=False)
                    except ValueError as exc:
                        raise AnsibleFilterError('Guest addresses must be literal IPs/CIDRs') from exc
            if rule.get('source') and rule.get('dest'):
                if ipaddress.ip_network(rule['source'], strict=False).version != ipaddress.ip_network(rule['dest'], strict=False).version:
                    raise AnsibleFilterError('A guest rule cannot mix IPv4 and IPv6')
            for key in ('dport', 'sport'):
                if rule.get(key) is not None:
                    if rule.get('proto', 'tcp') not in ('tcp', 'udp'):
                        raise AnsibleFilterError('Ports require TCP or UDP')
                    parts = str(rule[key]).split(':')
                    if len(parts) > 2 or any(not p.isdigit() or not 1 <= int(p) <= 65535 for p in parts):
                        raise AnsibleFilterError('Guest ports must be numbers or start:end ranges')
                    if len(parts) == 2 and int(parts[0]) > int(parts[1]):
                        raise AnsibleFilterError('Invalid port range')
    return rules



def normalize_api(value):
    result = merge({'host': '', 'user': '', 'password': '', 'token_id': '', 'token_secret': '',
                    'validate_certs': True, 'timeout': 60}, value)
    if result['token_id'] and '!' in result['token_id']:
        result['user'], result['token_id'] = result['token_id'].split('!', 1)
    if not result['host'] or not result['user']:
        raise AnsibleFilterError('Proxmox API host and user are required')
    if not ((result['token_id'] and result['token_secret']) or
            (result['password'] and result['password'] != '<filleme>')):
        raise AnsibleFilterError('Provide an API token or a real API password')
    if result['token_id'] and result['token_secret']:
        # proxmoxer prefers password authentication when both are supplied.
        result['password'] = ''
    return result


def validate_cluster_firewall(value):
    unknown = set(value) - {'groups', 'aliases', 'ipsets', 'rules', 'options'}
    if unknown:
        raise AnsibleFilterError('Unknown central firewall keys: ' + ', '.join(sorted(unknown)))
    for kind in ('groups', 'aliases', 'ipsets'):
        names = set()
        for entry in value.get(kind, []):
            name = entry.get('name', '')
            if not re.fullmatch(r'[a-z][a-z0-9_-]{0,19}', name) or name in names:
                raise AnsibleFilterError('Firewall object names must be unique lowercase identifiers, max 20 characters')
            names.add(name)
            if entry.get('state', 'present') not in ('present', 'absent'):
                raise AnsibleFilterError('Firewall object state must be present or absent')
            allowed = {'name', 'state', 'comment'} | {'groups': {'rules'}, 'aliases': {'cidr'}, 'ipsets': {'cidrs'}}[kind]
            if set(entry) - allowed:
                raise AnsibleFilterError('Unsupported ' + kind + ' field')
            if kind == 'groups':
                rule_list(entry.get('rules', []))
            if kind == 'aliases' and entry.get('state', 'present') != 'absent':
                ipaddress.ip_network(entry['cidr'], strict=False)
            if kind == 'ipsets':
                cidrs = set()
                for member in entry.get('cidrs', []):
                    ipaddress.ip_network(member['cidr'], strict=False)
                    if member['cidr'] in cidrs:
                        raise AnsibleFilterError('Duplicate IP-set member')
                    cidrs.add(member['cidr'])
    rule_list(value.get('rules', []))
    if set(value.get('options', {})) - {'enable', 'policy_in', 'policy_out'}:
        raise AnsibleFilterError('Only explicitly configured enable, policy_in and policy_out are supported')
    for key in ('policy_in', 'policy_out'):
        if key in value.get('options', {}) and value['options'][key] not in ('ACCEPT', 'DROP', 'REJECT'):
            raise AnsibleFilterError('Invalid central firewall policy')
    return deepcopy(value)

def normalize(variables, validate=True):
    removed = ['smtp_host', 'smtp_port', 'smtp_from', 'smtp_user', 'smtp_password', 'smtp_root', 'host_description', 'host_responsible', 'dnf_automatic_enabled', 'dnf_recipients', 'enable_epel', 'epel_packages', 'ha_group_nofailback']
    obsolete = [name for name in removed if 'proxmox_automatic_' + name in variables]
    if obsolete and validate:
        raise AnsibleFilterError('Removed no-op/retired settings: ' + ', '.join(obsolete) +
                                 '. Configure repositories/patching/notifications in the operating-system role.')
    legacy = {k.removeprefix('proxmox_automatic_'): deepcopy(v)
              for k, v in variables.items() if k.startswith('proxmox_automatic_')}
    for target, stem in [('storage_config', 'storage_config'), ('networks', 'networks'), ('users_merged', 'users')]:
        layers = [legacy.get(stem + '_' + suffix, []) for suffix in ('defaults', 'group_vars', 'host_vars')]
        layers.append(legacy.get(stem + '_playbook', legacy.get(stem, [])))
        legacy[target] = named_layers(layers)
    vm = merge({
        'name': variables.get('ansible_host', variables.get('inventory_hostname', '')),
        'node': legacy.get('hypervisor', '').split('.')[0], 'vmid': legacy.get('vmid'),
        'pool': legacy.get('vm_pool', ''),
        'startup': ('order=' + str(legacy.get('boot_order', 1)) + ',up=' + str(legacy.get('boot_order_up_wait', 2)) +
                    ',down=' + str(legacy.get('boot_order_down_wait', 3))) if 'startup_order' in legacy else '',
        'iso_storage': legacy.get('storage', legacy.get('pve_iso_storage', 'local')),
        'disk_storage': legacy.get('storage', legacy.get('pve_vm_storage', 'local-lvm')),
        'disks': legacy['storage_config'], 'networks': legacy['networks'],
        'hardware': {
            'cores': legacy.get('vcpu', 2), 'memory': legacy.get('memory', 2048),
            'sockets': legacy.get('sockets', 1), 'cpu': legacy.get('cpu_type', 'x86-64-v3'),
            'machine': legacy.get('machine', 'q35'), 'bios': 'ovmf',
            'efi': True, 'tpm': True, 'kvm': legacy.get('kvm', True),
            'numa': True,
            'onboot': legacy.get('onboot', True), 'ostype': legacy.get('os_type', 'l26'),
            'vga': legacy.get('vga', 'std'), 'hostpci': legacy.get('hostpci', {}),
            'hotplug': legacy.get('hotplug', 'network,disk,cpu,memory,usb'),
            'scsihw': legacy.get('scsi_hw', 'virtio-scsi-single'),
            'pre_enrolled_keys': legacy.get('efi_pre_enrolled_keys', False),
        }}, variables.get('proxmox_vm', {}))
    vm['boot_disk'] = next((d['name'] for d in vm['disks'] if d.get('bootloader')), vm['disks'][0]['name'] if vm['disks'] else '')
    install = merge({
        'backend': legacy.get('installer_backend', 'rocky_kickstart'),
        'source': legacy.get('install_source', 'online'),
        'source_iso': legacy.get('source_iso_path', ''),
        'source_iso_name': legacy.get('source_iso_name', legacy.get('iso_name', '')),
        'generated_iso_name': legacy.get('generated_iso_name', ''),
        'files_dir': legacy.get('files_dir', 'kickstart-files'),
        'iso_dir': legacy.get('iso_dir', 'kickstart-isos'),
        'build_dir': legacy.get('iso_build_dir', 'kickstart-isos/build'),
        'skip_upload': legacy.get('skip_iso_upload', False),
        'install_dependencies': legacy.get('install_dependencies', False),
        'kickstart_template': legacy.get('kickstart_template', ''),
        'preseed_template': legacy.get('preseed_template', ''), 'settings': {},
    }, variables.get('proxmox_install', {}))
    settings_allowed = {'timezone', 'ntp_servers', 'dns_servers', 'language', 'keyboard_layout', 'keyboard_variants',
                        'dhcp_enabled', 'ipv6_enabled', 'ipv6_dns_servers', 'ipv6_sysctl_settings', 'selinux_mode',
                        'firewall_enabled', 'firewall_services', 'enabled_services', 'disabled_services',
                        'debian_suite', 'debian_mirror', 'debian_mirror_directory', 'debian_security_host',
                        'debian_tasksel', 'debian_interface_prefix', 'debian_interface_index_start',
                        'debian_partition_recipe_override', 'debian_late_command_extra',
                        'debian_disable_network_manager', 'debian_root_login', 'debian_purge_microcode',
                        'repos', 'url_baseos', 'url_mirrorlist', 'packages_default', 'packages_additional',
                        'minimal_environment', 'package_retries', 'package_timeout', 'install_languages'}
    if set(install['settings']) - settings_allowed:
        raise AnsibleFilterError('Unsupported installer setting')
    legacy.update(install['settings'])
    if install['backend'] == 'debian_preseed':
        install['backend'] = 'debian13_preseed'
    if 'backend' in variables.get('proxmox_install', {}):
        explicit_hardware = variables.get('proxmox_vm', {}).get('hardware', {})
        if 'pre_enrolled_keys' not in explicit_hardware:
            vm['hardware']['pre_enrolled_keys'] = install['backend'] != 'debian13_preseed'
        if 'vga' not in explicit_hardware:
            vm['hardware']['vga'] = 'std'
    if vm['hardware']['vga'] == 'default':
        vm['hardware']['vga'] = 'std'
    api = merge({
        'host': legacy.get('api_host', ''), 'user': legacy.get('api_user', ''),
        'password': legacy.get('api_password', ''), 'token_id': legacy.get('api_token_id', ''),
        'token_secret': legacy.get('api_token_secret', ''),
        'validate_certs': legacy.get('api_validate_certs', True), 'timeout': 60,
    }, variables.get('proxmox_api', {}))
    # New API uses a complete token ID; community.proxmox takes the name separately.
    if api['token_id'] and '!' in api['token_id']:
        api['user'], api['token_id'] = api['token_id'].split('!', 1)
    if api['token_id'] and api['token_secret']:
        api['password'] = ''
    primary = next((n for n in vm['networks'] if n['name'] == 'net0'), next(iter(vm['networks']), {}))
    if vm['vmid'] is None and primary.get('ip'):
        vm['vmid'] = int(primary.get('vlanid', 0)) * 1000 + int(primary['ip'].split('.')[-1])
    guest = merge({
        'host': primary.get('ip', vm['name']), 'port': legacy.get('ssh_port', 22),
        'users': legacy['users_merged'], 'packages': legacy.get('packages_additional', []),
        'sysctl': legacy.get('sysctl_settings', {}), 'additional_hosts': legacy.get('additional_hosts', []),
        'ssh_user': next((u['name'] for u in legacy['users_merged'] if u.get('state', 'present') == 'present'), ''),
        'manage_users': True, 'manage_packages': True, 'manage_sysctl': True,
    }, variables.get('proxmox_guest', {}))
    if not guest['ssh_user']:
        guest['ssh_user'] = next((u['name'] for u in guest['users'] if u.get('state', 'present') == 'present'), '')
    firewall = merge({'pve_enabled': False, 'guest_enabled': False, 'groups': [], 'rules': [],
                      'guest_rules': [], 'allow_other_firewalls': False, 'management_sources': [], 'policy_in': 'DROP', 'policy_out': 'ACCEPT'},
                     variables.get('proxmox_firewall', {}))
    if firewall['guest_enabled']:
        legacy['firewall_enabled'] = False  # The installer must not activate a competing firewalld policy.
    cluster = merge({'groups': [], 'aliases': [], 'ipsets': [], 'rules': [], 'options': {}},
                    variables.get('proxmox_cluster_firewall', {}))
    ha = merge({'enabled': legacy.get('ha_enabled', False), 'manage': legacy.get('ha_group_manage', True),
                'name': legacy.get('ha_group', ''), 'auto': legacy.get('ha_group_auto', True),
                'nodes': legacy.get('ha_group_nodes', ''), 'strict': legacy.get('ha_group_restricted', False),
                'state': legacy.get('ha_state', 'started'), 'max_restart': legacy.get('ha_max_restart', 1),
                'max_relocate': legacy.get('ha_max_relocate', 1), 'comment': legacy.get('ha_comment', ''),
                'rule_comment': legacy.get('ha_group_comment', '') or None},
               variables.get('proxmox_ha', {}))
    if not ha['name'] and ha['auto']:
        ha['name'] = 'ha-group-' + vm['node'].split('.')[0]
    deploy = merge({'wait_for_install': True, 'configure_guest': True, 'detach_media': True,
                    'install_timeout': 3600, 'reinstall': False, 'update_hardware': False,
                    'cleanup_local_artifacts': False}, variables.get('proxmox_deploy', {}))
    legacy.update(storage_config=vm['disks'], networks=vm['networks'], users_merged=guest['users'],
                  installer_backend=install['backend'], install_source=install['source'])
    legacy['packages_effective'] = legacy.get('packages_default') or legacy.get(
        'debian_packages_default' if install['backend'] == 'debian13_preseed' else 'packages_default_rocky_kickstart', [])
    legacy['additional_hosts'] = deepcopy(guest['additional_hosts'])
    legacy['sysctl_settings'] = deepcopy(guest['sysctl'])
    legacy['users_merged'] = [u for u in guest['users'] if u.get('state', 'present') == 'present']
    for user in guest['users']:
        if user.get('sudo_commands', '').startswith('NOPASSWD:'):
            user['sudo_commands'] = user['sudo_commands'].split(':', 1)[1].strip()
            user['sudo_nopasswd'] = True
    legacy['users_merged'] = [deepcopy(u) for u in guest['users'] if u.get('state', 'present') == 'present']
    # A source ISO is immutable input; arbitrary paths never become shell source text.
    for value in [vm['name'], vm['node'], install['generated_iso_name'], install['source_iso_name']]:
        if value and not re.fullmatch(r'[A-Za-z0-9_.-]+', str(value)):
            raise AnsibleFilterError('VM, node and ISO names must use letters, digits, dots, underscores or hyphens')
    for value in [install['files_dir'], install['iso_dir'], install['build_dir'], install['source_iso']]:
        if value and not re.fullmatch(r'[A-Za-z0-9_./ -]+', str(value)):
            raise AnsibleFilterError('Installer paths contain unsupported shell metacharacters')
    if validate:
        public_keys = {
            'proxmox_api': {'host', 'user', 'password', 'token_id', 'token_secret', 'validate_certs', 'timeout'},
            'proxmox_vm': {'name', 'node', 'vmid', 'pool', 'startup', 'iso_storage', 'disk_storage', 'disks', 'networks', 'hardware'},
            'proxmox_install': {'backend', 'source', 'source_iso', 'source_iso_name', 'generated_iso_name', 'files_dir',
                                'iso_dir', 'build_dir', 'skip_upload', 'install_dependencies',
                                'kickstart_template', 'preseed_template', 'settings'},
            'proxmox_guest': {'host', 'port', 'users', 'packages', 'sysctl', 'additional_hosts', 'ssh_user',
                              'manage_users', 'manage_packages', 'manage_sysctl'},
            'proxmox_ha': {'enabled', 'manage', 'name', 'auto', 'nodes', 'strict', 'state', 'max_restart',
                           'max_relocate', 'comment', 'rule_comment'},
            'proxmox_firewall': {'pve_enabled', 'guest_enabled', 'groups', 'rules', 'guest_rules',
                                 'allow_other_firewalls', 'management_sources', 'policy_in', 'policy_out'},
            'proxmox_cluster_firewall': {'groups', 'aliases', 'ipsets', 'rules', 'options'},
            'proxmox_deploy': {'wait_for_install', 'configure_guest', 'detach_media', 'install_timeout',
                               'reinstall', 'update_hardware', 'cleanup_local_artifacts'},
        }
        for key, allowed in public_keys.items():
            unknown = set(variables.get(key, {})) - allowed
            if unknown:
                raise AnsibleFilterError('Unsupported ' + key + ' keys: ' + ', '.join(sorted(unknown)))
        for model, keys in [(firewall, ('pve_enabled', 'guest_enabled', 'allow_other_firewalls')),
                            (deploy, ('wait_for_install', 'configure_guest', 'detach_media', 'reinstall',
                                      'update_hardware', 'cleanup_local_artifacts')),
                            (ha, ('enabled', 'manage', 'auto', 'strict'))]:
            if any(not isinstance(model[key], bool) for key in keys):
                raise AnsibleFilterError('Configuration switches must be YAML booleans, not strings')
        if ha['state'] not in ('started', 'stopped', 'disabled', 'ignored'):
            raise AnsibleFilterError('Unsupported HA resource state')
        hardware_keys = {'cores', 'memory', 'sockets', 'cpu', 'machine', 'bios', 'efi', 'tpm', 'kvm',
                         'onboot', 'ostype', 'vga', 'hostpci', 'hotplug', 'scsihw', 'pre_enrolled_keys', 'numa'}
        if set(vm['hardware']) - hardware_keys:
            raise AnsibleFilterError('Unsupported VM hardware key')
        if not vm['hardware']['numa'] and 'memory' in vm['hardware']['hotplug'].split(','):
            raise AnsibleFilterError('Memory hotplug requires NUMA')
        if not re.fullmatch(r'[A-Za-z0-9_.@-]+', str(legacy.get('language', 'en_US.UTF-8'))) or not re.fullmatch(r'[A-Za-z0-9_-]+', str(legacy.get('keyboard_layout', 'de'))):
            raise AnsibleFilterError('Invalid locale or keyboard identifier')
        if not api['host'] or not vm['node'] or not vm['name']:
            raise AnsibleFilterError('API host, VM node and VM name are required')
        if not (api['token_id'] and api['token_secret']) and (not api['password'] or api['password'] == '<filleme>'):
            raise AnsibleFilterError('Provide an API token or a real API password')
        if vm['vmid'] is None or not 100 <= int(vm['vmid']) <= 999999999:
            raise AnsibleFilterError('VMID must be explicit or derivable, between 100 and 999999999')
        if install['backend'] not in ('rocky_kickstart', 'debian13_preseed') or install['source'] not in ('online', 'cdrom'):
            raise AnsibleFilterError('Unsupported installer backend or source')
        if deploy['wait_for_install'] and not guest['ssh_user']:
            raise AnsibleFilterError('Installation verification requires proxmox_guest.ssh_user or a bootstrap user')
        if firewall['guest_enabled'] and (firewall['policy_in'] == 'REJECT' or firewall['policy_out'] == 'REJECT'):
            raise AnsibleFilterError('nftables base policies must be ACCEPT or DROP; use REJECT on individual rules')
        if not 1 <= int(guest['port']) <= 65535:
            raise AnsibleFilterError('Guest SSH port must be between 1 and 65535')
        if not vm['disks'] or not vm['networks']:
            raise AnsibleFilterError('At least one disk and network are required')
        if len([d for d in vm['disks'] if d.get('bootloader')]) > 1:
            raise AnsibleFilterError('Only one disk may be marked as bootloader')
        for disk in vm['disks']:
            if not re.fullmatch(r'virtio\d+', disk['name']) or int(disk.get('size', 0)) <= 0:
                raise AnsibleFilterError('Disks require virtioN names and positive sizes')
        for net in vm['networks']:
            if not re.fullmatch(r'net\d+', net['name']) or not 0 <= int(net.get('vlanid', 0)) <= 4094:
                raise AnsibleFilterError('Invalid network name or VLAN')
            if not legacy.get('dhcp_enabled', False) and (not net.get('ip') or not net.get('netmask')):
                raise AnsibleFilterError('Static interfaces require explicit IPv4 address and netmask')
            if net.get('ip'):
                ipaddress.IPv4Interface(net['ip'] + '/' + net.get('netmask', '255.255.255.0'))
            if net.get('gateway'):
                ipaddress.IPv4Address(net['gateway'])
            if net.get('ipv6'):
                ipaddress.IPv6Interface(net['ipv6'])
            if net.get('ipv6_gateway'):
                ipaddress.IPv6Address(net['ipv6_gateway'])
            if net.get('mac') and not re.fullmatch(r'(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', net['mac']):
                raise AnsibleFilterError('Invalid interface MAC address')
            if net.get('interface_name') and not re.fullmatch(r'[A-Za-z0-9_.-]{1,15}', net['interface_name']):
                raise AnsibleFilterError('Invalid guest interface name')
        for collection in (vm['disks'], vm['networks'], guest['users']):
            if len({item['name'] for item in collection}) != len(collection):
                raise AnsibleFilterError('Duplicate names in structured configuration')
        if install['backend'] == 'debian13_preseed' and any(len(d.get('vg', [])) > 1 for d in vm['disks']):
            raise AnsibleFilterError('Debian currently supports one VG per disk')
        for user in guest['users']:
            if user.get('state', 'present') not in ('present', 'absent'):
                raise AnsibleFilterError('User state must be present or absent')
            if any(int(user[key]) < 0 for key in ('uid', 'gid') if key in user):
                raise AnsibleFilterError('UID and GID must be non-negative')
            if any(c in user.get('sudo_commands', '') for c in ('\n', '\r')):
                raise AnsibleFilterError('sudo_commands must be a single line')
            if user.get('password') and any(c in user['password'] for c in ("'", '\n', '\r', '`')):
                raise AnsibleFilterError('Password contains unsupported installer quoting characters; use a password hash')
            if not re.fullmatch(r'[a-z_][a-z0-9_-]*[$]?', user['name']):
                raise AnsibleFilterError('Invalid user name')
        if firewall['pve_enabled'] or firewall['guest_enabled']:
            if not firewall['management_sources']:
                raise AnsibleFilterError('Firewall activation requires explicit management_sources for SSH access')
        for cidr in firewall['management_sources']:
            ipaddress.ip_network(cidr, strict=False)
        if firewall['policy_in'] not in ('ACCEPT', 'DROP', 'REJECT') or firewall['policy_out'] not in ('ACCEPT', 'DROP', 'REJECT'):
            raise AnsibleFilterError('Unsupported firewall policy')
        rule_list(firewall['rules'])
        rule_list(firewall['guest_rules'], guest=True)
        validate_cluster_firewall(cluster)
        if deploy['configure_guest'] and not deploy['wait_for_install']:
            raise AnsibleFilterError('Guest configuration requires installation verification')
        if firewall['guest_enabled'] and not deploy['wait_for_install']:
            raise AnsibleFilterError('Guest firewall requires installation verification')
        if ha['enabled'] and not deploy['wait_for_install']:
            raise AnsibleFilterError('HA activation requires installation verification')
    return {'api': api, 'vm': vm, 'install': install, 'guest': guest, 'ha': ha,
            'firewall': firewall, 'cluster_firewall': cluster, 'deploy': deploy, 'legacy': legacy}


class FilterModule:
    def filters(self):
        return {'normalize_config': normalize, 'merge_named': named_layers, 'cluster_plan': cluster_plan, 'normalize_api': normalize_api,
                'validate_cluster_firewall': validate_cluster_firewall, 'management_allows': management_allows}


def cluster_plan(configs, api_host):
    selected = [c for c in configs if c['api']['host'] == api_host]
    vmids, names, profiles = set(), set(), {}
    nodes = sorted({c['vm']['node'] for c in selected})
    for config in selected:
        vm = config['vm']
        if vm['vmid'] in vmids or vm['name'] in names:
            raise AnsibleFilterError('Duplicate VMID or VM name within the same cluster')
        vmids.add(vm['vmid'])
        names.add(vm['name'])
        if config['cluster_firewall'] != selected[0]['cluster_firewall']:
            raise AnsibleFilterError('Conflicting central firewall definitions for the same cluster')
        ha = config['ha']
        if not ha['enabled']:
            continue
        if ha['nodes']:
            parsed = [(n.split(':')[0], int(n.split(':')[1]) if ':' in n else 0) for n in ha['nodes'].split(',')]
            maximum = max(p for _, p in parsed)
            normalized = [n + ':' + str(maximum - p + 1) for n, p in parsed]
        else:
            ordered = [vm['node']] + [n for n in nodes if n != vm['node']]
            normalized = [n + ':' + str(len(ordered) - index) for index, n in enumerate(ordered)]
        if not ha['manage']:
            normalized = []
        profile = {'nodes': normalized, 'strict': bool(ha['strict']), 'manage': bool(ha['manage']),
                   'comment': ha['rule_comment'], 'resources': []}
        existing = profiles.setdefault(ha['name'], profile)
        if existing['nodes'] != normalized or existing['strict'] != bool(ha['strict']) or existing['manage'] != bool(ha['manage']):
            raise AnsibleFilterError('Conflicting shared HA rule profile: ' + ha['name'])
        if existing['comment'] is not None and ha['rule_comment'] is not None and existing['comment'] != ha['rule_comment']:
            raise AnsibleFilterError('Conflicting shared HA rule comment')
        if ha['rule_comment'] is not None:
            existing['comment'] = ha['rule_comment']
        existing['resources'].append('vm:' + str(vm['vmid']))
    return profiles



def management_allows(connection, cidrs):
    try:
        source = ipaddress.ip_address(connection.split()[0])
        return any(source in ipaddress.ip_network(cidr, strict=False) for cidr in cidrs)
    except (ValueError, IndexError):
        return False
