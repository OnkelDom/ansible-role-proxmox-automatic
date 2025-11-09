# Variable Reference - proxmox_automatic

Complete documentation of all configuration variables for the `proxmox_automatic` Ansible role.

> **📖 Quick Links:** [Main README](README.md) | [Examples](README.md#-examples)

## Table of Contents

- [Core Configuration](#core-configuration)
- [Proxmox API Configuration](#proxmox-api-configuration)
- [VM Configuration](#vm-configuration)
- [Storage Configuration](#storage-configuration)
- [Network Configuration](#network-configuration)
- [Boot Configuration](#boot-configuration)
- [System Configuration](#system-configuration)
- [Security Configuration](#security-configuration)
- [User Management](#user-management)
- [Host Management](#host-management)
- [SMTP Configuration](#smtp-configuration)
- [Services Configuration](#services-configuration)
- [Package Management](#package-management)
- [High Availability Configuration](#high-availability-configuration)
- [Repository Configuration](#repository-configuration)
- [System Tuning](#system-tuning)
- [Pool Management](#pool-management)
- [Performance Tuning](#performance-tuning)

---

## Core Configuration

##### `proxmox_automatic_install_dependencies`
**Default:** `false`  
**Description:** Automatically install dependencies (xorriso, syslinux) on Ansible Controller

**Example:**
```yaml
proxmox_automatic_install_dependencies: true
```

##### `proxmox_automatic_files_dir`
**Default:** `"kickstart-files"`  
**Description:** Path for Kickstart files

**Example:**
```yaml
proxmox_automatic_files_dir: "/tmp/ks-files"
```

##### `proxmox_automatic_iso_dir`
**Default:** `"kickstart-isos"`  
**Description:** Path for generated ISO files

**Example:**
```yaml
proxmox_automatic_iso_dir: "/var/lib/isos"
```

##### `proxmox_automatic_iso_name`
**Default:** `"rocky9.6-ks"`  
**Description:** Name of the Kickstart ISO file (without .iso)

**Example:**
```yaml
proxmox_automatic_iso_name: "rocky9-custom"
```

### Proxmox API Configuration

##### `proxmox_automatic_api_host`
**Default:** *required*  
**Description:** FQDN or IP of the Proxmox API host

**Example:**
```yaml
proxmox_automatic_api_host: "pve.example.com"
```

##### `proxmox_automatic_api_user`
**Default:** `"svc_ansible_rw@pam"`  
**Description:** Username for Proxmox API

**Example:**
```yaml
proxmox_automatic_api_user: "ansible@pve"
```

##### `proxmox_automatic_api_password`
**Default:** *required*  
**Description:** Password for Proxmox API

**Example:**
```yaml
proxmox_automatic_api_password: "{{ vault_proxmox_password }}"
```

##### `proxmox_automatic_api_validate_certs`
**Default:** `false`  
**Description:** Validate SSL certificates for Proxmox API connections. Set to `false` by default since most Proxmox installations use self-signed certificates.

**Example:**
```yaml
proxmox_automatic_api_validate_certs: true  # Enable certificate validation
```

### VM Configuration

##### `proxmox_automatic_vmid`
**Default:** *optional*  
**Description:** Proxmox VM ID

**Example:**
```yaml
proxmox_automatic_vmid: 101
```

##### `proxmox_automatic_hypervisor`
**Default:** *required*  
**Description:** Proxmox Node (e.g. srv-hyp-01.local)

**Example:**
```yaml
proxmox_automatic_hypervisor: "pve-node1"
```

##### `proxmox_automatic_memory`
**Default:** `2048`  
**Description:** VM RAM in MB

**Example:**
```yaml
proxmox_automatic_memory: 4096
```

##### `proxmox_automatic_vcpu`
**Default:** `2`  
**Description:** Number of vCPUs

**Example:**
```yaml
proxmox_automatic_vcpu: 4
```

##### `proxmox_automatic_cpu_type`
**Default:** `"x86-64-v3"`  
**Description:** CPU type

**Example:**
```yaml
proxmox_automatic_cpu_type: "host"
```

##### `proxmox_automatic_sockets`
**Default:** `1`  
**Description:** Number of CPU sockets

**Example:**
```yaml
proxmox_automatic_sockets: 2
```

##### `proxmox_automatic_state`
**Default:** `"present"`  
**Description:** VM state

**Choices:** `["present", "absent"]`

**Example:**
```yaml
proxmox_automatic_state: "absent"  # To delete VM
```

##### `proxmox_automatic_kvm`
**Default:** `true`  
**Description:** Enable KVM

**Example:**
```yaml
proxmox_automatic_kvm: false  # For nested virtualization issues
```

##### `proxmox_automatic_os_type`
**Default:** `"l26"`  
**Description:** Operating system type

**Example:**
```yaml
proxmox_automatic_os_type: "l26"  # Linux 2.6+ kernel
```

##### `proxmox_automatic_onboot`
**Default:** `true`  
**Description:** Enable autostart

**Example:**
```yaml
proxmox_automatic_onboot: false
```

##### `proxmox_automatic_scsi_hw`
**Default:** `"virtio-scsi-single"`  
**Description:** SCSI controller type

**Example:**
```yaml
proxmox_automatic_scsi_hw: "virtio-scsi-pci"
```

##### `proxmox_automatic_machine`
**Default:** `"q35"`  
**Description:** Machine type

**Example:**
```yaml
proxmox_automatic_machine: "pc-i440fx-8.0"
```

##### `proxmox_automatic_hotplug`
**Default:** `"disk"`  
**Description:** Hotplug configuration

**Example:**
```yaml
proxmox_automatic_hotplug: "disk,network,usb"
```

### Storage Configuration

##### `proxmox_automatic_storage`
**Default:** *optional*  
**Description:** Optional: Override storage for VM and ISO

**Example:**
```yaml
proxmox_automatic_storage: "local-lvm"
```

##### `proxmox_automatic_pve_iso_storage`
**Default:** `"cephfs"`  
**Description:** Proxmox storage for ISOs

**Example:**
```yaml
proxmox_automatic_pve_iso_storage: "local"
```

##### `proxmox_automatic_pve_vm_storage`
**Default:** `"volumes"`  
**Description:** Proxmox storage for VM disks

**Example:**
```yaml
proxmox_automatic_pve_vm_storage: "ceph-rbd"
```

##### `proxmox_automatic_first_disk_size`
**Default:** `"20"`  
**Description:** Size of first disk in GB (number only)

**Example:**
```yaml
proxmox_automatic_first_disk_size: "50"
```

##### `proxmox_automatic_storage_config_defaults`
**Default:** `[]`  
**Description:** Default storage configuration for disks

**Supports hierarchical configuration:** This variable works together with `proxmox_automatic_storage_config_group_vars` and `proxmox_automatic_storage_config_host_vars` to create a complete storage layout.

**Example:**
```yaml
# Standard system disk for all VMs
proxmox_automatic_storage_config_defaults:
  - name: virtio0
    size: "20"
    disk: vda
    bootloader: true
    vg:
      - name: system
        lv:
          - name: root
            mount: /
            size: 8192
            fstype: xfs
          - name: swap
            mount: swap
            size: 2048
            fstype: swap
          - name: home
            mount: /home
            size: 1024
            grow: true
            fstype: xfs
```

**Group-specific storage additions:**
```yaml
# group_vars/databases.yml
proxmox_automatic_storage_config_group_vars:
  - name: virtio1
    size: "100"
    disk: vdb
    vg:
      - name: data
        lv:
          - name: mysql
            mount: /var/lib/mysql
            size: 1024
            grow: true
            fstype: xfs
```

**Host-specific storage:**
```yaml
# host_vars/db-master.yml
proxmox_automatic_storage_config_host_vars:
  - name: virtio2
    size: "200"
    disk: vdc
    vg:
      - name: backup
        lv:
          - name: backups
            mount: /backups
            size: 1024
            grow: true
            fstype: xfs
```

##### `proxmox_automatic_disks`
**Default:** `[]`  
**Description:** List of additional disks (name, size, storage)

**Example:**
```yaml
proxmox_automatic_disks:
  - name: virtio1
    size: "100"
    storage: "ceph-rbd"
  - name: virtio2
    size: "50"
    storage: "local-lvm"
```

### Network Configuration

##### `proxmox_automatic_defaultbridge`
**Default:** `"vmbr1"`  
**Description:** Default bridge for network cards

**Example:**
```yaml
proxmox_automatic_defaultbridge: "vmbr0"
```

##### `proxmox_automatic_networks`
**Default:** `[]`  
**Description:** List of network interfaces with static IP configuration (bridge, vlanid, ip, netmask, gateway, mtu, mac, model, ipv6, ipv6_gateway)

**Example:**
```yaml
proxmox_automatic_networks:
  - name: net0
    bridge: vmbr0
    ip: "192.168.1.10"
    netmask: "255.255.255.0"
    gateway: "192.168.1.1"
    vlanid: 100
    mtu: 1500
  - name: net1
    bridge: vmbr1
    ip: "10.0.0.10"
    netmask: "255.255.255.0"
    vlanid: 200
    model: "virtio"
```

**Supports hierarchical configuration:**
```yaml
# defaults/main.yml
proxmox_automatic_networks_defaults:
  - name: net0
    bridge: vmbr0
    ip: "192.168.1.10"
    netmask: "255.255.255.0"
    gateway: "192.168.1.1"

# group_vars/webservers.yml
proxmox_automatic_networks_group_vars:
  - name: net1
    bridge: vmbr1
    ip: "10.10.10.10"
    netmask: "255.255.255.0"
    vlanid: 100  # Web VLAN

# host_vars/web01.yml
proxmox_automatic_networks_host_vars:
  - name: net2
    bridge: vmbr2
    ip: "10.0.0.10"
    netmask: "255.255.255.0"
    vlanid: 999  # Management VLAN
```

##### `proxmox_automatic_dhcp_enabled`
**Default:** `false`  
**Description:** Enable DHCP for network configuration. When true, static IPs are ignored.

**Example:**
```yaml
proxmox_automatic_dhcp_enabled: true
```

##### `proxmox_automatic_dns_servers`
**Default:** `["1.0.0.1", "1.1.1.1"]`  
**Description:** List of DNS servers

**Example:**
```yaml
proxmox_automatic_dns_servers:
  - "8.8.8.8"
  - "8.8.4.4"
  - "1.1.1.1"
```

##### `proxmox_automatic_ipv6_enabled`
**Default:** `false`  
**Description:** Enable IPv6 support. When enabled, VMs will be configured with IPv6 addresses and routing.

**Example:**
```yaml
proxmox_automatic_ipv6_enabled: true
```

##### `proxmox_automatic_ipv6_dns_servers`
**Default:** `[]`  
**Description:** List of IPv6 DNS servers (used when IPv6 is enabled)

**Example:**
```yaml
proxmox_automatic_ipv6_dns_servers:
  - "2606:4700:4700::1111"
  - "2606:4700:4700::1001"
  - "2001:4860:4860::8888"
```

**Note:** When configuring IPv6 for network interfaces, add `ipv6` and optionally `ipv6_gateway` to your network configuration:

```yaml
proxmox_automatic_networks:
  - name: net0
    bridge: vmbr0
    ip: "192.168.1.10"
    netmask: "255.255.255.0"
    gateway: "192.168.1.1"
    ipv6: "2001:db8::10/64"
    ipv6_gateway: "2001:db8::1"
```

If `ipv6` is not specified but `proxmox_automatic_ipv6_enabled` is `true`, IPv6 will be configured using autoconfiguration (SLAAC).

##### `proxmox_automatic_ipv6_sysctl_settings`
**Default:**
```yaml
proxmox_automatic_ipv6_sysctl_settings:
  net.ipv6.conf.all.forwarding: 1
  net.ipv6.conf.all.accept_ra: 0
  net.ipv6.conf.default.accept_ra: 0
  net.ipv6.conf.all.accept_redirects: 0
  net.ipv6.conf.default.accept_redirects: 0
```
**Description:** Sysctl settings applied when IPv6 is enabled

### Boot Configuration

##### `proxmox_automatic_boot_order`
**Default:** `1`  
**Description:** Boot order

**Example:**
```yaml
proxmox_automatic_boot_order: 2
```

##### `proxmox_automatic_boot_order_up_wait`
**Default:** `3`  
**Description:** Wait time after start (seconds)

**Example:**
```yaml
proxmox_automatic_boot_order_up_wait: 10
```

##### `proxmox_automatic_boot_order_down_wait`
**Default:** `3`  
**Description:** Wait time after shutdown (seconds)

**Example:**
```yaml
proxmox_automatic_boot_order_down_wait: 5
```

### System Configuration

##### `proxmox_automatic_timezone`
**Default:** `"Europe/Berlin"`  
**Description:** VM timezone

**Example:**
```yaml
proxmox_automatic_timezone: "America/New_York"
```

##### `proxmox_automatic_language`
**Default:** `"en_US.UTF-8"`  
**Description:** System language

**Example:**
```yaml
proxmox_automatic_language: "de_DE.UTF-8"
```

##### `proxmox_automatic_keyboard_layout`
**Default:** `"de"`  
**Description:** Keyboard layout

**Example:**
```yaml
proxmox_automatic_keyboard_layout: "us"
```

##### `proxmox_automatic_keyboard_variants`
**Default:** `"de (nodeadkeys),us"`  
**Description:** Keyboard variants

**Example:**
```yaml
proxmox_automatic_keyboard_variants: "us,de"
```

##### `proxmox_automatic_ntp_servers`
**Default:** `["0.de.pool.ntp.org", "1.de.pool.ntp.org", "2.de.pool.ntp.org", "3.de.pool.ntp.org"]`  
**Description:** List of NTP servers

**Example:**
```yaml
proxmox_automatic_ntp_servers:
  - "0.pool.ntp.org"
  - "1.pool.ntp.org"
  - "time.google.com"
```

##### `proxmox_automatic_selinux_mode`
**Default:** `"enforcing"`  
**Description:** SELinux mode

**Choices:** `["enforcing", "permissive", "disabled"]`

**Example:**
```yaml
proxmox_automatic_selinux_mode: "permissive"
```

### Security Configuration

##### `proxmox_automatic_firewall_enabled`
**Default:** `true`  
**Description:** Enable firewall

**Example:**
```yaml
proxmox_automatic_firewall_enabled: false
```

##### `proxmox_automatic_firewall_services`
**Default:** `["ssh"]`  
**Description:** Firewall services to allow

**Example:**
```yaml
proxmox_automatic_firewall_services:
  - "ssh"
  - "http"
  - "https"
  - "mysql"
```

##### `proxmox_automatic_ssh_port`
**Default:** `22`  
**Description:** SSH port for the VM

**Example:**
```yaml
proxmox_automatic_ssh_port: 2222
```

### User Management

##### `proxmox_automatic_users`
**Default:** `[]`  
**Description:** List of users to be created during installation

**Supports hierarchical configuration:** This variable works together with `proxmox_automatic_users_defaults`, `proxmox_automatic_users_group_vars`, and `proxmox_automatic_users_host_vars`.

**Example:**
```yaml
# Standard users for all VMs
proxmox_automatic_users_defaults:
  root:
    password: "$6$rounds=656000$salt$hash"
    ssh_key: "ssh-rsa AAAA..."

# Group-specific users
proxmox_automatic_users_group_vars:
  webadmin:
    password: "$6$rounds=656000$salt$hash"
    groups: ["wheel", "apache"]
    shell: "/bin/bash"
    home: "/home/webadmin"

# Host-specific users
proxmox_automatic_users_host_vars:
  developer:
    password: "$6$rounds=656000$salt$hash"
    groups: ["wheel"]
    ssh_key: "ssh-rsa AAAA...developer-key"
```

##### `proxmox_automatic_service_user`
**Default:** `"ansible"`  
**Description:** Ansible service account created in the target system

**Example:**
```yaml
proxmox_automatic_service_user: "automation"
```

##### `proxmox_automatic_service_password`
**Default:** `""`  
**Description:** Password for the Ansible service account

**Example:**
```yaml
proxmox_automatic_service_password: "{{ vault_service_password }}"
```

##### `proxmox_automatic_service_ssh_key`
**Default:** `""`  
**Description:** SSH public key for the Ansible service account

**Example:**
```yaml
proxmox_automatic_service_ssh_key: "ssh-rsa AAAA...ansible-controller-key"
```

##### `proxmox_automatic_service_gecos`
**Default:** `"Ansible Serviceaccount"`  
**Description:** Comment/GECOS for the Ansible service account

**Example:**
```yaml
proxmox_automatic_service_gecos: "Automation Service Account"
```

### Host Management

##### `proxmox_automatic_host_description`
**Default:** `"Managed by Ansible"`  
**Description:** Host description

**Example:**
```yaml
proxmox_automatic_host_description: "Web Server - Production"
```

##### `proxmox_automatic_host_responsible`
**Default:** `"admin@example.com"`  
**Description:** Person responsible for the host

**Example:**
```yaml
proxmox_automatic_host_responsible: "webteam@company.com"
```

##### `proxmox_automatic_additional_hosts`
**Default:** `[]`  
**Description:** Additional hosts entries for /etc/hosts

**Example:**
```yaml
proxmox_automatic_additional_hosts:
  - ip: "10.1.1.50"
    hostname: "db.internal.com"
    aliases: ["database", "mysql"]
  - ip: "10.1.1.60"
    hostname: "cache.internal.com"
```

### SMTP Configuration

##### `proxmox_automatic_smtp_host`
**Default:** `"smtp.example.com"`  
**Description:** SMTP server for email delivery

**Example:**
```yaml
proxmox_automatic_smtp_host: "mail.company.com"
```

##### `proxmox_automatic_smtp_port`
**Default:** `587`  
**Description:** SMTP port

**Example:**
```yaml
proxmox_automatic_smtp_port: 25
```

##### `proxmox_automatic_smtp_from`
**Default:** `"noreply@example.com"`  
**Description:** Sender email address

**Example:**
```yaml
proxmox_automatic_smtp_from: "system@company.com"
```

##### `proxmox_automatic_smtp_user`
**Default:** `"<fillme>"`  
**Description:** SMTP username

**Example:**
```yaml
proxmox_automatic_smtp_user: "{{ vault_smtp_user }}"
```

##### `proxmox_automatic_smtp_password`
**Default:** `"<fillme>"`  
**Description:** SMTP password

**Example:**
```yaml
proxmox_automatic_smtp_password: "{{ vault_smtp_password }}"
```

##### `proxmox_automatic_smtp_root`
**Default:** `"<fillme>"`  
**Description:** Email address for root notifications

**Example:**
```yaml
proxmox_automatic_smtp_root: "sysadmin@company.com"
```

### Services Configuration

##### `proxmox_automatic_enabled_services`
**Default:** `["sshd", "rsyslog", "chronyd", "NetworkManager"]`  
**Description:** Services to enable at boot

**Example:**
```yaml
proxmox_automatic_enabled_services:
  - "sshd"
  - "httpd"
  - "mysqld"
  - "chronyd"
```

##### `proxmox_automatic_disabled_services`
**Default:** `[]`  
**Description:** Services to disable

**Example:**
```yaml
proxmox_automatic_disabled_services:
  - "postfix"
  - "cups"
  - "bluetooth"
```

### Package Management

##### `proxmox_automatic_packages_default`
**Default:** `[]` (populated with base system packages in defaults/main.yml)  
**Description:** Default packages installed on all VMs (base system). This list contains essential tools, network utilities, monitoring tools, etc. that are installed on every VM.

**Default includes:**
- Essential system packages (bash-completion, curl, git, vim, etc.)
- Network & Debug tools (bind-utils, tcpdump, nmap, etc.)
- Monitoring & Diagnosis tools (htop, iotop, tmux, etc.)
- Mail tools (msmtp, s-nail)

**Example (override defaults):**
```yaml
proxmox_automatic_packages_default:
  - "bash-completion"
  - "vim"
  - "git"
  - "curl"
  - "htop"
```

##### `proxmox_automatic_packages_additional`
**Default:** `[]`  
**Description:** Additional packages specific to groups or individual hosts. Use this to add role-specific packages without modifying the base package list.

**Example:**
```yaml
# group_vars/webservers.yml
proxmox_automatic_packages_additional:
  - "httpd"
  - "php"
  - "php-mysqlnd"

# host_vars/db01.yml
proxmox_automatic_packages_additional:
  - "mariadb-server"
  - "mariadb-client"
```

##### `proxmox_automatic_package_retries`
**Default:** `5`  
**Description:** Number of retries for package installation

**Example:**
```yaml
proxmox_automatic_package_retries: 3
```

##### `proxmox_automatic_package_timeout`
**Default:** `20`  
**Description:** Timeout for package installation (seconds)

**Example:**
```yaml
proxmox_automatic_package_timeout: 60
```

##### `proxmox_automatic_minimal_environment`
**Default:** `"@^minimal-environment"`  
**Description:** Minimal environment for installation

**Example:**
```yaml
proxmox_automatic_minimal_environment: "@^server-product-environment"
```

##### `proxmox_automatic_install_languages`
**Default:** `"en"`  
**Description:** Installed language packages

**Example:**
```yaml
proxmox_automatic_install_languages: "en de fr"
```

##### `proxmox_automatic_dnf_automatic_enabled`
**Default:** `true`  
**Description:** Enable automatic DNF updates using dnf-automatic

**Example:**
```yaml
proxmox_automatic_dnf_automatic_enabled: false
```

##### `proxmox_automatic_dnf_recipients`
**Default:** `["support@{{ proxmox_automatic_smtp_from.split('@')[1] }}"]`  
**Description:** List of email recipients for DNF automatic update notifications

**Example:**
```yaml
proxmox_automatic_dnf_recipients:
  - "sysadmin@example.com"
  - "monitoring@example.com"
```

### High Availability Configuration

##### `proxmox_automatic_ha_enabled`
**Default:** `true`  
**Description:** Enable High Availability for the VM. When enabled, the VM will be added to a Proxmox HA group.

**Example:**
```yaml
proxmox_automatic_ha_enabled: false  # Disable HA
```

##### `proxmox_automatic_ha_group_manage`
**Default:** `true`  
**Description:** Automatically create/manage the HA group if it doesn't exist. When enabled, the role will ensure the HA group is created with the specified configuration before adding VMs to it.

**Example:**
```yaml
proxmox_automatic_ha_group_manage: false  # Use existing HA groups only
```

##### `proxmox_automatic_ha_group_auto`
**Default:** `true`  
**Description:** Automatically generate one HA group per hypervisor. Each VM will be assigned to the HA group of its hypervisor with that node as primary (priority 0). Group names follow the pattern `ha-group-<hypervisor>` (e.g., `ha-group-srv-hyp-01`).

**How it works:**
- Collects all unique hypervisors from the play
- Creates one HA group per hypervisor
- Primary node (where VMs run) gets priority 0
- Other cluster nodes get ascending priorities (1, 2, 3, ...)
- VMs automatically join their hypervisor's HA group

**Example:**
```yaml
proxmox_automatic_ha_group_auto: false  # Use manual HA group assignment
```

##### `proxmox_automatic_ha_group`
**Default:** `""`  
**Description:** Name of the HA group to assign the VM to. If `proxmox_automatic_ha_group_manage` is `false`, the group must already exist in the Proxmox cluster.

**Example:**
```yaml
proxmox_automatic_ha_group: "ha-group-production"
```

##### `proxmox_automatic_ha_group_nodes`
**Default:** `""`  
**Description:** Comma-separated list of Proxmox nodes with their priorities for the HA group. Lower priority values indicate preferred nodes (0 = most preferred). Only used when `proxmox_automatic_ha_group_manage` is `true`.

**Format:** `"node1:priority1,node2:priority2,node3:priority3"`

**Example:**
```yaml
proxmox_automatic_ha_group_nodes: "pve-node1:0,pve-node2:1,pve-node3:2"
```

##### `proxmox_automatic_ha_group_nofailback`
**Default:** `false`  
**Description:** If true, the HA manager won't automatically migrate resources back to higher-priority nodes after they become available again. Only used when managing the HA group.

**Example:**
```yaml
proxmox_automatic_ha_group_nofailback: true
```

##### `proxmox_automatic_ha_group_restricted`
**Default:** `false`  
**Description:** If true, only resources assigned to this HA group can run on the specified nodes. Only used when managing the HA group.

**Example:**
```yaml
proxmox_automatic_ha_group_restricted: true
```

##### `proxmox_automatic_ha_group_comment`
**Default:** `""`  
**Description:** Optional comment for the HA group. Only used when managing the HA group.

**Example:**
```yaml
proxmox_automatic_ha_group_comment: "Production HA group for critical services"
```

##### `proxmox_automatic_ha_state`
**Default:** `"started"`  
**Description:** Desired state of the HA resource. Available states:
- `started`: Resource should be running
- `stopped`: Resource should be stopped
- `disabled`: Resource is not managed by HA
- `ignored`: Resource is ignored by HA manager

**Example:**
```yaml
proxmox_automatic_ha_state: "started"
```

##### `proxmox_automatic_ha_max_restart`
**Default:** `1`  
**Description:** Maximum number of restart attempts after a service start failure on the same node.

**Example:**
```yaml
proxmox_automatic_ha_max_restart: 3
```

##### `proxmox_automatic_ha_max_relocate`
**Default:** `1`  
**Description:** Maximum number of service relocation attempts when a service fails to start. After this many relocations, the service will be placed in an error state.

**Example:**
```yaml
proxmox_automatic_ha_max_relocate: 2
```

##### `proxmox_automatic_ha_comment`
**Default:** `""`  
**Description:** Optional comment for the HA resource.

**Example:**
```yaml
proxmox_automatic_ha_comment: "Production database server"
```

### Repository Configuration

##### `proxmox_automatic_repos`
**Default:** `[]`  
**Description:** List of additional repositories

**Example:**
```yaml
proxmox_automatic_repos:
  - name: "epel"
    baseurl: "https://download.fedoraproject.org/pub/epel/9/Everything/$basearch/"
    gpgcheck: true
    gpgkey: "https://download.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-9"
```

##### `proxmox_automatic_url_baseurl`
**Default:** `""`  
**Description:** Base URL for Rocky Linux (e.g. http://mirror.example.com/rocky/9/updates/x86_64/Packages/)

**Example:**
```yaml
proxmox_automatic_url_baseurl: "http://mirror.local.com/rocky/9/"
```

##### `proxmox_automatic_url_baseos`
**Default:** `""`  
**Description:** BaseOS URL (optional)

**Example:**
```yaml
proxmox_automatic_url_baseos: "http://mirror.local.com/rocky/9/BaseOS/"
```

##### `proxmox_automatic_url_mirrorlist`
**Default:** `"http://mirrors.rockylinux.org/mirrorlist?arch=$basearch&repo=BaseOS-$releasever"`  
**Description:** Mirrorlist URL for Rocky Linux BaseOS

**Example:**
```yaml
proxmox_automatic_url_mirrorlist: "http://internal-mirror.com/rocky/mirrorlist"
```

### System Tuning

##### `proxmox_automatic_sysctl_settings`
**Default:**
```yaml
proxmox_automatic_sysctl_settings:
  net.ipv4.ip_forward: 1
  net.ipv4.conf.all.rp_filter: 1
  vm.swappiness: 10
  vm.vfs_cache_pressure: 50
```
**Description:** Sysctl settings for better network performance

**Example:**
```yaml
proxmox_automatic_sysctl_settings:
  net.ipv4.tcp_congestion_control: "bbr"
  net.core.rmem_max: 16777216
  net.core.wmem_max: 16777216
  vm.swappiness: 10
```

### Pool Management

##### `proxmox_automatic_vm_pool`
**Default:** `"omit"`  
**Description:** Optional pool where the VM will be registered. The role automatically creates the pool if it doesn't exist before VM creation. Pools are useful for organizing VMs and applying permissions.

**Example:**
```yaml
# group_vars/production.yml
proxmox_automatic_vm_pool: "production"

# group_vars/development.yml
proxmox_automatic_vm_pool: "development"
```

**Note:** 
- Pools are automatically created before VMs if they don't exist
- Multiple VMs can share the same pool
- If set to `"omit"` or empty, no pool will be assigned

### Performance Tuning

##### `proxmox_automatic_create_vm_throttle`
**Default:** `3`  
**Description:** Number of concurrent VM creations

**Example:**
```yaml
proxmox_automatic_create_vm_throttle: 5
```

##### `proxmox_automatic_create_vm_retries`
**Default:** `3`  
**Description:** Retries for VM creation

**Example:**
```yaml
proxmox_automatic_create_vm_retries: 5
```

##### `proxmox_automatic_create_vm_retry_delay`
**Default:** `5`  
**Description:** Delay between retries (seconds)

**Example:**
```yaml
proxmox_automatic_create_vm_retry_delay: 10
```

##### `proxmox_automatic_create_vm_pause`
**Default:** `3`  
**Description:** Pause after VM creation (seconds)

**Example:**
```yaml
proxmox_automatic_create_vm_pause: 5
```

##### `proxmox_automatic_start_vm_throttle`
**Default:** `3`  
**Description:** Number of concurrent VM starts

**Example:**
```yaml
proxmox_automatic_start_vm_throttle: 2
```

##### `proxmox_automatic_start_vm_retries`
**Default:** `3`  
**Description:** Retries for VM start

**Example:**
```yaml
proxmox_automatic_start_vm_retries: 5
```

##### `proxmox_automatic_start_vm_retry_delay`
**Default:** `3`  
**Description:** Delay between start retries (seconds)

**Example:**
```yaml
proxmox_automatic_start_vm_retry_delay: 5
```

##### `proxmox_automatic_start_vm_pause`
**Default:** `5`  
**Description:** Pause after VM start (seconds)

**Example:**
```yaml
proxmox_automatic_start_vm_pause: 10
```

##### `proxmox_automatic_enable_epel`
**Default:** `true`  
**Description:** Enable EPEL repository

##### `proxmox_automatic_epel_packages`
**Default:**
```yaml
proxmox_automatic_epel_packages:
  - epel-release
  - dstat
  - htop
  - iotop
  - tig
  - msmtp
  - msmtp-mta
  - p7zip
```
**Description:** List of EPEL packages to install
