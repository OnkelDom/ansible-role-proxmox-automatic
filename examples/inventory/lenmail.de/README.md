---
This inventory preserves historical Debian 13 preseed files from ansible-infra-lenmail.

The host_vars entries point each VM at an exact legacy preseed snapshot via proxmox_automatic_preseed_template.
That keeps the old installer behavior reproducible while the role continues to generate and remaster media.

Usage:

```bash
ansible-playbook -i examples/inventory/lenmail.de/hosts.yml examples/playbook.yml
```

Notes:

- The VM IDs for the lenmail.de hosts are example values and should be adjusted before real use.
- The swarm hosts keep their previous per-host Proxmox placement overrides.
- The preseed files live in examples/inventory/lenmail.de/preseed/ with the original file names.