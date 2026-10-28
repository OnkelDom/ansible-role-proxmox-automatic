# `degitag.proxmox`

[![CI](https://github.com/degitag/ansible-role-proxmox-automatic/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/degitag/ansible-role-proxmox-automatic/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/degitag/ansible-role-proxmox-automatic)](https://github.com/degitag/ansible-role-proxmox-automatic/releases)
[![Tag](https://img.shields.io/github/v/tag/degitag/ansible-role-proxmox-automatic?sort=date)](https://github.com/degitag/ansible-role-proxmox-automatic/tags)
![Ansible Core](https://img.shields.io/badge/ansible--core-2.20%20%7C%202.21-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Ansible-Collection für unbeaufsichtigte Rocky-Linux- und Debian-Installationen auf Proxmox VE, zentrale Firewall-Regeln und optionale Gastkonfiguration. Der bisherige Rollenname `proxmox_automatic` bleibt als Kompatibilitätseinstieg erhalten.

**Firewall-Verwaltung ist enthalten:** Sicherheitsgruppen, Aliase und IP-Sets im Cluster, Zuweisungen und Regeln je VM sowie optional nftables im Gast.

[Installation](#installation) · [Firewall](#firewall-konfigurieren) · [VM installieren](#vm-installieren) · [Betrieb](#betrieb-vorhandener-vms) · [Checks](#entwicklung-und-checks) · [Migration](#migration)

## Verantwortung und Architektur

`deploy` verwendet interne Task-Einstiege für Pools, HA und VM-Firewall. Die Spezialrollen `install_media`, `vm` und `guest` erhalten dabei den normalisierten privaten Kontext `_proxmox_config`; für eigenständige Aufrufe zuerst `deploy`, `tasks_from: normalize_only`, verwenden. Medien-only-Normalisierung ist über `normalize_media` verfügbar.

Aus Sicht des Plattformbetriebs bleiben Patchmanagement, SMTP, Monitoring und allgemeine Server-Baselines in den dafür zuständigen Betriebssystemrollen. Die Gastrolle bildet bewusst keine zweite vollständige Server-Baseline.

Zusätzlich konfiguriert die eigenständige Rolle [`degitag.proxmox.metric_server`](roles/metric_server/README.md) einen nativen PVE-OTLP-Metrikexport. Sie läuft mit Root-Rechten auf genau einem repräsentativen PVE-Node je Cluster und wird vom VM-Deployment nicht automatisch aufgerufen.

## Plattformen und Laufzeit

- Controller: Python 3.12, ansible-core ab 2.20.10 bis einschließlich 2.21, `requests`, `xorriso` und für die Debian-Bootmenü-Anpassung `perl`.
- Collections aus `requirements.yml`; für die Community-Proxmox-Module zusätzlich `proxmoxer` im Python-Interpreter des Controllers.
- Rocky-Backend: vorbereitetes Haupt-ISO auf Proxmox, das `ks.cfg` von der zweiten CD lädt. Die Collection baut die Konfigurations-CD.
- Debian-Backend: lokales Debian-13-AMD64-ISO. Der Remaster übernimmt BIOS-/EFI-Bootmetadaten des Originals.
- ISO- und VM-Storage, Bridge, API-Berechtigungen, DNS/Mirror-Erreichbarkeit und ein SSH-Schlüssel für den Bootstrap-Benutzer sowie eine geklärte SSH-Hostkey-Vertrauensstellung für neue Gäste.
- Für Node-Affinity-HA-Regeln ein Proxmox mit `/cluster/ha/rules` (Proxmox VE 9). Der Zugriff wird nicht benötigt, wenn HA deaktiviert ist.
- Firewall-Sicherheitsgruppen benötigen zentrale Änderungsrechte; für die Gruppe ist laut Proxmox-API `Sys.Modify` erforderlich. VM- und HA-Rechte separat begrenzen.

TLS-Zertifikatsprüfung ist standardmäßig aktiv. Eine interne CA gehört in den Truststore des Controllers. `validate_certs: false` ist nur eine ausdrückliche Konfiguration für eine entsprechend abgegrenzte Umgebung.

## Installation

Die Collection wird aus diesem Repository gebaut. Die folgenden Befehle benötigen kein auf Galaxy veröffentlichtes Release:

```bash
git clone https://github.com/degitag/ansible-role-proxmox-automatic.git
cd ansible-role-proxmox-automatic
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-test.txt
ansible-galaxy collection install -r requirements.yml
make build
ansible-galaxy collection install ./degitag-proxmox-0.2.0.tar.gz --force
```

Die Beispiele verwenden die Playbooks aus dem Checkout und die installierte Collection. Für lokale Entwicklung stattdessen `make prepare` ausführen: Es erzeugt ignorierte Verweise auf den Checkout unter `.collections/` und `.ci-roles/`.

API-Zugang zentral im eigenen Inventory hinterlegen. Das Token-Secret gehört in Ansible Vault:

```yaml
# inventory/group_vars/all/main.yml
proxmox_api:
  host: pve.example.com
  token_id: automation@pve!ansible
  token_secret: "{{ vault_proxmox_token_secret }}"
  validate_certs: true
```

```bash
mkdir -p inventory/group_vars/all
EDITOR=vim ansible-vault create inventory/group_vars/all/vault.yml
# vault_proxmox_token_secret im Vault hinterlegen; Editor bei Bedarf:
EDITOR=vim ansible-vault edit inventory/group_vars/all/vault.yml
```

Vault-Läufe benötigen `--ask-vault-pass` oder eine konfigurierte Vault-ID.

## Verwendung

### Firewall konfigurieren

#### Welche Ebene ist zuständig?

| Ebene | Konfiguration | Wirkung und Einstieg |
|---|---|---|
| Cluster | `proxmox_cluster_firewall` | Sicherheitsgruppen, Aliase, IP-Sets und explizite Hostregeln; `playbooks/firewall.yml` |
| VM auf Proxmox | `proxmox_firewall.pve_enabled: true` | Gruppenreferenzen, eigene VM-Regeln, Policies und Firewall-Flag an VM-NICs; `playbooks/deploy.yml` |
| Gastbetriebssystem | `proxmox_firewall.guest_enabled: true` | Eigene nftables-Tabelle im Gast; Deployment oder `playbooks/configure_guests.yml` |

Beide VM-bezogenen Schalter sind standardmäßig `false`. `management_sources` muss bei Aktivierung gesetzt sein und den tatsächlichen SSH-Zugriff abdecken. Für wirksamen PVE-Filterschutz müssen zusätzlich die Firewall-Aktivierung und das Backend auf Cluster und Nodes passend eingerichtet sein.

#### 1. Zentrale Gruppen, Aliase und IP-Sets

Für den separaten Firewall-Lauf einen repräsentativen Host je Cluster ergänzen:

```yaml
# inventory/hosts.yml
all:
  children:
    proxmox_clusters:
      hosts:
        production:
          ansible_connection: local
    proxmox_vms:
      hosts:
        web01.example.com: {}
```

Der bevorzugte Betriebsweg ist `playbooks/firewall.yml`. Die Zuweisung zu VMs erfolgt beispielsweise in `group_vars/webservers.yml` über `proxmox_firewall.groups: [management, webserver]`. Im Inventory steht **ein Host je Cluster** in `proxmox_clusters`. VM-Provisionierung und Gastzugriff sind für diesen Weg nicht erforderlich.

```yaml
# group_vars/proxmox_clusters.yml
proxmox_api:
  host: pve.example.com
  token_id: automation@pve!ansible
  token_secret: "{{ vault_proxmox_token_secret }}"
  validate_certs: true

proxmox_cluster_firewall:
  aliases:
    - name: monitoring
      cidr: 192.0.2.20
  ipsets:
    - name: management
      cidrs:
        - cidr: 192.0.2.0/24
        - cidr: 2001:db8:10::/64
    - name: application
      cidrs:
        - cidr: 198.51.100.0/24
  groups:
    - name: management
      rules:
        - name: ssh
          type: in
          action: ACCEPT
          source: +management
          proto: tcp
          dport: '22'
    - name: webserver
      rules:
        - name: https
          type: in
          action: ACCEPT
          proto: tcp
          dport: '443'
    - name: database
      rules:
        - name: postgres
          type: in
          action: ACCEPT
          source: +application
          proto: tcp
          dport: '5432'
  rules: []
  options: {}
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/firewall.yml --check
ansible-playbook -i inventory/hosts.yml playbooks/firewall.yml
```

Eine Sicherheitsgruppe enthält Regeln und wird anschließend von VMs referenziert. Zentrale `rules` betreffen hingegen die **Proxmox-Hosts**. `options` kann ausschließlich ausdrücklich gesetzte Werte `enable`, `policy_in` und `policy_out` verändern. Mit `options: {}` bleiben globale Aktivierung und Standard-Policies unverändert. `options.enable: true` aktiviert die Datacenter-Firewall ausdrücklich; einen Wechsel des Node-Firewall-Backends führt die Collection nicht durch. Vor einer restriktiven Host-Policy müssen Management-, Cluster- und Infrastrukturpfade im Regelwerk berücksichtigt sein.

Zentrale Firewall-Objekte benötigen `Sys.Modify` auf `/`; die eingebaute Rolle `PVEAdmin` reicht dafür nicht aus. Für den Dauerbetrieb ist diese Berechtigung gezielt einem separaten Policy-Account beziehungsweise dessen Token zuzuweisen. Wenn Token und Passwort konfiguriert sind, hat die Token-Anmeldung Vorrang. Vor einer Aktivierung müssen SSH und die Proxmox-API (standardmäßig TCP 22 und 8006) für die aktuellen internen und gegebenenfalls öffentlichen Adminadressen ausdrücklich freigegeben und ein Rückweg vorbereitet sein.

#### Eigentum, Reihenfolge und Löschung

- Sicherheitsgruppen, Aliase und IP-Sets werden nur aus der ausdrücklich übergebenen Liste verwaltet. Die Collection reserviert ihren Kommentar als Eigentumsmarker `lenmail.proxmox`.
- Gleichnamige vorhandene Objekte ohne diesen Marker werden nicht automatisch übernommen.
- Innerhalb eines verwalteten IP-Sets ist `cidrs` die vollständige Mitgliederliste. Fehlende Mitglieder werden entfernt.
- Regeln erhalten über `name` eine stabile Identität im Kommentar. Die Reihenfolge in der Liste ist verbindlich. Vorhandene fremde Regeln bleiben in ihrer relativen Reihenfolge **vor** dem verwalteten Block; sie können daher früher entscheiden.
- In einem übergebenen Regelwerk werden zuvor verwaltete, jetzt fehlende Regeln entfernt. `state: absent` ist ebenfalls möglich. Ein ausgelassenes `rules`-Feld beim direkten Modulaufruf verändert dieses Regelwerk nicht.
- Für ein ganzes Objekt gilt `state: absent`. Abhängige Referenzen zuerst entfernen, dann die Gruppe beziehungsweise das IP-Set löschen. Eine Gruppe lediglich aus der Objektliste zu entfernen löscht sie nicht.
- Proxmox verarbeitet mehrere API-Schreibzugriffe einzeln. Ein Firewall-Lauf ist keine atomare Transaktion. Parallele Bearbeitung derselben Objekte ist zu vermeiden; Digests schützen die unterstützten Einzeloperationen.
- Vor Schreibzugriffen entsteht lokal ein Journal unter `.proxmox-firewall-backups/`, mit Modus `0600`. Es enthält gelesene Ausgangszustände und geplante API-Operationen. Der Modulrückgabewert `backup_file` benennt die Datei auch bei Fehlern. Ein Rollback muss anhand des Journals und der tatsächlichen API-Lage gezielt erfolgen.

#### 2. Regeln und Gruppen einer VM zuweisen

```yaml
# inventory/group_vars/webservers.yml oder host_vars/web01.example.com.yml
proxmox_firewall:
  pve_enabled: true
  groups: [management, webserver]
  management_sources: [192.0.2.0/24]
  policy_in: DROP
  policy_out: ACCEPT
  rules:
    - name: monitoring-agent
      type: in
      action: ACCEPT
      source: monitoring
      proto: tcp
      dport: '9100'
  guest_enabled: false
  guest_rules: []
```

Die referenzierten zentralen Gruppen und der Alias `monitoring` müssen zuvor angelegt sein. Die VM-Regeln werden in dieser Reihenfolge aufgebaut: SSH-Ausnahmen aus `management_sources`, Gruppenreferenzen in Listenreihenfolge, danach `rules`. Fremde bestehende Regeln bleiben vor diesem verwalteten Block erhalten. `deploy` aktiviert außerdem das Firewall-Flag an den VM-NICs und erhält dabei MAC-Adressen und andere NIC-Optionen.

```bash
ansible-playbook -i inventory/hosts.yml playbooks/deploy.yml --limit web01.example.com --check
ansible-playbook -i inventory/hosts.yml playbooks/deploy.yml --limit web01.example.com
```

Dies ist der Deployment-Einstieg einschließlich VM-Identitätsprüfung und Gastverifikation. `playbooks/firewall.yml` verwaltet ausschließlich zentrale Objekte und weist vorhandenen VMs keine Gruppen zu.

#### 3. Optionale nftables-Regeln im Gast

```yaml
# Vollständige gewünschte proxmox_firewall-Konfiguration am Host hinterlegen.
proxmox_firewall:
  pve_enabled: true
  groups: [management, webserver]
  management_sources: [192.0.2.0/24]
  policy_in: DROP
  policy_out: ACCEPT
  guest_enabled: true
  guest_rules:
    - name: https
      type: in
      action: ACCEPT
      proto: tcp
      dport: '443'
```

`guest_enabled: true` verwaltet eine eigene nftables-Tabelle `inet lenmail_proxmox` und einen eigenen Systemd-Dienst. Bestehende Tabellen und deren Dienste werden nicht gelöscht oder deaktiviert. Eine bereits aktive firewalld-, UFW- oder nftables-Systemkonfiguration führt vor Aktivierung zum Abbruch. Eine geplante Koexistenz kann ausdrücklich über `allow_other_firewalls: true` freigegeben werden. Bei neuen Rocky-Installationen mit aktivierter Gast-nftables-Policy wird firewalld im Installer deaktiviert.

`guest_rules` verwendet ebenfalls stabile Namen, `type: in|out`, `action: ACCEPT|DROP|REJECT`, `proto`, `source`, `dest`, `dport` und `sport`. Gastadressen sind IPs/CIDRs; Proxmox-Aliase, IP-Sets und Sicherheitsgruppen werden dort nicht stillschweigend expandiert. Ports sind Zahlen oder `start:end`-Bereiche. Basis-Policies sind `ACCEPT` oder `DROP`.

Loopback, bestehende Verbindungen, ICMP/IPv6-Kontrollverkehr und DHCP-Antworten bleiben in der Gast-Basis erlaubt. Beide Firewall-Ebenen benötigen explizite `management_sources`; vor Aktivierung wird geprüft, ob sie die im Gast beobachtete SSH-Quelladresse abdecken. Die Regeln der Gruppen sollten bei abweichendem SSH-Port entsprechend angepasst sein. `guest_enabled: false` und `pve_enabled: false` lassen die jeweilige Ebene unverwaltet; sie entfernen keine zuvor eingerichtete Policy. Eine Deaktivierung bestehender Policies muss als eigene, bewusste Betriebsänderung erfolgen.

`proxmox_guest.port` wird bereits im Installer gesetzt. Rocky richtet bei Bedarf zusätzlich das SELinux-Portlabel ein. Ein nachträglicher Portwechsel vorhandener Gäste gehört in eine geplante SSH-Migration; der bestehende Zugriff wird durch `guest` nicht umgestellt.

Für bereits installierte Gäste:

```bash
ansible-playbook -i inventory/hosts.yml playbooks/configure_guests.yml --limit web01.example.com
```

Dieser Einstieg prüft und konfiguriert den Gast einschließlich aktivierter Gast-Firewall. Er verwaltet weder VM-Hardware noch die PVE-VM-Firewall.

#### Ressourcenidentität beim Namespace-Wechsel

Der öffentliche Collection-Name ist `degitag.proxmox`. Bestehende Laufzeitkennungen bleiben aus Kompatibilitätsgründen erhalten: Firewall-Eigentumsmarker `lenmail.proxmox`, VM-Installationsmarker `lenmail.proxmox:installing` beziehungsweise `:ready`, nftables-Tabelle `inet lenmail_proxmox` sowie `/etc/lenmail-proxmox.nft` und `lenmail-proxmox-firewall.service`. Sie identifizieren bereits verwaltete Ressourcen; ihre Umbenennung würde eine gesonderte Migration erfordern.

### VM installieren

Das folgende Beispiel kommt nach `inventory/host_vars/web01.example.com.yml`. Es verwendet die oben definierten API-Daten und zentralen Firewall-Gruppen. `bootstrap_public_key` muss einen eigenen öffentlichen SSH-Schlüssel enthalten; der Controller benötigt den zugehörigen privaten Schlüssel für SSH und einen funktionierenden Sudo-Zugang.

```yaml
proxmox_vm:
  name: web01.example.com
  vmid: 3011
  node: pve01
  pool: applications
  iso_storage: local
  disk_storage: local-lvm
  hardware:
    cores: 4
    memory: 4096
  networks:
    - name: net0
      interface_name: ens18
      bridge: vmbr0
      vlanid: 30
      ip: 192.0.2.11
      netmask: 255.255.255.0
      gateway: 192.0.2.1
  # Optional: vollständige eigene Disk-/Partitionierungsstruktur als disks.
  # Ohne disks wird das kompatible Standardlayout verwendet.

proxmox_install:
  backend: debian_preseed
  source: online
  source_iso: /srv/iso/debian-13-amd64-netinst.iso
  settings:
    timezone: Europe/Berlin
    dns_servers: [192.0.2.53]

proxmox_guest:
  host: 192.0.2.11
  ssh_user: automation
  users:
    - name: automation
      groups: [sudo]
      ssh_key: "{{ bootstrap_public_key }}"
      sudo_commands: ALL
      sudo_nopasswd: true
  # Wenn eine andere Baseline-Rolle diese Ressourcen verwaltet:
  manage_users: true
  manage_packages: false
  manage_sysctl: false

proxmox_ha:
  enabled: false

proxmox_firewall:
  pve_enabled: true
  groups: [management, webserver]
  management_sources: [192.0.2.0/24]
  policy_in: DROP
  policy_out: ACCEPT
  rules: []
  guest_enabled: false
  guest_rules: []
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/deploy.yml --check
ansible-playbook -i inventory/hosts.yml playbooks/deploy.yml
```

`proxmox_vm.name` ist der Systemname, `proxmox_guest.host` das SSH-Ziel und `proxmox_api.host` der API-Endpunkt. Die Adressen müssen nicht identisch sein. `ansible_host` wird im Kompatibilitätsweg weiterhin als Systemname verwendet.

Die Standarddisk ist 20 GiB groß und enthält EFI, `/boot`, LVM-Root, `/var/log` und Swap. Mehrere VirtIO-Disks mit PVE-Optionen, mehrere NICs, VLAN, MAC, MTU, Bandbreitenlimit, CPU/Sockel, UEFI, TPM, VGA und PCI-Passthrough bleiben konfigurierbar. Auf Debian wird derzeit eine VG je Disk unterstützt; nicht unterstützte Konfigurationen werden abgewiesen.

Neue VMs aktivieren NUMA, da der Standard RAM-Hotplug enthält. Bei `hardware.numa: false` muss `memory` aus `hardware.hotplug` entfernt werden. Der historische VGA-Wert `default` wird zu `std` normalisiert.

Für Rocky Linux `proxmox_install.backend: rocky_kickstart` setzen und über `source_iso_name` das vorbereitete Haupt-ISO auf dem konfigurierten Proxmox-ISO-Storage auswählen. Das Haupt-ISO muss die Kickstart-Datei von der separat erzeugten Konfigurations-CD laden. `source: online` verwendet Paketquellen im Netz, `source: cdrom` benötigt ein Medium mit dem vollständigen Paketbestand. Debian verwendet `debian_preseed` beziehungsweise `debian13_preseed` und ein lokales Quell-ISO.

Die Variablen sind in [VARIABLES.md](VARIABLES.md) indiziert; weitere Inventory-Beispiele liegen unter [examples/inventory](examples/inventory).

### Betrieb vorhandener VMs

1. Variablen normalisieren und VMID-/Namenskollisionen, Firewall-Definitionen und gemeinsame HA-Profile vor Änderungen prüfen.
2. Pools und zentrale Firewall-Objekte vorbereiten.
3. Nur für eine neue VM, einen eigenen unterbrochenen Installationslauf oder ausdrücklich `reinstall: true` Medien bauen und den Installer starten.
4. SSH abwarten, Betriebssystem, erwartete Mountpoints und statische IPv4-Adressen prüfen. Diese Kontrollen ersetzen keine vollständige Prüfung aller LVM-Größen oder der Anwendung.
5. Gewünschte Gastkonfiguration anwenden; danach nur eigene Installationsmedien entfernen und den Systemboot festlegen.
6. Optional VM-Firewall und anschließend HA aktivieren.

Vor einer HA-Registrierung prüft die Rolle Quorum sowie aktuelle Heartbeats des HA-Masters und des lokalen Ressourcenmanagers. Fehlende oder mehr als zwei Minuten alte Heartbeats führen vor dem Anlegen der HA-Ressource zum Abbruch. Die Rolle startet oder repariert keine HA-Dienste. Für Deployments ohne betriebsbereite HA-Verwaltung ist `proxmox_ha.enabled: false` zu setzen.

Bestehende VMs mit anderem Namen oder anderer Ressourcenart führen zum Abbruch. Eine vorhandene gleichnamige VM erhält ohne expliziten Neuinstallationsauftrag keine Installationsmedien. Die interne Installationsmarkierung in der VM-Beschreibung ermöglicht die Wiederaufnahme eigener Läufe. Gleichnamige vorhandene VMs ohne Markierung werden nicht als eigene Installationen markiert.

`proxmox_deploy.reinstall: true` ist ein destruktiver Installationsauftrag. Die VM muss vorher bewusst gestoppt sein. Die Collection löscht keine virtuellen Disks; der Installer partitioniert die konfigurierten Gastdisks neu. Ein VM-/Datenbackup gehört vor diesen Auftrag. Bei einer bloßen Wiederaufnahme ohne Neuinstallationsauftrag bleibt die Systemdisk vor dem Installer in der Bootreihenfolge; ein unvollständig installiertes System kann dadurch eine manuelle Entscheidung zum erneuten Installieren erfordern.

Bei einer expliziten Neuinstallation fährt der Installer am Ende herunter. Mit `wait_for_install: true` wartet die Rolle auf den aktuellen QEMU-Status `stopped` und startet danach die Systemdisk in einem neuen QEMU-Prozess. Dadurch wird die geänderte Bootreihenfolge wirksam. Ohne Installationswartephase bleibt die fertig installierte VM ausgeschaltet und muss anschließend bewusst von Disk gestartet werden.

Neuinstallationen erzeugen neue SSH-Hostkeys. Die Vertrauensdatei muss nach einem unabhängigen Abgleich gezielt aktualisiert werden, etwa anhand des über den authentifizierten Hypervisor abgefragten Guest Agents. Die Rolle schaltet die Hostkey-Prüfung nicht ab.

`update_hardware: true` erlaubt ausschließlich die Änderung von CPU, Kernen, Sockeln, RAM und Autostart. Disks, MACs, EFI-/TPM-Disks und PCI-Mappings werden bei vorhandenen VMs nicht automatisch ersetzt. Änderungen können einen späteren Neustart erfordern.

Der Deployment-Weg benötigt die lineare Ansible-Strategie ohne `serial`-Batches. Unabhängige Cluster- und Gastpflege laufen über eigene Playbooks.

### Installationsmedien und Geheimnisse

Installer-Eingaben und Quell-ISO werden gehasht. Ein Manifest prüft zusätzlich die lokale ISO-Prüfsumme; unveränderte Artefakte werden wiederverwendet. Der Remote-Name enthält VMID und volle ISO-SHA256. Ein vorhandener Remote-Name wird nur bei passender Größe wiederverwendet; es erfolgt kein vollständiger Remote-Download zur Inhaltsprüfung. Diese Namen sind als unveränderliche Artefakte zu behandeln.

Uploads warten auf den erfolgreichen Proxmox-Task. Ein bereits vorhandenes Rocky-Haupt-ISO wird vor VM-Erstellung ebenfalls auf Verfügbarkeit geprüft.

Konfigurationsdateien, lokale ISOs und Manifeste erhalten `0600`, Arbeitsverzeichnisse `0700`; Debian-Extraktionsverzeichnisse werden auch bei Fehlern bereinigt. Installer-Medien können Passwort-Hashes enthalten. SSH-Schlüssel und gesperrte Passwortanmeldung sind für Bootstrap-Zugänge zu bevorzugen.

`proxmox_deploy.cleanup_local_artifacts: true` entfernt eigene lokale Artefakte nach erfolgreicher Installation. Remote-ISOs werden nicht automatisch gelöscht, da sie referenziert oder für Wiederaufnahme benötigt werden können. Retention auf Proxmox muss anhand der Artefaktnamen und tatsächlichen Referenzen erfolgen.

`--check` liest vorhandene API-Zustände und prognostiziert unterstützte Änderungen. Es baut keine neuen ISOs, lädt nichts hoch und verbindet sich nicht mit neuen Gästen. Ein vollständiger Trockenlauf der Betriebssysteminstallation ist damit nicht möglich.

## Rollen

| Rolle | Aufgabe |
|---|---|
| `degitag.proxmox.deploy` | Vorprüfung, Installation, Verifikation und Abschluss koordinieren |
| `degitag.proxmox.cluster_resources` | Zentrale Sicherheitsgruppen, Aliase, IP-Sets und explizite Cluster-Regeln unabhängig von VMs verwalten |
| `degitag.proxmox.install_media` | Kickstart-Konfigurations-CD beziehungsweise remastertes Debian-ISO erzeugen und hochladen |
| `degitag.proxmox.vm` | VM-Hardware erstellen, Installer starten und Bootreihenfolge steuern |
| `degitag.proxmox.guest` | Installation prüfen, Bootstrap-Benutzer/Pakete/Sysctl verwalten und optional eine Gast-Firewall einrichten |

Interne Rollen `install_media`, `vm` und `guest` erhalten ihren validierten Kontext von `deploy`. Direkte Aufrufe benötigen den in der Architektur beschriebenen Normalisierungsschritt. `cluster_resources` und `metric_server` bieten eigenständige Betriebseinstiege.

## Repository-Struktur

```text
.github/             CI, geprüfte Tag-Releases und Dependency-Updates
meta/runtime.yml     unterstützte Ansible-Versionen
galaxy.yml           Collection-Identität, Abhängigkeiten und Paketgrenzen
requirements.yml     externe Collections für Entwicklung und Checks
requirements-test.txt Python-Werkzeuge für lokale und GitHub-Prüfungen
roles/               Deploy-, Cluster-, Medien-, VM-, Gast- und Metrikrollen
plugins/             API-Module, Filter und gemeinsame API-Bibliotheken
playbooks/           Deployment, zentrale Firewall und Gastpflege
examples/            generische Inventories und Aufrufbeispiele
tests/               Unit-, Integrations-, Installer- und explizite Live-E2E-Tests
tools/               lokale Vorbereitung, Repository- und Paketprüfungen
docs/                gemeinsamer Repository-Standard, Migration und Prüfnachweise
```

`defaults/`, `tasks/`, `templates/` und `meta/main.yml` im Root bleiben für den historischen Rollenaufruf erhalten. Sie sind Adapter zur Collection; neue Funktionalität liegt unter `roles/` und `plugins/`. Dies ist eine dokumentierte Abweichung vom gemeinsamen [Repository-Standard](docs/repository-standard.md).

## Entwicklung und Checks

```bash
source .venv/bin/activate
bash tests/run_checks.sh
```

`bash tests/run_checks.sh` (auch `make ci`) umfasst Lint, Syntax, Python-Tests, Installer-/Firewall-Rendering und isolierte Medien-Fixtures inklusive Cache-Wiederholung. Die Medien-Fixture prüft Struktur und Bootkonfiguration; ihr Kernel/Initrd/BIOS-Stub ist absichtlich nicht bootfähig. Der GitHub-Workflow ist für Python 3.12 mit ansible-core 2.20 und 2.21 konfiguriert. Auf Linux mit installiertem nftables wird zusätzlich die nftables-Syntax geprüft; lokal auf macOS entfällt diese Kernelprüfung.

Die echte E2E-Matrix liegt unter `tests/proxmox_e2e*.yml`: Rocky und Debian, online und CD-ROM, SSH, Layout und gemeinsame HA-Regel. Sie wird nur über `make e2e` ausdrücklich gestartet. CD-ROM-Installation benötigt ein Medium mit dem vollständigen erforderlichen Paketbestand. Für Offline-Gäste zusätzliche Paketinstallation entsprechend deaktivieren.

Vor produktiver Nutzung sind im Testcluster mindestens neue Installation, Wiederholung, Wiederaufnahme, explizite Neuinstallation, zentrale Gruppenänderung, VM-Gruppenzuordnung, Firewall-Zugriff aus erlaubten und gesperrten Netzen sowie beide Gastbetriebssysteme abzunehmen. Die E2E-Bereinigung prüft VM-Identität und Eigentumsmarkierungen; unveränderliche Remote-ISOs bleiben erhalten.

[CONTRIBUTING.md](CONTRIBUTING.md) beschreibt die Entwicklungsumgebung und die Make-Ziele. Die Fachtests laufen ohne produktive API-Zugriffe; echte Proxmox-E2E-Läufe sind separat und ausdrücklich zu starten.

## CI und Releases

Der neue Ausgangstag der Collection ist `v0.2.0`. Historische Tags ohne `v` wie `1.0.2` gehören zur früheren Standalone-Rolle und bleiben unverändert.

GitHub ruft denselben Einstieg `bash tests/run_checks.sh` wie die lokale Entwicklung auf. Die Matrix verwendet Python 3.12 mit ansible-core 2.20 und 2.21. Actions sind auf Commit-SHAs festgelegt; Pull-Request-Workflows erhalten nur Leserechte.

Ein Release wird ausschließlich durch einen zur `galaxy.yml`-Version passenden Tag `v<version>` ausgelöst und führt die Checks erneut aus. Das geprüfte Collection-Archiv wird als GitHub-Release-Artefakt bereitgestellt. Eine Galaxy-Publikation wird nicht automatisch ausgeführt.

## Migration

Die gemeinsame Controller-Basis wechselt von Python 3.11/ansible-core 2.19 auf Python 3.12/ansible-core >=2.20.10,<2.22. Bestehende Controller müssen vor dem Collection-Update angeglichen werden; die Gastbetriebssysteme werden dadurch nicht verändert. Details stehen in [docs/migration.md](docs/migration.md).

Bestehende Inventories und der Rollenname bleiben nutzbar, wenn die Collection installiert ist. Named-Merges gelten weiter für die expliziten Legacy-Ebenen Defaults → Gruppe → Host → Playbook; Benutzer werden jetzt anhand ihres Namens zusammengeführt. Listen in der strukturierten Konfiguration sind dagegen vollständige Listen gemäß normaler Ansible-Variablenpriorität.

Bewusste Änderungen:

- Kein Beispiel-Admin mit Platzhalterpasswort mehr. Bootstrap-Zugang ausdrücklich definieren.
- TLS-Prüfung standardmäßig aktiv; vorhandene explizite Ausnahmen bleiben wirksam.
- Entfernte wirkungslose/ausgelagerte Optionen: SMTP, EPEL-Schalter, DNF-Automatic, Verantwortlicher/Hostbeschreibung und `ha_group_nofailback`. Vollständige Deployments weisen diese Eingaben mit Migrationshinweis ab.
- Rocky verwendet jetzt tatsächlich die berechnete Backend-Paketliste.
- Der vollständige Kompatibilitäts-Tag `proxmox_automatic` bleibt erhalten. Selektive alte Tags werden durch die getrennten Rolleneinstiege und Playbooks ersetzt; `--tags proxmox_validate` führt nur die Vorprüfung aus.
- Interne Task-Dateien sind keine stabile öffentliche Schnittstelle. `create_kickstart`, `create_preseed` und `install_dependencies` bleiben als Adapter bestehen.
- Eigene Installer-Templates erhalten `_proxmox_config`; alte Vorlagen müssen bei abweichender Variablenschnittstelle geprüft werden.

Bei bisheriger Nutzung der unveröffentlichten Collection `lenmail.proxmox` die Rollen-, Modul- und Filteraufrufe auf `degitag.proxmox` sowie Collection-Abhängigkeiten umstellen. Der Legacy-Rollenname `proxmox_automatic` bleibt erhalten. Für dessen Auflösung außerhalb dieses Checkouts muss die installierte Collection zusätzlich im Rollenpfad unter diesem Namen verlinkt sein; `make prepare` richtet dies nur für die lokale Entwicklung ein.

## Sicherheit

Secrets gehören in Ansible Vault oder einen externen Secret Store. Installer-Medien und Firewall-Journale enthalten betriebliche beziehungsweise sensible Daten; sie werden nicht mit der Collection ausgeliefert. [SECURITY.md](SECURITY.md) beschreibt vertrauliche Meldungen und die belegten Sicherheitsgrenzen.

## Lizenz

[MIT](LICENSE). Enthaltene Rollen und Module behalten ihre vorhandenen Lizenzangaben.

Betriebsdokumentation: [Lenmail-Outline](https://docs.lenmail.de/doc/ansible-proxmox-refactoring-und-zentrale-firewall-policies-DGBs0T8Jbq). Weitere Referenzen: [Variablen](VARIABLES.md), [Changelog](CHANGELOG.md), [Firewall-Beispiel](examples/firewall.yml), [Metrikserver](roles/metric_server/README.md).
