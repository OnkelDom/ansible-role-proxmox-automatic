#!/usr/bin/env python3
"""Expose this checkout as an isolated role and collection for local validation."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for relative in ('.collections/ansible_collections/degitag/proxmox', '.ci-roles/proxmox_automatic'):
    link = root / relative
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink() and link.resolve() == root:
        continue
    if link.exists() or link.is_symlink():
        raise SystemExit('Refusing to replace existing test path: ' + str(link))
    link.symlink_to(root, target_is_directory=True)

# Remove only our own obsolete namespace alias, never an unrelated checkout.
obsolete = root / '.collections/ansible_collections/lenmail/proxmox'
if obsolete.is_symlink() and obsolete.resolve() == root:
    obsolete.unlink()
