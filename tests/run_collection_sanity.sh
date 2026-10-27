#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ARTIFACT="${1:?collection artifact required}"
# Validate before extracting, including rejection of links and unsafe paths.
python tools/check_collection_artifact.py "$ARTIFACT"
NAMESPACE="$(python tools/collection_metadata.py namespace)"
COLLECTION="$(python tools/collection_metadata.py name)"
SANITY_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/degitag-sanity.XXXXXX")"
trap 'rm -rf "$SANITY_ROOT"' EXIT
COLLECTION_PATH="$SANITY_ROOT/ansible_collections/$NAMESPACE/$COLLECTION"
mkdir -p "$COLLECTION_PATH"
tar -xzf "$ARTIFACT" -C "$COLLECTION_PATH"
# Outside the checkout: ignored install directories can make sanity skip targets.
cd "$COLLECTION_PATH"
ansible-test sanity --test compile --test import --python 3.12 --requirements
