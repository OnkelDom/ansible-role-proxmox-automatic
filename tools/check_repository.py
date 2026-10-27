#!/usr/bin/env python3
"""Check the shared degitag collection repository contract without host changes."""
from __future__ import annotations

import argparse
from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[1]
README_HEADINGS = (
    'Verantwortung und Architektur', 'Plattformen und Laufzeit', 'Installation',
    'Verwendung', 'Rollen', 'Repository-Struktur', 'Entwicklung und Checks',
    'CI und Releases', 'Migration', 'Sicherheit', 'Lizenz',
)
REQUIRED = (
    'README.md', 'CHANGELOG.md', 'LICENSE', 'CONTRIBUTING.md', 'SECURITY.md',
    '.editorconfig', 'Makefile', 'galaxy.yml', 'ansible.cfg', 'requirements.yml',
    'requirements-test.txt', 'meta/runtime.yml', '.github/dependabot.yml',
    '.github/workflows/ci.yml', '.github/workflows/release.yml',
    'tests/run_checks.sh', 'docs/migration.md', 'docs/repository-standard.md',
    'tools/check_collection_artifact.py', 'tools/collection_metadata.py',
)


def check(root: Path = ROOT) -> list[str]:
    errors = [f'Missing {name}' for name in REQUIRED if not (root / name).is_file()]
    for name in ('roles', 'tests/unit', 'docs/validation'):
        if not (root / name).is_dir():
            errors.append(f'Missing {name}/')
    for alternatives in (('.ansible-lint.yml', '.ansible-lint'), ('.yamllint.yml', '.yamllint')):
        if not any((root / name).is_file() for name in alternatives):
            errors.append('Missing ' + ' or '.join(alternatives))
    if errors:
        return errors
    metadata = yaml.safe_load((root / 'galaxy.yml').read_text())
    if metadata.get('namespace') != 'degitag':
        errors.append('Collection namespace must be degitag')
    readme = (root / 'README.md').read_text()
    if f"`{metadata['namespace']}.{metadata['name']}`" not in readme.splitlines()[0]:
        errors.append('README title must contain collection identity')
    headings = re.findall(r'^## (.+)$', readme, flags=re.MULTILINE)
    if headings != list(README_HEADINGS):
        errors.append('README H2 headings differ from repository-standard.md')
    for path in (root / '.github/workflows').glob('*.yml'):
        data = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
        if data.get('permissions', {}).get('contents') != 'read':
            errors.append(f'{path.name}: top-level contents permission must be read')
        for job in data.get('jobs', {}).values():
            for step in job.get('steps', []):
                action = step.get('uses', '')
                if action and not action.startswith('./') and not re.fullmatch(r'[^@]+@[a-f0-9]{40}', action):
                    errors.append(f'{path.name}: unpinned action {action}')
                if action.startswith('actions/checkout@') and step.get('with', {}).get('persist-credentials') != 'false':
                    errors.append(f'{path.name}: checkout must not persist credentials')
    ci = yaml.load((root / '.github/workflows/ci.yml').read_text(), Loader=yaml.BaseLoader)
    jobs = ci.get('jobs', {})
    if not any('bash tests/run_checks.sh' in step.get('run', '') for job in jobs.values() for step in job.get('steps', [])):
        errors.append('CI must call bash tests/run_checks.sh')
    matrices = [job.get('strategy', {}).get('matrix', {}) for job in jobs.values()]
    if not any({'2.20', '2.21'} <= set(matrix.get('core', [])) for matrix in matrices if isinstance(matrix, dict)):
        errors.append('CI must test Ansible Core 2.20 and 2.21')
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    problems = check(args.root)
    if problems:
        parser.exit(1, '\n'.join(problems) + '\n')
    print('Repository contract degitag-collections-v1 passed')
