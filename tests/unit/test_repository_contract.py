"""Ensure CI and documentation drift fails the shared repository gate."""
import importlib.util
from pathlib import Path
import shutil

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('repository_contract', ROOT / 'tools/check_repository.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


@pytest.fixture
def checkout(tmp_path):
    for name in checker.REQUIRED + ('.ansible-lint.yml', '.yamllint.yml'):
        source = ROOT / name
        if not source.exists():
            source = ROOT / name.removesuffix('.yml')
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    for directory in ('roles', 'tests/unit', 'docs/validation'):
        (tmp_path / directory).mkdir(parents=True, exist_ok=True)
    return tmp_path


def test_current_contract():
    assert checker.check(ROOT) == []


def test_missing_security_policy(checkout):
    (checkout / 'SECURITY.md').unlink()
    assert 'Missing SECURITY.md' in checker.check(checkout)


def test_readme_drift(checkout):
    path = checkout / 'README.md'
    path.write_text(path.read_text().replace('## Sicherheit', '## Irgendwas'))
    assert any('README H2' in error for error in checker.check(checkout))


def test_unpinned_action(checkout):
    path = checkout / '.github/workflows/ci.yml'
    data = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
    job = next(job for job in data['jobs'].values() if 'steps' in job)
    job['steps'].append({'uses': 'actions/checkout@main', 'with': {'persist-credentials': 'false'}})
    path.write_text(yaml.safe_dump(data))
    assert any('unpinned action' in error for error in checker.check(checkout))


def test_persisted_credentials(checkout):
    path = checkout / '.github/workflows/ci.yml'
    data = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
    job = next(job for job in data['jobs'].values() if 'steps' in job)
    job['steps'].append({'uses': 'actions/checkout@' + 'a' * 40})
    path.write_text(yaml.safe_dump(data))
    assert any('persist credentials' in error for error in checker.check(checkout))
