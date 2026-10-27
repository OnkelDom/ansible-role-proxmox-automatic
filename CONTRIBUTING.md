# Entwicklung und Abnahme

Der Entwicklungsstand wird als Collection `degitag.proxmox` gebaut. Der bisherige Rollenname bleibt ein Kompatibilitätseinstieg. Änderungen an Inventories, Proxmox-Clustern oder Gastbetriebssystemen sind kein Bestandteil der lokalen CI.

## Entwicklungsumgebung

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
ansible-galaxy collection install -r collections/requirements.yml
make prepare
make ci
make build
```

Auf dem Controller werden `xorriso` und `perl` benötigt. Für die nftables-Syntaxprüfung auf Linux sind zusätzlich nftables und die dafür nötigen lokalen Rechte erforderlich. Auf macOS werden Rendering und Modell geprüft; die Linux-Kernelprüfung entfällt.

## Zuständigkeiten

- `roles/deploy`: Phasen und Sicherheitsgrenzen des Deployments.
- `roles/cluster_resources`: Zentrale Firewall-Objekte, Pools, VM-Referenzen und HA.
- `roles/install_media`: Deterministische Installer-Konfiguration und Medien-Lifecycle.
- `roles/vm`: Hardware und Installationszustand ohne automatischen Disk-Ersatz.
- `roles/guest`: Verifikation und begrenzte Bootstrap-Konfiguration.
- `plugins/filter/config.py`: Öffentliche Konfiguration normalisieren und vor Änderungen validieren.
- `plugins/module_utils`: API-Zugriff, stabile Regelidentitäten und Änderungsjournale.

Öffentliche Variablen werden nicht durch Facts überschrieben. Die Rollen verwenden einen dokumentierten Collection-weiten Kontext `_proxmox_config`; deshalb ist ausschließlich die rollenbezogene Präfixregel des Linters ausgenommen. Andere Variablen- und YAML-Prüfungen bleiben aktiv.

## Prüfungen

`make ci` führt Lint, Syntax, Python-Tests, Template-Rendering, Produktions-Preflight und Medien-Fixtures aus. Die Medien-Fixture enthält absichtlich keinen bootfähigen Kernel; geprüft werden ISO-Struktur, Bootmenü, Label, eingebettete Konfiguration, Pfade mit Leerzeichen und Cache-Integrität.

Für Änderungen an API-Modulen sind Erhalt fremder Ressourcen, Wiederholungslauf, Check-Mode und Fehlerpfad relevant. Bei Firewall-Regeln müssen Namensidentität, Reihenfolge und entfernte optionale Felder geprüft werden. Bei HA müssen fremde Mitglieder erhalten bleiben und Digests zwischen Änderungen frisch gelesen werden.

Echte Proxmox-Tests erfolgen ausschließlich in einer ausdrücklich festgelegten Testumgebung:

```bash
make e2e-syntax
make e2e
make e2e-cleanup
```

Die Ziele und Zugangsdaten werden über die in `tests/proxmox_e2e.yml` genannten Umgebungsvariablen gesetzt. Die reservierten VMIDs, Namen, Quell-ISOs und Netzwerkziele vor Ausführung prüfen. Die Bereinigung verweigert fremde VM-Identitäten und entfernt keine unveränderlichen Remote-ISOs.

## Änderungen dokumentieren

Auswirkungen auf Laufzeitverhalten, unterstützte Installer, Variablen und Migration in README und Changelog beschreiben. Die Betriebsdokumentation liegt zusätzlich in Lenmail-Outline unter Proxmox. Keine Secrets, privaten Schlüssel oder erzeugten Installer-Artefakte einchecken. Für lokale Anleitungen `vim` verwenden.
