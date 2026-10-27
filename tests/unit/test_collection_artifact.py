"""Reject corrupted, mislabeled and unsafe release payloads."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile

import pytest
import yaml

spec = importlib.util.spec_from_file_location('collection_artifact', Path(__file__).resolve().parents[2] / 'tools/check_collection_artifact.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def artifact(tmp_path, *, namespace='degitag', payload=b'content', recorded=b'content', extra=None):
    metadata = tmp_path / 'galaxy.yml'
    metadata.write_text(yaml.safe_dump({'namespace': 'degitag', 'name': 'example', 'version': '1.0.0'}))
    files = json.dumps({'files': [{'name': '.', 'ftype': 'dir'}, {'name': 'README.md', 'ftype': 'file', 'chksum_type': 'sha256', 'chksum_sha256': hashlib.sha256(recorded).hexdigest()}]}).encode()
    manifest = json.dumps({'collection_info': {'namespace': namespace, 'name': 'example', 'version': '1.0.0'}, 'file_manifest_file': {'chksum_sha256': hashlib.sha256(files).hexdigest()}}).encode()
    path = tmp_path / 'collection.tar.gz'
    with tarfile.open(path, 'w:gz') as archive:
        for name, data in (('README.md', payload), ('FILES.json', files), ('MANIFEST.json', manifest)):
            member = tarfile.TarInfo(name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
        if extra:
            member = tarfile.TarInfo(extra)
            archive.addfile(member, io.BytesIO(b''))
    return path, metadata


def test_valid_collection(tmp_path):
    path, metadata = artifact(tmp_path)
    assert checker.check(path, metadata)['name'] == 'example'


def test_wrong_namespace(tmp_path):
    path, metadata = artifact(tmp_path, namespace='degit')
    with pytest.raises(ValueError, match='namespace'):
        checker.check(path, metadata)


def test_corrupted_payload(tmp_path):
    path, metadata = artifact(tmp_path, payload=b'corrupt')
    with pytest.raises(ValueError, match='Payload checksum'):
        checker.check(path, metadata)


@pytest.mark.parametrize('name', ['../escape', '/absolute', '.venv-other/token', '.env', 'roles/example/tests/key', '.DS_Store'])
def test_unsafe_payload_members(tmp_path, name):
    path, metadata = artifact(tmp_path, extra=name)
    with pytest.raises(ValueError, match='Unexpected artifact member'):
        checker.check(path, metadata)


def test_unlisted_payload(tmp_path):
    path, metadata = artifact(tmp_path, extra='unlisted.txt')
    with pytest.raises(ValueError, match='differ from FILES'):
        checker.check(path, metadata)
