PYTHON ?= python3
export PYTHON

.PHONY: prepare lint syntax unit test ci build package-smoke render media sanity e2e-syntax e2e e2e-cleanup

prepare lint syntax unit build package-smoke render media sanity:
	bash tests/run_checks.sh $@

test ci:
	bash tests/run_checks.sh

e2e-syntax:
	ansible-playbook tests/proxmox_e2e.yml --syntax-check
	ansible-playbook tests/proxmox_e2e_cleanup.yml --syntax-check

e2e:
	ansible-playbook tests/proxmox_e2e.yml

e2e-cleanup:
	ansible-playbook tests/proxmox_e2e_cleanup.yml
