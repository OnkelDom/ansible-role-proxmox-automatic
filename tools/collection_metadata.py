#!/usr/bin/env python3
"""Print paths and identity from this checkout's galaxy.yml."""
import argparse
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def value(field, root=ROOT):
    info = yaml.safe_load((root / 'galaxy.yml').read_text())
    if field == 'artifact':
        return f"{info['namespace']}-{info['name']}-{info['version']}.tar.gz"
    if field == 'fqcn':
        return f"{info['namespace']}.{info['name']}"
    return str(info[field])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('field', choices=('artifact', 'namespace', 'name', 'version', 'fqcn'))
    print(value(parser.parse_args().field))
