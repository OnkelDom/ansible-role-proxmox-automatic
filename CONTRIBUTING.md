# Ansible Role: proxmox_automatic - Contributing Guide

Thank you for your interest in contributing! This guide helps you contribute to this project.

## 🚀 Types of Contributions

We welcome all kinds of contributions:

- 🐛 **Bug Reports** - Report issues or bugs
- ✨ **Feature Requests** - Suggest new features
- 📖 **Documentation** - Improve or extend the docs
- 🔧 **Code Contributions** - Fix bugs or implement features
- 🧪 **Tests** - Add tests or improve existing ones
- 💬 **Discussions** - Share ideas and best practices

## 📋 Before You Start

1. **Search for existing issues** - Someone might already be working on the problem
2. **Create an issue** - For larger changes, discuss your idea first
3. **Read the documentation** - Understand the current functionality

## 🔧 Development Setup

### Prerequisites

```bash
# Install Ansible and tools
pip install ansible ansible-lint yamllint

# Install local ISO tooling on Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y xorriso isolinux syslinux libarchive-tools

# Clone repository
git clone https://github.com/inframonks/ansible-role-proxmox-automatic.git
cd ansible-role-proxmox-automatic

# Install dependencies
ansible-galaxy collection install -r collections/requirements.yml
```

### Development Environment

```bash
# Run linting
yamllint .
ansible-lint
python3 -m py_compile library/proxmox_automatic_upload_iso.py

# Run CI-equivalent checks
make ci

# Run template rendering checks
ansible-playbook tests/render_templates.yml

# Optional controller-side media build checks
ansible-playbook tests/build_media.yml

# Optional Proxmox integration syntax checks
make e2e-syntax
```

## 📝 Pull Request Process

### 1. Fork and Create Branch

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR-USERNAME/ansible-role-proxmox-automatic.git
cd ansible-role-proxmox-automatic

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Development

- **Code Style**: Follow Ansible best practices
- **Commits**: Use meaningful commit messages
- **Tests**: Add tests for new functionality
- **Documentation**: Update README.md if needed

### 3. Testing

```bash
# Linting
yamllint .
ansible-lint
python3 -m py_compile library/proxmox_automatic_upload_iso.py

# Syntax Check
ansible-playbook tests/test.yml --syntax-check
ansible-playbook tests/render_templates.yml --syntax-check
ansible-playbook tests/build_media.yml --syntax-check

# Render and validate unattended installer configs
ansible-playbook tests/render_templates.yml

# Optional controller-side media build validation
ansible-playbook tests/build_media.yml

# Proxmox E2E syntax validation
ansible-playbook tests/proxmox_e2e.yml --syntax-check
ansible-playbook tests/proxmox_e2e_cleanup.yml --syntax-check
```

### Real Proxmox E2E Matrix

From a DevOps and system architecture perspective, the repository now contains a real Proxmox end-to-end matrix under:

- `tests/proxmox_e2e.yml`
- `tests/proxmox_e2e_cleanup.yml`
- `tests/proxmox_e2e_matrix.yml`

The matrix covers:

- Rocky online
- Rocky CDROM-only
- Debian online
- Debian CDROM-only

The E2E playbook expects real Proxmox credentials via environment variables:

```bash
export PROXMOX_AUTOMATIC_API_HOST="pve.example.com"
export PROXMOX_AUTOMATIC_API_USER="svc_ansible_rw@pam"
export PROXMOX_AUTOMATIC_API_PASSWORD="..."
export PROXMOX_AUTOMATIC_HYPERVISOR="pve"
export PROXMOX_AUTOMATIC_PVE_ISO_STORAGE="local"
export PROXMOX_AUTOMATIC_PVE_VM_STORAGE="volumes"
export PROXMOX_AUTOMATIC_DEFAULTBRIDGE="vmbr1"
export PROXMOX_AUTOMATIC_GATEWAY="192.0.2.1"
export PROXMOX_E2E_SSH_USER="litsadmin"
export PROXMOX_E2E_SSH_PASSWORD="..."
```

Run the lifecycle with:

```bash
ansible-playbook tests/proxmox_e2e_cleanup.yml
ansible-playbook tests/proxmox_e2e.yml
```

The cleanup playbook removes the E2E VMs, the shared HA rule/resource state for that matrix, and the generated E2E installer ISOs on Proxmox storage. The deploy playbook creates and verifies the guests, including HA rule/resource aggregation and in-guest storage layout checks.

### 4. Create Pull Request

1. Push your branch: `git push origin feature/your-feature-name`
2. Create a Pull Request on GitHub
3. Fill out the PR template completely
4. Wait for review and feedback

## 🎯 Code Standards

### Ansible Best Practices

- Use meaningful task names
- Use tags for all tasks
- Follow YAML indentation (2 spaces)
- Use `ansible.builtin.*` for core modules
- Document complex logic with comments

### Variable Naming Convention

```yaml
# Prefix for all variables
proxmox_automatic_*

# Examples
proxmox_automatic_memory: 2048
proxmox_automatic_storage_config: []
proxmox_automatic_networks: []
```

### Commit Message Format

```
type(scope): short description

Longer description if needed.

Fixes #123
```

**Types:** feat, fix, docs, style, refactor, test, chore

## 🧪 Testing

### Local Tests

```bash
# CI-equivalent checks
make ci

# Optional extended local validation:
yamllint .
ansible-lint
python3 -m py_compile library/proxmox_automatic_upload_iso.py
ansible-playbook tests/test.yml --syntax-check
ansible-playbook tests/render_templates.yml
ansible-playbook tests/build_media.yml
```

### Test Environment

For comprehensive tests you need:
- Ansible Controller (Linux/macOS)
- `xorriso`, `isolinux`, `syslinux`, `libarchive-tools` on the controller
- GitHub Actions validates linting, syntax, and template rendering only
- `tests/build_media.yml` is a controller-side media-build test and is intended for manual local validation
- Proxmox VE is only required for integration tests beyond this repository

## 📖 Documentation

### README Updates

When changing:
- Variables → Update variable tables
- Features → Add to feature list
- Configuration → Add examples
- Dependencies → Update requirements

### Adding Examples

New features should always include examples:

```yaml
# Example for new storage option
proxmox_automatic_storage_config:
  - name: virtio0
    size: "20"
    new_option: "example_value"  # New option explained
```

## 🐛 Bug Reports

Good bug reports contain:
- **Clear description** of the problem
- **Reproduction steps**
- **Expected vs. actual behavior**
- **Environment details** (OS, Ansible version, etc.)
- **Relevant logs** (without sensitive data!)
- **Minimal reproduction configuration**

## ✨ Feature Requests

Good feature requests contain:
- **Use case description** - Why is this feature useful?
- **Proposed API** - How should it be configured?
- **Alternatives** - Other approaches considered?
- **Backwards compatibility** - Avoid breaking changes

## 📞 Getting Help

- 🐛 **Bugs**: Create an issue with the Bug Report template
- ❓ **Questions**: Use GitHub Discussions or Question template
- 💬 **Chat**: [If Discord/Slack available]
- 📧 **Email**: [Maintainer email if available]

## 📄 License

By contributing, you agree that your work will be published under the same license as the project.

---

**Thank you for your contribution! 🎉**
