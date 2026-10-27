#!/usr/bin/env python3
from __future__ import annotations

import io
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString


ROOT = Path(__file__).resolve().parents[1]
INCLUDE_NAMES = {".ansible-lint.yml", "galaxy.yml", "meta/runtime.yml"}
INCLUDE_SUFFIXES = {".yml", ".yaml"}
EXCLUDE_PARTS = {".git", ".venv", ".ansible", ".host-collection", ".collections", ".ci-roles", ".e2e-live", ".cache"}


def iter_yaml_files() -> list[Path]:
    paths: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if EXCLUDE_PARTS.intersection(path.parts):
            continue
        relative = path.relative_to(ROOT)
        if relative.as_posix() in INCLUDE_NAMES or path.suffix in INCLUDE_SUFFIXES:
            paths.append(path)
    return sorted(paths)


def quote_ambiguous_strings(data):
    if isinstance(data, str) and data.lower() in {"yes", "no", "on", "off", "y", "n"}:
        return DoubleQuotedScalarString(data)
    if isinstance(data, list):
        for index, value in enumerate(data):
            data[index] = quote_ambiguous_strings(value)
    elif isinstance(data, dict):
        for key, value in data.items():
            data[key] = quote_ambiguous_strings(value)
    return data


def main() -> int:
    yaml = YAML()
    yaml.explicit_start = True
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    yaml.allow_unicode = False
    yaml.sort_base_mapping_type_on_output = False
    yaml.indent(mapping=2, sequence=2, offset=0)
    yaml.width = 1000

    for path in iter_yaml_files():
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            continue
        data = quote_ambiguous_strings(yaml.load(text))
        if data is None:
            continue
        buffer = io.StringIO()
        yaml.dump(data, buffer)
        formatted = buffer.getvalue()
        if not formatted.endswith("\n"):
            formatted = f"{formatted}\n"
        if formatted != text:
            path.write_text(formatted, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
