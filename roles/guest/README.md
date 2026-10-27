# `degitag.proxmox.guest`

Gast prüfen und konfigurieren. Interne Deployment-Phase: prüft Betriebssystem, Mountpoints und Adressen, pflegt begrenzte Bootstrap-Einstellungen und optional eine eigene nftables-Policy.

## Schnittstelle

Benötigt _proxmox_config, SSH-Delegation, passenden Benutzer und become. playbooks/configure_guests.yml stellt den dokumentierten Einstieg für vorhandene Gäste bereit.

Öffentliche Variablen werden nicht durch Rollen-Facts ersetzt. Interne Zustände tragen das Präfix `_proxmox_`. Laufzeitvoraussetzungen, Plattformgrenzen und Betriebsabläufe stehen in der [Collection-README](../../README.md).

## Prüfung und Betriebsgrenzen

`bash tests/run_checks.sh` im Repository-Root prüft Syntax und die fachlichen Unit-/Template-/Medien-Fixtures. Syntaxprüfungen führen diese Rolle nicht gegen einen Gast oder Cluster aus. Echte Proxmox-Abnahme bleibt ein ausdrücklich gestarteter E2E-Lauf.
