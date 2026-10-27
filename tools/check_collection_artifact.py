#!/usr/bin/env python3
"""Verify collection identity, payload boundaries and Galaxy file checksums."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {
    '.git', '.github', '.ansible', '.pytest_cache', '__pycache__', '.DS_Store',
    'tests', 'tools', 'docs', '.host-collection', 'node_modules', '.editorconfig',
    'AGENTS.md', 'Makefile', 'CONTRIBUTING.md', 'SECURITY.md', 'CHANGELOG.md',
    'ansible.cfg', '.gitignore', 'requirements-test.txt', 'requirements-dev.yml',
    '.ansible-lint', '.ansible-lint.yml', '.yamllint', '.yamllint.yml',
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check(path: str | Path, metadata: str | Path = ROOT / 'galaxy.yml') -> dict:
    expected = yaml.safe_load(Path(metadata).read_text())
    with tarfile.open(path, 'r:gz') as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive members')
        for member in members:
            name = PurePosixPath(member.name)
            if (name.is_absolute() or '..' in name.parts or '\\' in member.name
                    or not (member.isfile() or member.isdir())
                    or FORBIDDEN.intersection(name.parts)
                    or any(part.startswith(('.venv', '.env', '.zshenv')) for part in name.parts)
                    or member.name.endswith(('.tar.gz', '.pyc', '.pem', '.key'))):
                raise ValueError(f'Unexpected artifact member: {member.name}')
        manifest = json.load(archive.extractfile('MANIFEST.json'))
        info = manifest['collection_info']
        for key in ('namespace', 'name', 'version'):
            if str(info[key]) != str(expected[key]):
                raise ValueError(f'Unexpected collection {key}: {info[key]}')
        for key in ('namespace', 'name'):
            if not re.fullmatch(r'[a-z][a-z0-9_]*', info[key]):
                raise ValueError(f'Invalid collection {key}')
        file_manifest = archive.extractfile('FILES.json').read()
        if digest(file_manifest) != manifest['file_manifest_file']['chksum_sha256']:
            raise ValueError('FILES.json checksum mismatch')
        entries = json.loads(file_manifest)['files']
        listed = {entry['name'] for entry in entries}
        if len(listed) != len(entries):
            raise ValueError('Duplicate FILES.json entries')
        # Galaxy lists the logical collection root but omits its tar member.
        if set(names) - {'.'} != (listed - {'.'}) | {'MANIFEST.json', 'FILES.json'}:
            raise ValueError('Archive contents differ from FILES.json')
        for entry in entries:
            if entry['name'] == '.' and entry['ftype'] == 'dir' and '.' not in names:
                continue
            member = archive.getmember(entry['name'])
            if entry['ftype'] == 'file':
                if not member.isfile() or entry['chksum_type'] != 'sha256':
                    raise ValueError(f'Invalid file entry: {member.name}')
                if digest(archive.extractfile(member).read()) != entry['chksum_sha256']:
                    raise ValueError(f'Payload checksum mismatch: {member.name}')
            elif entry['ftype'] != 'dir' or not member.isdir():
                raise ValueError(f'Invalid directory entry: {member.name}')
        print(f"Verified {path}: {info['namespace']}.{info['name']}:{info['version']}, {len(names)} entries")
        return info


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifacts', nargs='+')
    parser.add_argument('--metadata', type=Path, default=ROOT / 'galaxy.yml')
    args = parser.parse_args()
    for artifact in args.artifacts:
        check(artifact, args.metadata)
