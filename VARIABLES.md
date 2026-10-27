# Konfigurationsreferenz

Die strukturierte Schnittstelle und ihre Beispiele sind in [README.md](README.md) beschrieben. Der folgende Index enthält die tatsächlich vorhandenen kompatiblen Defaults; die Laufzeitnormalisierung validiert zusätzliche Beziehungen und verweigert entfernte Optionen.

## Strukturierte Eingaben

| Variable | Bedeutung |
|---|---|
| `proxmox_api` | API-Zugang; vollständige Token-ID oder Benutzer und Passwort |
| `proxmox_vm` | Systemname, Node, VMID, Hardware, Disks und Netzwerke |
| `proxmox_install` | Backend, Quell-ISO, Artefaktpfade und Installer-Einstellungen |
| `proxmox_guest` | SSH-Ziel, Benutzer, Pakete und begrenzte Gastkonfiguration |
| `proxmox_ha` | HA-Ressourcen und gemeinsame Node-Affinity |
| `proxmox_firewall` | VM-Gruppenreferenzen, eigene VM-Regeln und optionale Gastregeln |
| `proxmox_cluster_firewall` | Zentrale Gruppen, Aliase, IP-Sets, Hostregeln und explizite globale Optionen |
| `proxmox_deploy` | Warten, Neuinstallation, Hardware-Updates und lokales Cleanup |

## Kompatible Defaults

| Variable | Typ | Default |
|---|---|---|
| `proxmox_automatic_install_dependencies` | bool | `False` |
| `proxmox_automatic_installer_backend` | str | `rocky_kickstart` |
| `proxmox_automatic_files_dir` | str | `kickstart-files` |
| `proxmox_automatic_iso_dir` | str | `kickstart-isos` |
| `proxmox_automatic_iso_build_dir` | str | `{{ proxmox_automatic_iso_dir }}/build` |
| `proxmox_automatic_first_disk_size` | str | `20` |
| `proxmox_automatic_pve_iso_storage` | str | `cephfs` |
| `proxmox_automatic_pve_vm_storage` | str | `volumes` |
| `proxmox_automatic_defaultbridge` | str | `vmbr1` |
| `proxmox_automatic_iso_name` | str | `rocky9.6-ks` |
| `proxmox_automatic_source_iso_name` | str | `{{ proxmox_automatic_iso_name }}` |
| `proxmox_automatic_source_iso_path` | str | `` |
| `proxmox_automatic_generated_iso_name` | str | `` |
| `proxmox_automatic_install_source` | str | `online` |
| `proxmox_automatic_kickstart_template` | str | `kickstart.cfg.j2` |
| `proxmox_automatic_preseed_template` | str | `preseed.cfg.j2` |
| `proxmox_automatic_skip_iso_upload` | bool | `False` |
| `proxmox_automatic_efi_pre_enrolled_keys` | str | `{{ proxmox_automatic_installer_backend != 'debian13_preseed' }}` |
| `proxmox_automatic_vga` | str | `{{ 'std' if proxmox_automatic_installer_backend == 'debian13_preseed' else 'default' }}` |
| `proxmox_automatic_hotplug` | str | `network,disk,cpu,memory,usb` |
| `proxmox_automatic_debian_suite` | str | `trixie` |
| `proxmox_automatic_debian_mirror` | str | `deb.debian.org` |
| `proxmox_automatic_debian_mirror_directory` | str | `/debian` |
| `proxmox_automatic_debian_security_host` | str | `security.debian.org` |
| `proxmox_automatic_debian_tasksel` | list | `0 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_debian_packages_default` | list | `7 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_debian_interface_prefix` | str | `ens` |
| `proxmox_automatic_debian_interface_index_start` | int | `18` |
| `proxmox_automatic_debian_partition_recipe_override` | str | `` |
| `proxmox_automatic_debian_late_command_extra` | list | `0 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_debian_disable_network_manager` | bool | `True` |
| `proxmox_automatic_debian_root_login` | bool | `False` |
| `proxmox_automatic_debian_purge_microcode` | bool | `True` |
| `proxmox_automatic_api_user` | str | `svc_ansible_rw@pam` |
| `proxmox_automatic_api_password` | str | `<filleme>` |
| `proxmox_automatic_api_validate_certs` | bool | `True` |
| `proxmox_automatic_timezone` | str | `Europe/Berlin` |
| `proxmox_automatic_ntp_servers` | list | `4 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_dns_servers` | list | `2 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_ipv6_enabled` | bool | `False` |
| `proxmox_automatic_ipv6_dns_servers` | list | `0 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_ssh_port` | int | `22` |
| `proxmox_automatic_additional_hosts` | list | `0 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_ha_enabled` | bool | `True` |
| `proxmox_automatic_ha_group_manage` | bool | `True` |
| `proxmox_automatic_ha_group_auto` | bool | `True` |
| `proxmox_automatic_ha_group` | str | `` |
| `proxmox_automatic_ha_group_nodes` | str | `` |
| `proxmox_automatic_ha_group_restricted` | bool | `False` |
| `proxmox_automatic_ha_group_comment` | str | `` |
| `proxmox_automatic_ha_state` | str | `started` |
| `proxmox_automatic_ha_max_restart` | int | `1` |
| `proxmox_automatic_ha_max_relocate` | int | `1` |
| `proxmox_automatic_ha_comment` | str | `` |
| `proxmox_automatic_sysctl_settings` | dict | `4 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_ipv6_sysctl_settings` | dict | `5 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_keyboard_layout` | str | `de` |
| `proxmox_automatic_keyboard_variants` | str | `de (nodeadkeys),us` |
| `proxmox_automatic_language` | str | `en_US.UTF-8` |
| `proxmox_automatic_selinux_mode` | str | `enforcing` |
| `proxmox_automatic_firewall_enabled` | bool | `True` |
| `proxmox_automatic_firewall_services` | list | `1 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_enabled_services` | list | `4 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_disabled_services` | list | `0 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_dhcp_enabled` | bool | `False` |
| `proxmox_automatic_package_retries` | int | `5` |
| `proxmox_automatic_package_timeout` | int | `20` |
| `proxmox_automatic_install_languages` | str | `en` |
| `proxmox_automatic_minimal_environment` | str | `@^minimal-environment` |
| `proxmox_automatic_vcpu` | int | `2` |
| `proxmox_automatic_memory` | int | `2048` |
| `proxmox_automatic_users` | list | `0 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_url_baseos` | str | `` |
| `proxmox_automatic_url_mirrorlist` | str | `http://mirrors.rockylinux.org/mirrorlist?arch=x86_64&repo=BaseOS-9` |
| `proxmox_automatic_repos` | list | `4 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_storage_config_defaults` | list | `1 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_packages_default_rocky_kickstart` | list | `6 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_packages_default` | list | `0 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_packages_additional` | list | `0 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_networks` | list | `0 Einträge; siehe defaults/main.yml` |
| `proxmox_automatic_create_vm_throttle` | int | `3` |
| `proxmox_automatic_create_vm_retries` | int | `3` |
| `proxmox_automatic_create_vm_retry_delay` | int | `5` |
| `proxmox_automatic_create_vm_pause` | int | `3` |
| `proxmox_automatic_start_vm_throttle` | int | `3` |
| `proxmox_automatic_start_vm_retries` | int | `3` |
| `proxmox_automatic_start_vm_retry_delay` | int | `3` |
| `proxmox_automatic_start_vm_pause` | int | `5` |

Die expliziten Legacy-Layer für Disks, Netze und Benutzer (`_defaults`, `_group_vars`, `_host_vars`, `_playbook`) werden anhand von `name` zusammengeführt. Listen in der strukturierten API werden gemäß normaler Ansible-Variablenpriorität ersetzt.

Zusätzliche kompatible Skalare ohne eigenen Default: `proxmox_automatic_api_host`, `proxmox_automatic_hypervisor`, `proxmox_automatic_vmid`, `proxmox_automatic_api_token_id`, `proxmox_automatic_api_token_secret`, `proxmox_automatic_cpu_type`, `proxmox_automatic_sockets`, `proxmox_automatic_machine`, `proxmox_automatic_kvm`, `proxmox_automatic_onboot`, `proxmox_automatic_os_type`, `proxmox_automatic_scsi_hw`, `proxmox_automatic_hostpci`, `proxmox_automatic_vm_pool` und `proxmox_automatic_storage`.

Entfernte Optionen werden im [Migrationsabschnitt](README.md#migration-und-abnahme) aufgeführt.
