# `degitag.proxmox.install_media`

Installer-Medien erzeugen. Interne Deployment-Phase: erzeugt Rocky-Kickstart-Konfigurations-CDs beziehungsweise remasterte Debian-ISOs und lädt sie bei Bedarf hoch.

## Schnittstelle

Benötigt _proxmox_config, normalisiert durch deploy (tasks_from: normalize_media für Medien-only-Aufrufe). Direkte unnormalisierte Variablen sind keine öffentliche Schnittstelle.

Öffentliche Variablen werden nicht durch Rollen-Facts ersetzt. Interne Zustände tragen das Präfix `_proxmox_`. Laufzeitvoraussetzungen, Plattformgrenzen und Betriebsabläufe stehen in der [Collection-README](../../README.md).

## Prüfung und Betriebsgrenzen

`bash tests/run_checks.sh` im Repository-Root prüft Syntax und die fachlichen Unit-/Template-/Medien-Fixtures. Syntaxprüfungen führen diese Rolle nicht gegen einen Gast oder Cluster aus. Echte Proxmox-Abnahme bleibt ein ausdrücklich gestarteter E2E-Lauf.
