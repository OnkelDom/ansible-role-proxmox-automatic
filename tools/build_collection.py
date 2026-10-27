#!/usr/bin/env python3
"""Build a runtime-only collection with regular files for the legacy adapters."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

from collection_metadata import ROOT, value

RUNTIME = ('galaxy.yml', 'README.md', 'LICENSE', 'VARIABLES.md', 'roles', 'plugins',
           'meta', 'defaults', 'tasks', 'templates', 'playbooks', 'examples')
ADAPTERS = {'defaults/main.yml', 'templates/kickstart.cfg.j2', 'templates/preseed.cfg.j2'}


def ignored(directory, names):
    return {name for name in names if name in {'__pycache__', '.DS_Store', 'tests', 'molecule'}
            or (Path(directory) == ROOT / 'examples' and name == 'roles')}


def build():
    with tempfile.TemporaryDirectory(prefix='proxmox-collection-build-') as directory:
        staging = Path(directory) / 'source'
        staging.mkdir()
        for name in RUNTIME:
            source = ROOT / name
            if not source.exists():
                continue
            if source.is_dir():
                for parent, dirs, files in os.walk(source, followlinks=False):
                    excluded = ignored(parent, dirs + files)
                    dirs[:] = [item for item in dirs if item not in excluded]
                    for item in dirs + files:
                        path = Path(parent) / item
                        if item in excluded or not path.is_symlink():
                            continue
                        target = path.resolve(strict=True)
                        if (path.relative_to(ROOT).as_posix() not in ADAPTERS
                                or not target.is_file() or ROOT not in target.parents):
                            raise ValueError('Unexpected runtime symlink: ' + str(path.relative_to(ROOT)))
                shutil.copytree(source, staging / name, ignore=ignored)
            else:
                shutil.copy2(source, staging / name)
        subprocess.run(['ansible-galaxy', 'collection', 'build', '--force',
                        '--output-path', str(ROOT)], cwd=staging, check=True)
    return ROOT / value('artifact')


if __name__ == '__main__':
    print(build())
