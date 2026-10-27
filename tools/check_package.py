#!/usr/bin/env python3
"""Validate a fresh collection installation, including its legacy role wrapper."""
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

from collection_metadata import value

root = Path(__file__).resolve().parents[1]
artifact = Path(sys.argv[1] if len(sys.argv) > 1 else root / value('artifact')).resolve()
python_bin = Path(sys.executable).parent
with tarfile.open(artifact) as archive:
    forbidden = {'.venv', '.git', '.ansible', '.collections', '.proxmox-firewall-backups', '.e2e-live'}
    if any(forbidden & set(name.split('/')) for name in archive.getnames()):
        raise SystemExit('Development caches or firewall backups leaked into the package')
    if any(name.startswith('examples/roles/') for name in archive.getnames()):
        raise SystemExit('Local example role symlinks leaked into the package')
with tempfile.TemporaryDirectory(prefix='proxmox-package-smoke-') as directory:
    workspace = Path(directory)
    target = workspace / 'collections'
    galaxy = python_bin / 'ansible-galaxy'
    playbook = python_bin / 'ansible-playbook'
    role = workspace / 'roles/proxmox_automatic'
    role.parent.mkdir()
    role.symlink_to(target / 'ansible_collections/degitag/proxmox', target_is_directory=True)
    config = workspace / 'ansible.cfg'
    config.write_text('[defaults]\ncollections_path = ' + str(target) + '\nroles_path = ' + str(role.parent) + '\n')
    env = dict(os.environ, ANSIBLE_CONFIG=str(config), ANSIBLE_COLLECTIONS_PATH=str(target),
               ANSIBLE_ROLES_PATH=str(role.parent))
    # Isolate installation as well as execution: an inherited checkout collection
    # must not make Galaxy skip installing the release artifact into the fresh target.
    subprocess.run([str(galaxy), 'collection', 'install', '--force', '--no-deps', '-p', str(target), str(artifact)],
                   cwd=directory, env=env, check=True, capture_output=True, text=True)
    installed = target / 'ansible_collections' / value('namespace') / value('name')
    if not (installed / 'roles/deploy/tasks/main.yml').is_file():
        raise SystemExit('Fresh collection installation did not create the deploy role')
    result = subprocess.run([str(playbook), str(root / 'tests/preflight.yml'), '--tags', 'proxmox_validate', '--check'],
                            cwd=directory, env=env, capture_output=True, text=True)
    if result.returncode:
        print(result.stdout)
        print(result.stderr)
        raise SystemExit(result.returncode)
print('PASS: fresh package installation, modern preflight and legacy role wrapper')
