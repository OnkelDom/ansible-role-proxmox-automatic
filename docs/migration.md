# Migration zum gemeinsamen Collection-Repository-Standard

## Controller und Abhängigkeiten

Python 3.12 und ansible-core >=2.20.10,<2.22 ersetzen die bisherige Basis Python 3.11/ansible-core 2.19. Vor dem Update eine passende virtuelle Umgebung aufbauen und die tatsächlich verwendete Core-Version prüfen:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-test.txt
ansible-galaxy collection install -r requirements.yml
ansible --version
bash tests/run_checks.sh
```

`requirements.yml` ersetzt `collections/requirements.yml`, `requirements-test.txt` ersetzt `requirements-dev.txt`, und Entwicklungswerkzeuge liegen unter `tools/` statt `scripts/`. Eigene Aufrufskripte entsprechend anpassen.

## Collection und alter Rollenaufruf

Der öffentliche Namespace bleibt `degitag.proxmox`. Rollen-, Modul- und Filteraufrufe aus dem unveröffentlichten Namespace `lenmail.proxmox` müssen angepasst werden. `proxmox_automatic` bleibt als Root-Adapter verfügbar. Außerhalb dieses Checkouts benötigt der historische Rollenname einen passenden Rollenpfad beziehungsweise Link auf die installierte Collection. `make prepare` richtet nur lokale Entwicklungsverweise ein.

Bestehende Laufzeitkennungen bleiben erhalten: Firewall-Eigentumsmarker `lenmail.proxmox`, VM-Installationsmarker `lenmail.proxmox:installing`/`:ready`, nftables-Tabelle `inet lenmail_proxmox` und der zugehörige Dienst. Eine Änderung dieser Kennungen würde eine getrennte Ressourcenmigration erfordern.

## Öffentliche und interne Rollen

`deploy`, `cluster_resources` und `metric_server` stellen dokumentierte Betriebseinstiege bereit. `install_media`, `vm` und `guest` benötigen einen durch `deploy` normalisierten `_proxmox_config`-Kontext. Der gemeinsame Repository-Standard macht interne Phasen nicht automatisch zu eigenständig nutzbaren Rollen.

## Prüfungen und Veröffentlichung

Der gemeinsame vollständige Einstieg ist `bash tests/run_checks.sh`; `make ci` und `make test` sind Wrapper. Build- und Paketprüfungen gehören zum vollständigen Lauf. Echte VM-Installationen und Clusteränderungen bleiben außerhalb dieser CI und werden nur ausdrücklich über die fachlichen E2E-Ziele gestartet.

Release-Tags müssen zur Version in `galaxy.yml` passen. Das GitHub-Release enthält das zuvor geprüfte Archiv; eine Galaxy-Publikation erfolgt nicht automatisch. Der abgeglichene Repository-Vertrag steht in [repository-standard.md](repository-standard.md).
