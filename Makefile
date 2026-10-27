PYTHON ?= python3
ANSIBLE_PLAYBOOK ?= ansible-playbook

.PHONY: prepare lint syntax render media unit test ci e2e-syntax e2e e2e-cleanup build package-smoke

prepare:
	$(PYTHON) scripts/prepare_checkout.py

lint: prepare
	yamllint .
	ansible-lint --offline
	$(PYTHON) -m compileall -q plugins tests/unit scripts

syntax: prepare
	$(ANSIBLE_PLAYBOOK) tests/test.yml --syntax-check
	$(ANSIBLE_PLAYBOOK) tests/render_templates.yml --syntax-check
	$(ANSIBLE_PLAYBOOK) tests/build_media.yml --syntax-check
	$(ANSIBLE_PLAYBOOK) tests/configuration.yml --syntax-check
	$(ANSIBLE_PLAYBOOK) playbooks/deploy.yml --syntax-check
	$(ANSIBLE_PLAYBOOK) playbooks/firewall.yml --syntax-check
	$(ANSIBLE_PLAYBOOK) playbooks/configure_guests.yml --syntax-check
	$(ANSIBLE_PLAYBOOK) tests/proxmox_e2e.yml --syntax-check
	$(ANSIBLE_PLAYBOOK) tests/proxmox_e2e_cleanup.yml --syntax-check

render: prepare
	$(ANSIBLE_PLAYBOOK) tests/render_templates.yml
	$(ANSIBLE_PLAYBOOK) tests/configuration.yml
	$(ANSIBLE_PLAYBOOK) tests/preflight.yml --tags proxmox_validate

media: prepare
	$(ANSIBLE_PLAYBOOK) tests/build_media.yml

unit: prepare
	$(PYTHON) -m unittest discover -s tests/unit -v

test: lint syntax unit render media

ci: test

e2e-syntax: prepare
	$(ANSIBLE_PLAYBOOK) tests/proxmox_e2e.yml --syntax-check
	$(ANSIBLE_PLAYBOOK) tests/proxmox_e2e_cleanup.yml --syntax-check

e2e: prepare
	$(ANSIBLE_PLAYBOOK) tests/proxmox_e2e.yml

e2e-cleanup: prepare
	$(ANSIBLE_PLAYBOOK) tests/proxmox_e2e_cleanup.yml

build:
	ansible-galaxy collection build --force

package-smoke: build
	$(PYTHON) scripts/check_package.py
