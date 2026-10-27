# Native PVE metric server

Supported: PVE 9 on Debian 13. Run on exactly one representative node per cluster;
PVE stores this configuration in pmxcfs and every node exports its local node,
storage and guest statistics. For separate clusters, use separate plays or one
representative inventory host per cluster. Do not run concurrently on all members.

```yaml
- hosts: pve_cluster_representatives
  become: true
  gather_facts: false
  roles:
    - role: degitag.proxmox.metric_server
      proxmox_metric_server_host: metrics.example.invalid
      proxmox_metric_server_cluster: production-a
      proxmox_metric_server_headers: "{{ vault_otlp_headers }}"
```

Use HTTPS with trusted certificates and an Authorization header from Ansible Vault.
No PVE API token or additional node agent is needed. Explicit port defaults to 443;
this avoids the PVE plugin's unusual HTTP port default. The module supports check
mode and semantic header comparison, uses a returned API digest when available and preserves
other metric-server entries. Header values never appear in returned results.
Set `proxmox_metric_server_disabled: true` for reversible suspension; set state to
`absent` to remove only this named entry. Existing local log shipping is independent.

Receiver and alert rules are owned by `degit.monitoring`; endpoints, credentials
and cluster identities belong to the infrastructure inventory.
