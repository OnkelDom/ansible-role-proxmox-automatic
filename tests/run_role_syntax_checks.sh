#!/usr/bin/env bash
# Parse every collection role with facts enabled, without executing any tasks.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 - <<'PY'
from pathlib import Path
import subprocess
import tempfile
import yaml

info = yaml.safe_load(Path('galaxy.yml').read_text())
with tempfile.TemporaryDirectory(prefix='proxmox-role-syntax-') as directory:
    for role in sorted(Path('roles').iterdir()):
        if not (role / 'tasks/main.yml').is_file():
            continue
        name = f"{info['namespace']}.{info['name']}.{role.name}"
        playbook = Path(directory) / (role.name + '.yml')
        playbook.write_text(yaml.safe_dump([{'name': 'Syntax for ' + name,
                                           'hosts': 'localhost', 'gather_facts': True,
                                           'roles': [name]}], sort_keys=False))
        subprocess.run(['ansible-playbook', str(playbook), '--syntax-check',
                        '-i', 'localhost,', '-c', 'local'], check=True)
PY
