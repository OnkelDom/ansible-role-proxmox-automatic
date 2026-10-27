"""Plan and reconcile owned firewall rules without replacing foreign entries."""
from copy import deepcopy

RULE_KEYS = {'type', 'action', 'source', 'dest', 'proto', 'dport', 'sport', 'macro', 'iface', 'log', 'enable', 'icmp-type'}


def prepare_rules(rules, owner):
    result = []
    names = set()
    for rule in rules:
        name = rule.get('name')
        if not name or name in names:
            raise ValueError('Firewall rules require unique names')
        names.add(name)
        if rule.get('state', 'present') == 'absent':
            continue
        unknown = set(rule) - RULE_KEYS - {'name', 'state', 'comment'}
        if unknown:
            raise ValueError('Unsupported firewall fields: ' + ', '.join(sorted(unknown)))
        value = {k: v for k, v in rule.items() if k in RULE_KEYS}
        value.setdefault('type', 'in')
        value.setdefault('action', 'ACCEPT')
        value['enable'] = int(rule.get('enable', True))
        value['comment'] = owner + ':' + name + (' ' + rule['comment'] if rule.get('comment') else '')
        result.append(value)
    return result


def clean(rule):
    value = {k: v for k, v in rule.items() if k in RULE_KEYS | {'comment'} and v not in (None, '')}
    value.setdefault('enable', 0)
    value['enable'] = int(value['enable'])
    return value


def rule_plan(existing, wanted, owner):
    owned = [r for r in existing if r.get('comment', '').startswith(owner + ':')]
    foreign = [r for r in existing if not r.get('comment', '').startswith(owner + ':')]
    # Preserve foreign ordering and append a contiguous managed block after it.
    current = [clean(r) for r in existing]
    desired = [clean(r) for r in foreign] + [clean(r) for r in wanted]
    return {'changed': current != desired, 'delete': sorted([r['pos'] for r in owned], reverse=True),
            'create': deepcopy(wanted), 'offset': len(foreign)}


def reconcile_rules(api, path, rules, owner, check_mode=False):
    wanted = prepare_rules(rules, owner)
    existing = api.get(path)
    plan = rule_plan(existing, wanted, owner)
    if not plan['changed'] or check_mode:
        return plan['changed']
    def identity(rule):
        return rule.get('comment', '').split(' ', 1)[0]

    desired_ids = {identity(rule) for rule in wanted}
    for rule in wanted:
        current = api.get(path)
        matches = [r for r in current if identity(r) == identity(rule)]
        if len(matches) > 1:
            raise ValueError('Duplicate managed rule identity; resolve before reconciliation')
        existing_rule = matches[0] if matches else None
        if existing_rule is None:
            # A newly created allow rule must not briefly precede foreign deny rules.
            api.request('POST', path, dict(rule, enable=0))
            current = api.get(path)
            existing_rule = next(r for r in current if identity(r) == identity(rule))
            actual = existing_rule['pos']
            last = len(current) - 1
            if actual != last:
                detail = api.get(path + '/' + str(actual))
                api.request('PUT', path + '/' + str(actual), {'moveto': len(current), 'digest': detail['digest']})
                existing_rule = next(r for r in api.get(path) if identity(r) == identity(rule))
        if clean(existing_rule) != clean(rule):
            detail = api.get(path + '/' + str(existing_rule['pos']))
            if identity(detail) != identity(rule):
                raise RuntimeError('Firewall changed concurrently; refusing positional update')
            payload = dict(rule, digest=detail['digest'])
            obsolete = (set(clean(detail)) - set(clean(rule))) & RULE_KEYS
            if obsolete:
                payload['delete'] = ','.join(sorted(obsolete))
            api.request('PUT', path + '/' + str(existing_rule['pos']), payload)
    # Remove stale rules only after desired replacements are present.
    stale = [r for r in api.get(path) if r.get('comment', '').startswith(owner + ':') and identity(r) not in desired_ids]
    for rule in sorted(stale, key=lambda value: value['pos'], reverse=True):
        detail = api.get(path + '/' + str(rule['pos']))
        if identity(detail) != identity(rule):
            raise RuntimeError('Firewall changed concurrently; refusing positional deletion')
        api.request('DELETE', path + '/' + str(rule['pos']), {'digest': detail['digest']})
    for index, rule in enumerate(wanted):
        current = api.get(path)
        actual = next(r['pos'] for r in current if identity(r) == identity(rule))
        target = plan['offset'] + index
        if actual != target:
            detail = api.get(path + '/' + str(actual))
            api.request('PUT', path + '/' + str(actual),
                        {'moveto': target + 1 if actual < target else target, 'digest': detail['digest']})
    final = api.get(path)
    if any(r.get('errors') for r in final if r.get('comment', '').startswith(owner + ':')):
        raise RuntimeError('Proxmox reports invalid managed firewall rules; inspect aliases, IP sets and groups')
    if rule_plan(final, wanted, owner)['changed']:
        raise RuntimeError('Firewall readback differs from intended rule order')
    return True


class FirewallJournal:
    """Persist the original reads and each planned write before touching the API."""
    def __init__(self, api, directory):
        self.api = api
        self.directory = directory
        self.snapshots = {}
        self.operations = []
        self.path = None

    def get(self, path):
        result = self.api.get(path)
        self.snapshots.setdefault(path, deepcopy(result))
        return result

    def request(self, method, path, data=None):
        import json
        import os
        from pathlib import Path
        import tempfile
        directory = Path(self.directory)
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.path is None:
            fd, self.path = tempfile.mkstemp(prefix='firewall-', suffix='.json', dir=directory)
            os.close(fd)
        self.operations.append({'method': method, 'path': path, 'data': data})
        fd, temporary = tempfile.mkstemp(prefix='.journal-', dir=directory)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as journal:
                json.dump({'snapshots': self.snapshots, 'operations': self.operations}, journal, indent=2)
                journal.flush()
                os.fsync(journal.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return self.api.request(method, path, data)
