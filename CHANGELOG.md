# Changelog

## Unreleased

- PR #2: lokaler Beispielrollen-Link und Lint-/Ignore-Regeln in die Collection-Struktur integriert.

- Debian-Remaster ersetzt nur Installer-Konfigurationen und erhält Bootdateien für xorriso 1.5.6.
- Medien-Tests prüfen den Erhalt beider El-Torito-Booteinträge für BIOS und UEFI.

## 0.2.0 — 2026-10-27

- Collection `degitag.proxmox` mit Deploy-, Cluster-, Medien-, VM- und begrenzter Gastrolle.
- Namespace auf `degitag` umgestellt; bestehende Firewall- und Installationsmarker bleiben kompatibel.
- README mit Betriebswegen, zentraler Firewall, VM-Zuweisungen und Gast-nftables neu strukturiert.
- Eigenständige Rolle für nativen PVE-OTLP-Metrikexport.
- Strukturierte Konfiguration mit Legacy-Adapter, Validierung und Benutzer-Merge anhand des Namens.
- Zentrale Sicherheitsgruppen, IP-Sets, Aliase, explizite Cluster-Regeln und VM-Gruppenreferenzen.
- Optionale isolierte Gast-nftables-Policy mit Management-Zugriffsprüfung.
- Regeln mit stabiler Identität, Erhalt fremder Regeln und lokalen Änderungsjournalen.
- Inhaltsbasierter Mediencache, korrekte Passwort-API-Authentifizierung und Upload-Taskprüfung.
- Prüfung vorhandener VM-Identität, bewusste Neuinstallation, Wiederaufnahme und Medienabschluss.
- HA erst nach Gastprüfung; gemeinsame Regeln erhalten vorhandene Mitglieder.
- Entfernte wirkungslose SMTP-/EPEL-/DNF- und Metadaten-Optionen; TLS-Prüfung standardmäßig aktiv.
- Lokale Tests und Collection-Build; echte Proxmox-/Firewall-E2E-Abnahme weiterhin separat erforderlich.


All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.7] - 2025-08-04

### Added
- GitHub Actions permissions for security scanning (`security-events: write`)
- Conditional security scans to prevent fork PR permission issues
- Comprehensive .gitignore for Ansible, Python, IDE files, and generated artifacts

### Fixed
- Security scan upload permissions - resolves "Resource not accessible by integration" errors
- GitHub Actions security job now properly uploads SARIF results to Security tab
- Fork pull request compatibility - security scans only run for internal PRs and push events

### Security
- Enhanced Trivy security scanning with proper GitHub integration
- Automated SARIF upload to GitHub Security dashboard for vulnerability tracking

## [1.0.6] - 2025-08-04

### Added
- Functional badges in README.md for CI status, license, and versions
- Collections requirements with version constraints for `community.general` 10.x
- CHANGELOG documentation with complete release history

### Changed
- **BREAKING**: Requires `community.general` collection version 10.x (11+ removes Proxmox modules)
- Enhanced documentation with prerequisites section for collection installation
- Updated CI/CD workflows to use collections/requirements.yml

### Fixed
- All ansible-lint violations (production profile compliance)
- GitHub Actions CodeQL deprecation warnings (updated to v3)
- Trailing spaces and formatting issues throughout codebase
- Long line violations in Ansible tasks with YAML folded strings
- Ansible-lint configuration compatibility issues
- Yamllint configuration for ansible-lint requirements

## [1.0.5] - 2025-08-03

### Added
- MIT License for free usage
- Comprehensive GitHub infrastructure (issue templates, PR templates, CI/CD workflows)
- Multi-distribution dependency installation support (RHEL, Debian, macOS, SUSE, Arch)
- Hierarchical configuration system with intelligent merging
- English internationalization for global accessibility
- Complete documentation restructure and optimization (800+ → 442 lines)
- Security policies and best practices guide (SECURITY.md)
- Contributing guidelines (CONTRIBUTING.md)
- Automated testing with GitHub Actions (CI/CD)
- Security scanning with Trivy
- Ansible lint configuration and yamllint setup

### Changed
- Documentation language changed from German to English
- README completely restructured for better usability
- Improved error handling and debugging information
- Enhanced CI/CD workflows with multiple Ansible version testing (2.14, 2.15, 2.16)

### Fixed
- Template improvements for better repository handling
- Deployment methods for network interfaces, storage, and users

## [1.0.4] - Previous Release

### Fixed
- Template fixes for better repository handling
- Various bug fixes and improvements

## [1.0.3] - Previous Release

### Fixed
- Typography and minor text corrections

## [1.0.2] - Previous Release

### Changed
- Updates to main task file

## [1.0.1] - Previous Release

### Changed  
- Updates to main task file

## [1.0.0] - Initial Release

### Added
- Automated VM creation on Proxmox VE with Kickstart configurations
- Dynamic storage configuration with LVM support
- Multi-network interface support with VLAN
- Flexible user management with SSH keys
- Rocky Linux 9 optimization
- ISO management and upload functionality
- Hierarchical configuration through defaults, group_vars, and host_vars
