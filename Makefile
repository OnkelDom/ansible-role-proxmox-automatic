PYTHON ?= python3
ANSIBLE_PLAYBOOK ?= ansible-playbook

.PHONY: lint syntax render media unit test ci e2e-syntax e2e e2e-cleanup

lint:
	yamllint .
	ansible-lint
	$(PYTHON) -m py_compile library/proxmox_automatic_upload_iso.py

syntax:
	$(ANSIBLE_PLAYBOOK) tests/test.yml --syntax-check
	$(ANSIBLE_PLAYBOOK) tests/render_templates.yml --syntax-check
	$(ANSIBLE_PLAYBOOK) tests/build_media.yml --syntax-check
	$(ANSIBLE_PLAYBOOK) tests/proxmox_e2e.yml --syntax-check
	$(ANSIBLE_PLAYBOOK) tests/proxmox_e2e_cleanup.yml --syntax-check

render:
	$(ANSIBLE_PLAYBOOK) tests/render_templates.yml

media:
	$(ANSIBLE_PLAYBOOK) tests/build_media.yml

unit: lint syntax render

test: lint syntax render media

ci: lint syntax render

e2e-syntax:
	$(ANSIBLE_PLAYBOOK) tests/proxmox_e2e.yml --syntax-check
	$(ANSIBLE_PLAYBOOK) tests/proxmox_e2e_cleanup.yml --syntax-check

e2e:
	$(ANSIBLE_PLAYBOOK) tests/proxmox_e2e.yml

e2e-cleanup:
	$(ANSIBLE_PLAYBOOK) tests/proxmox_e2e_cleanup.yml
