#!/usr/bin/env bash
# Shared entry point; named stages also back the Make targets.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
  export PATH="$VIRTUAL_ENV/bin:$PATH"
elif [[ -d .venv/bin ]]; then
  export PATH="$PWD/.venv/bin:$PATH"
fi
export ANSIBLE_HOME="${ANSIBLE_HOME:-$PWD/.ansible}"
export ANSIBLE_COLLECTIONS_PATH="$PWD/.collections:$PWD/.ansible/collections:${ANSIBLE_COLLECTIONS_PATH:-$HOME/.ansible/collections}"
PYTHON="${PYTHON:-python3}"

prepare_checkout() { "$PYTHON" tools/prepare_checkout.py; }
lint() {
  "$PYTHON" tools/check_repository.py
  yamllint .
  ansible-lint --offline
  "$PYTHON" -m compileall -q plugins tests/unit tools
}
syntax() {
  bash tests/run_role_syntax_checks.sh
  local playbook
  for playbook in tests/test.yml tests/render_templates.yml tests/build_media.yml \
    tests/configuration.yml playbooks/deploy.yml playbooks/firewall.yml \
    playbooks/configure_guests.yml tests/proxmox_e2e.yml tests/proxmox_e2e_cleanup.yml \
    roles/metric_server/tests/test.yml; do
    ansible-playbook "$playbook" --syntax-check
  done
}
unit() { "$PYTHON" -m pytest tests/unit -q; }
render() {
  ansible-playbook tests/render_templates.yml
  ansible-playbook tests/configuration.yml
  ansible-playbook tests/preflight.yml --tags proxmox_validate
}
media() { ansible-playbook tests/build_media.yml; }
build() { "$PYTHON" tools/build_collection.py; }
package_smoke() {
  local artifact
  artifact="$("$PYTHON" tools/collection_metadata.py artifact)"
  "$PYTHON" tools/check_collection_artifact.py "$artifact"
  "$PYTHON" tools/check_package.py "$artifact"
}
sanity() { bash tests/run_collection_sanity.sh "$("$PYTHON" tools/collection_metadata.py artifact)"; }

case "${1:-all}" in
  prepare)
    "$PYTHON" -m pip install -r requirements-test.txt
    ansible-galaxy collection install -r requirements.yml
    prepare_checkout
    ;;
  lint|syntax|unit|render|media|build) prepare_checkout; "$1" ;;
  package-smoke) prepare_checkout; build; package_smoke ;;
  sanity) sanity ;;
  all) prepare_checkout; lint; syntax; unit; render; media; build; package_smoke; sanity ;;
  *) printf 'Unknown check stage: %s\n' "$1" >&2; exit 2 ;;
esac
