# Ansible Role: proxmox_automatic

[![CI](https://github.com/lenhardt-its/ansible-role-proxmox-automatic/workflows/CI/badge.svg)](https://github.com/lenhardt-its/ansible-role-proxmox-automatic/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Ansible Galaxy](https://img.shields.io/badge/ansible--galaxy-proxmox__automatic-blue.svg)](https://galaxy.ansible.com/lenhardt-its/proxmox_automatic)
[![Ansible](https://img.shields.io/badge/ansible-2.14%2B-red.svg)](https://ansible.com)
[![GitHub release](https://img.shields.io/github/release/lenhardt-its/ansible-role-proxmox-automatic.svg)](https://github.com/lenhardt-its/ansible-role-proxmox-automatic/releases)

This role automatically creates virtual machines on a **Proxmox VE Cluster** with individual **Kickstart configurations**. It generates customized ISO files, uploads them to Proxmox, and starts VMs with complex storage and network configurations.

## 🚀 Features

- **Automatic Dependency Installation**: Installs `xorriso` and `syslinux` on various distributions
- **Hierarchical Configuration**: Defaults → group_vars → host_vars → Playbook variables
- **Dynamic Storage Configuration**: Multi-disk support with LVM and flexible sizes
- **Automatic Kickstart Generation**: Individual `.cfg` files per VM
- **ISO Management**: Automatic ISO creation and upload to Proxmox
- **Flexible User Configuration**: Hierarchical user management with SSH keys
- **Multi-Network Support**: Multiple network interfaces with VLAN support
- **Rocky Linux 9 Optimized**: Fixed repository URLs, modern interface names

## 📋 Requirements

### Proxmox VE
- API user with VM management permissions
- Storage for VMs and ISOs

### Ansible Controller Dependencies

**Automatic installation (recommended):**
```yaml
proxmox_automatic_install_dependencies: true
```

**Supported systems:**
- Red Hat family (RHEL, Rocky, CentOS, Fedora)
- Debian family (Debian, Ubuntu)
- macOS (via Homebrew)
- SUSE family (openSUSE, SLES)
- Arch family (Arch, Manjaro)

### Collections

**Required Ansible collections:**
```bash
ansible-galaxy collection install -r collections/requirements.yml
```

**Note:** This role uses the new `community.proxmox` collection.

## 📚 Quick Start

### Minimal Configuration

```yaml
# playbook.yml
- hosts: proxmox_vms
  roles:
    - lenhardt-its.proxmox_automatic
  vars:
    proxmox_automatic_api_host: "pve.example.com"
    proxmox_automatic_api_password: "your-api-password"
    proxmox_automatic_hypervisor: "pve-node1"
```

```ini
# inventory
[proxmox_vms]
web01 proxmox_automatic_vmid=101 ansible_host=10.1.1.10
db01 proxmox_automatic_vmid=102 ansible_host=10.1.1.20
```

### IPv6 Configuration Example

```yaml
# group_vars/all.yml
proxmox_automatic_ipv6_enabled: true
proxmox_automatic_ipv6_dns_servers:
  - "2606:4700:4700::1111"
  - "2606:4700:4700::1001"

# host_vars/web01.yml
proxmox_automatic_networks:
  - name: net0
    bridge: vmbr0
    ip: "192.168.1.10"
    netmask: "255.255.255.0"
    gateway: "192.168.1.1"
    ipv6: "2001:db8:1::10/64"
    ipv6_gateway: "2001:db8:1::1"
```

### High Availability Configuration Example

#### Option 1: Automatic HA per Hypervisor (Default & Recommended)

```yaml
# group_vars/all.yml or defaults
proxmox_automatic_ha_enabled: true          # Default: true
proxmox_automatic_ha_group_auto: true       # Default: true
proxmox_automatic_ha_group_manage: true     # Default: true

# Inventory
[proxmox_vms]
web01 proxmox_automatic_hypervisor=srv-hyp-01.local
web02 proxmox_automatic_hypervisor=srv-hyp-01.local
db01 proxmox_automatic_hypervisor=srv-hyp-02.local
db02 proxmox_automatic_hypervisor=srv-hyp-03.local
```

**Result:**
- HA group `ha-group-srv-hyp-01` created with srv-hyp-01 as primary
  - VMs: web01, web02
- HA group `ha-group-srv-hyp-02` created with srv-hyp-02 as primary
  - VMs: db01
- HA group `ha-group-srv-hyp-03` created with srv-hyp-03 as primary
  - VMs: db02

**Benefits:**
- ✅ VMs prefer their hypervisor (priority 0)
- ✅ Automatic failover to other cluster nodes
- ✅ Zero manual configuration needed
- ✅ One HA group per hypervisor

#### Option 2: Manual HA Group Assignment

```yaml
# group_vars/production.yml
proxmox_automatic_ha_enabled: true
proxmox_automatic_ha_group_auto: false      # Disable auto mode
proxmox_automatic_ha_group_manage: true
proxmox_automatic_ha_group: "ha-group-production"
proxmox_automatic_ha_group_nodes: "pve-node1:0,pve-node2:1,pve-node3:2"
proxmox_automatic_ha_group_nofailback: false
proxmox_automatic_ha_group_comment: "Production HA group - shared across all VMs"

# host_vars/db01.yml
proxmox_automatic_ha_comment: "Primary database server - critical service"
```

**Use case:** All VMs in a group should share the same HA configuration

#### Option 3: Using Existing HA Groups

```yaml
# group_vars/production.yml
proxmox_automatic_ha_enabled: true
proxmox_automatic_ha_group_auto: false      # Disable auto mode
proxmox_automatic_ha_group_manage: false    # Use existing groups
proxmox_automatic_ha_group: "ha-group-production"

# host_vars/db01.yml
proxmox_automatic_ha_comment: "Primary database server"
```

**Note:** The HA group must already exist in your Proxmox cluster:
- Proxmox Web UI: Datacenter → HA → Groups
- CLI: `ha-manager groupadd ha-group-production --nodes pve-node1:0,pve-node2:1`

#### Option 4: Disable HA

```yaml
# group_vars/development.yml
proxmox_automatic_ha_enabled: false
```

## 🎯 Understanding Hierarchical Configuration

This role uses an intelligent merge system that combines configurations from different levels:

**Priority Order (highest to lowest):**
```
Playbook variables → host_vars/ → group_vars/ → defaults/main.yml
```

### Storage Configuration Hierarchy

The role supports three levels of storage configuration:

- `proxmox_automatic_storage_config_defaults` - Base configuration
- `proxmox_automatic_storage_config_group_vars` - Group-specific additions
- `proxmox_automatic_storage_config_host_vars` - Host-specific configuration

**Example:**

```yaml
# defaults/main.yml - All VMs get this base disk
proxmox_automatic_storage_config_defaults:
  - name: virtio0
    size: "20"
    disk: vda
    bootloader: true

# group_vars/databases.yml - Database servers get additional storage
proxmox_automatic_storage_config_group_vars:
  - name: virtio0
    size: "40"  # Override base size
  - name: virtio1
    size: "200"  # Additional data disk

# host_vars/db01.yml - Specific host gets backup disk
proxmox_automatic_storage_config_host_vars:
  - name: virtio2
    size: "100"  # Backup storage
```

**Result:** `db01` will have 3 disks: 40GB system, 200GB data, 100GB backup.

### Package Configuration Hierarchy

Packages are split into two categories for maximum flexibility:

- `proxmox_automatic_packages_default` - Base packages installed on **all** VMs
- `proxmox_automatic_packages_additional` - Additional packages per group/host

**Example:**

```yaml
# defaults/main.yml - Base packages on all VMs
proxmox_automatic_packages_default:
  - bash-completion
  - vim
  - git
  - htop
  - tcpdump
  # ... many more essential tools

# group_vars/webservers.yml - Web-specific packages
proxmox_automatic_packages_additional:
  - httpd
  - php
  - php-mysqlnd

# host_vars/web01.yml - Host-specific package
proxmox_automatic_packages_additional:
  - php-redis  # Only web01 needs Redis
```

**Result:** All VMs get the base tools, webservers get PHP/Apache, web01 additionally gets php-redis.

### User Configuration Hierarchy

Similar hierarchical approach for users:

```yaml
# defaults/main.yml - Standard admin user
proxmox_automatic_users_defaults:
  root:
    password: "$6$encrypted_password"
    ssh_key: "ssh-rsa AAAA..."

# group_vars/webservers.yml - Web-specific service user
proxmox_automatic_users_group_vars:
  nginx:
    shell: "/bin/false"
    home: "/var/www"

# host_vars/web01.yml - Host-specific developer access
proxmox_automatic_users_host_vars:
  developer:
    password: "$6$dev_password"
    groups: ["wheel"]
```

### Network Configuration Hierarchy

```yaml
# defaults/main.yml - Standard network
proxmox_automatic_networks_defaults:
  - name: net0
    bridge: vmbr0

# group_vars/databases.yml - Database VLAN
proxmox_automatic_networks_group_vars:
  - name: net1
    bridge: vmbr1
    vlanid: 200

# host_vars/db01.yml - Additional management interface
proxmox_automatic_networks_host_vars:
  - name: net2
    bridge: vmbr2
    vlanid: 100
```

## 🛠️ Configuration

### Variable Documentation

For a complete list of all 96 configuration variables with detailed descriptions and examples, see **[VARIABLES.md](VARIABLES.md)**.

### Most Important Variables

**Required:**
- `proxmox_automatic_api_host` - Proxmox API host
- `proxmox_automatic_api_password` - Proxmox API password
- `proxmox_automatic_hypervisor` - Target Proxmox node

**Commonly Used:**
```yaml
# VM Resources
proxmox_automatic_memory: 2048          # RAM in MB
proxmox_automatic_vcpu: 2               # CPU cores

# Network
proxmox_automatic_networks:
  - name: net0
    bridge: vmbr0
    ip: "192.168.1.10"
    netmask: "255.255.255.0"
    gateway: "192.168.1.1"
    vlanid: 100

# Storage
proxmox_automatic_storage_config:
  - name: virtio0
    size: "20"
    disk: vda
    bootloader: true

# High Availability (enabled by default)
proxmox_automatic_ha_enabled: true      # Default: true
proxmox_automatic_ha_group_auto: true   # Auto HA group per hypervisor

# Packages
proxmox_automatic_packages_additional:
  - "httpd"
  - "php"
```

### Configuration Hierarchy

This role uses a powerful hierarchical configuration system:

```
defaults/main.yml  →  group_vars/  →  host_vars/  →  playbook vars
   (lowest)              (medium)       (higher)       (highest)
```

**Example:** Storage Configuration Merging
```yaml
# defaults/main.yml - Base disk for all VMs
proxmox_automatic_storage_config_defaults:
  - name: virtio0
    size: "20"

# group_vars/databases.yml - Additional disk for DB servers
proxmox_automatic_storage_config_group_vars:
  - name: virtio1
    size: "100"

# host_vars/db-master.yml - Extra disk for master only
proxmox_automatic_storage_config_host_vars:
  - name: virtio2
    size: "200"

# Result: db-master gets 3 disks (20GB + 100GB + 200GB)
```

## ⚙️ Quick Reference

### Variable Categories

| Category | Variables | Description |
|----------|-----------|-------------|
| **[Core](VARIABLES.md#core-configuration)** | 4 vars | Installation paths, dependencies |
| **[Proxmox API](VARIABLES.md#proxmox-api-configuration)** | 4 vars | API credentials, SSL validation |
| **[VM Config](VARIABLES.md#vm-configuration)** | 12 vars | CPU, RAM, boot settings |
| **[Storage](VARIABLES.md#storage-configuration)** | 5 vars | Disks, volumes, LVM |
| **[Network](VARIABLES.md#network-configuration)** | 10 vars | Interfaces, VLANs, IPv6 |
| **[Security](VARIABLES.md#security-configuration)** | 3 vars | Firewall, SELinux, SSH |
| **[Users](VARIABLES.md#user-management)** | 6 vars | Accounts, SSH keys |
| **[High Availability](VARIABLES.md#high-availability-configuration)** | 11 vars | HA groups, failover |
| **[Packages](VARIABLES.md#package-management)** | 7 vars | Software installation |
| **[Performance](VARIABLES.md#performance-tuning)** | 8 vars | Throttling, retries |

For detailed documentation of all variables, see **[VARIABLES.md](VARIABLES.md)**.

## 📚 Examples

### Database Server with Multiple Disks

```yaml
# host_vars/db01.yml
proxmox_automatic_memory: 8192
proxmox_automatic_vcpu: 4

# Storage hierarchy example
proxmox_automatic_storage_config_host_vars:
  - name: virtio0  # System disk
    size: "40"
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
            size: 4096
            fstype: swap
          - name: var
            mount: /var
            size: 4096
            fstype: xfs
          - name: tmp
            mount: /tmp
            size: 2048
            fstype: xfs
            
  - name: virtio1  # Database storage
    size: "200"
    disk: vdb
    vg:
      - name: database
        lv:
          - name: mysql
            mount: /var/lib/mysql
            size: 1024
            grow: true
            fstype: xfs
            
  - name: virtio2  # Log storage
    size: "50"
    disk: vdc
    vg:
      - name: logs
        lv:
          - name: mysqllogs
            mount: /var/log/mysql
            size: 1024
            grow: true
            fstype: xfs

# Network configuration
proxmox_automatic_networks_host_vars:
  - name: net1
    bridge: vmbr1
    ip: "10.10.20.10"
    netmask: "255.255.255.0"
    vlanid: 200  # Database VLAN

# Database-specific packages
proxmox_automatic_packages_additional:
  - "mariadb-server"
  - "mariadb-client"
  - "python3-pymysql"
```

### Web Server Cluster

```yaml
# group_vars/webservers.yml
proxmox_automatic_memory: 4096
proxmox_automatic_vcpu: 2

# Web servers get additional storage for content
proxmox_automatic_storage_config_group_vars:
  - name: virtio1
    size: "100"
    disk: vdb
    vg:
      - name: web
        lv:
          - name: www
            mount: /var/www
            size: 1024
            grow: true
            fstype: xfs

# Web VLAN
proxmox_automatic_networks_group_vars:
  - name: net1
    bridge: vmbr1
    ip: "10.10.10.10"
    netmask: "255.255.255.0"
    vlanid: 100

# Web-specific packages
proxmox_automatic_packages_additional:
  - "httpd"
  - "php"
  - "php-mysqlnd"

# Web admin user
proxmox_automatic_users_group_vars:
  webadmin:
    password: "$6$rounds=656000$YourSaltHere$YourHashHere"
    groups: ["wheel", "apache"]
    shell: "/bin/bash"
```

### Development Environment

```yaml
# group_vars/development.yml
proxmox_automatic_selinux_mode: "permissive"
proxmox_automatic_firewall_enabled: false

# Development packages (additional to base packages)
proxmox_automatic_packages_additional:
  - "nodejs"
  - "npm"
  - "python3-pip"
  - "docker-ce"
  - "docker-ce-cli"
  - "containerd.io"

# Developer users with sudo access
proxmox_automatic_users_group_vars:
  developer:
    password: "$6$rounds=656000$DevSalt$DevHash"
    groups: ["wheel", "docker"]
    ssh_key: "ssh-rsa AAAA...developer-key"

# Additional development repositories
proxmox_automatic_repos:
  - name: "docker-ce"
    baseurl: "https://download.docker.com/linux/centos/9/$basearch/stable"
    gpgcheck: true
    gpgkey: "https://download.docker.com/linux/centos/gpg"
```

## 🚀 Advanced Usage

### Custom Kickstart Templates

You can extend the role by providing custom kickstart templates:

```yaml
# Create custom template in templates/
# templates/custom-kickstart.cfg.j2

# Use custom template
proxmox_automatic_kickstart_template: "custom-kickstart.cfg.j2"
```

### Integration with Ansible Vault

```yaml
# group_vars/all/vault.yml (encrypted with ansible-vault)
vault_proxmox_password: "super-secret-password"
vault_smtp_password: "email-password"

# group_vars/all/main.yml
proxmox_automatic_api_password: "{{ vault_proxmox_password }}"
proxmox_automatic_smtp_password: "{{ vault_smtp_password }}"
```

### Conditional VM Creation

```yaml
# Create VMs only in production
- hosts: all
  roles:
    - role: lenhardt-its.proxmox_automatic
      when: environment == "production"
```

## 🔧 Troubleshooting

### Common Issues

1. **ISO Creation Fails**
   ```bash
   # Check dependencies
   proxmox_automatic_install_dependencies: true
   ```

2. **VM Creation Timeout**
   ```yaml
   # Increase timeouts
   proxmox_automatic_create_vm_retries: 5
   proxmox_automatic_create_vm_retry_delay: 10
   ```

3. **Network Issues**
   ```yaml
   # Use DHCP for testing
   proxmox_automatic_dhcp_enabled: true
   ```

### Debug Mode

```bash
# Run with increased verbosity
ansible-playbook -vvv playbook.yml
```

### Log Locations

- **Kickstart Files:** `{{ proxmox_automatic_files_dir }}/`
- **ISO Files:** `{{ proxmox_automatic_iso_dir }}/`
- **VM Console:** Proxmox VE web interface → VM → Console

## 📄 License

MIT

## 👥 Author Information

This role was created by [lenhardt-its](https://github.com/lenhardt-its).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

- [GitHub Issues](https://github.com/lenhardt-its/ansible-role-proxmox-automatic/issues)
- [Ansible Galaxy](https://galaxy.ansible.com/lenhardt-its/proxmox_automatic)
