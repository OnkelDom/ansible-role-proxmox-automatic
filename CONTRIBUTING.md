# Entwicklung und Beiträge

Die Collection folgt dem gemeinsam abgestimmten [Repository-Standard](docs/repository-standard.md). Betriebsdokumentation wird in [Outline](https://docs.lenmail.de) gepflegt; dieses Repository enthält die direkt zur Implementierung gehörenden Einstiege, Konfigurationsreferenzen und Prüfnachweise.

## Entwicklungsumgebung

Python 3.12 und ansible-core >=2.20.10,<2.22 verwenden. Auf dem Controller werden `xorriso` und `perl` benötigt; Linux prüft zusätzlich nftables. Eine aktive virtuelle Umgebung wird von den Prüfskripten respektiert.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-test.txt
ansible-galaxy collection install -r requirements.yml
make prepare
bash tests/run_checks.sh
```

Für lokale Dateiänderungen `vim` verwenden. API-Tokens, Vault-Passwörter, Installer-Medien, Firewall-Journale und Laufzeitprotokolle gehören nicht in Git oder das Collection-Archiv.

## Ein gemeinsamer Prüfeinstieg

`bash tests/run_checks.sh` führt die vollständige lokale CI aus. `make test` und `make ci` delegieren an diesen Einstieg; GitHub verwendet denselben Ablauf. Teilprüfungen stehen als Make-Ziele bereit und verwenden dieselben Stufen des Skripts:

| Ziel | Zweck |
|---|---|
| `prepare` | Checkout als Collection und Legacy-Rolle lokal verfügbar machen |
| `lint` | Repository-Vertrag, YAML, Ansible-Lint und Python-Kompilierung |
| `syntax` | Playbooks und Testeinstiege auflösbar und syntaktisch prüfen |
| `unit` | Unit-Tests für Normalisierung, API, Firewall, HA, Upload und Metriken |
| `test`, `ci` | vollständiger nichtproduktiver Prüflauf |
| `build` | Collection bauen, ohne sie zu veröffentlichen |
| `package-smoke` | Archiv prüfen und frisch installiert einschließlich Legacy-Adapter testen |

`make render` und `make media` prüfen die fachlichen Installer-/Firewall-Templates und ISO-Fixtures. Die Fixtures sind absichtlich nicht bootfähig; sie prüfen Struktur, BIOS-/UEFI-Einträge, Bootmenüs, Cache-Wiederholung und Pfade mit Leerzeichen. Diese Prüfungen bestätigen keine Installation eines echten Betriebssystems.

## Zuständigkeiten und Schnittstellen

- `roles/deploy` normalisiert Eingaben und koordiniert das Deployment.
- `roles/cluster_resources` verwaltet zentrale Firewall-Objekte, VM-Gruppenreferenzen, Pools und HA.
- `roles/install_media`, `roles/vm` und `roles/guest` sind interne Phasen mit validiertem `_proxmox_config`-Kontext.
- `roles/metric_server` bietet einen eigenständigen Einstieg für den nativen PVE-Metrikexport.
- `plugins/filter/config.py` definiert die öffentliche Normalisierung und Validierung.
- `plugins/module_utils` enthält API-Zugriff, Eigentumsmarker, stabile Regelidentitäten und Änderungsjournale.
- Root-Dateien unter `defaults/`, `tasks/`, `templates/` und `meta/` erhalten den alten Rollenaufruf `proxmox_automatic`.

Öffentliche Inventory-Variablen werden nicht durch Facts überschrieben. Die gemeinsame interne Variable `_proxmox_config` ist eine dokumentierte Ausnahme von rollenbezogenen Variablenpräfixen. Neue Funktionen gehören in die Collection, nicht in eine zweite Implementierung im Root-Adapter.

## Aussagekräftige Prüfungen

API-Änderungen prüfen mindestens Idempotenz, Check-Mode, Erhalt fremder Ressourcen und Fehlerpfade. Firewall-Änderungen müssen Regelidentität, Reihenfolge und entfernte optionale Felder berücksichtigen. HA-Änderungen müssen fremde Mitglieder erhalten und aktuelle Digests verwenden. Installer-Änderungen müssen BIOS und UEFI sowie die Cache-Integrität berücksichtigen.

Echte Proxmox-Tests benötigen eine ausdrücklich festgelegte Testumgebung und werden nicht durch die CI gestartet:

```bash
make e2e-syntax
make e2e
make e2e-cleanup
```

Ziele, reservierte VMIDs, Namen, Quell-ISOs und Netzwerke gemäß `tests/proxmox_e2e.yml` vor Ausführung prüfen. Cleanup prüft VM-Identität und Eigentumsmarker; unveränderliche Remote-ISOs werden nicht automatisch gelöscht. Laufende Gäste anderer Tests dürfen nicht verändert werden.

## Änderungen und Releases

Verhaltensänderungen und Migrationen in README, Changelog und gegebenenfalls `docs/migration.md` dokumentieren. Testberichte unter `docs/validation/` benennen Commit, Umgebung, tatsächlich ausgeführte Prüfungen und verbleibende Grenzen. Ein grüner Template-Test darf nicht als Live-Abnahme beschrieben werden.

Release-Tags müssen zur Version in `galaxy.yml` passen. Der Release-Workflow prüft den Stand vor Erzeugung des GitHub-Release-Artefakts. Eine automatische Galaxy-Publikation ist nicht vorgesehen.
