# `degitag.proxmox.vm`

VM-Lifecycle verwalten. Interne Deployment-Phase: erstellt neue VMs, steuert Installer-/Systemboot, nimmt eigene Installationen wieder auf und wendet ausdrücklich erlaubte Hardware-Updates an.

## Schnittstelle

Benötigt _proxmox_config und den durch deploy geprüften VM-Zustand. Die Rolle darf nicht ohne Identitätsprüfung als allgemeine VM-Update-Rolle aufgerufen werden.

Öffentliche Variablen werden nicht durch Rollen-Facts ersetzt. Interne Zustände tragen das Präfix `_proxmox_`. Laufzeitvoraussetzungen, Plattformgrenzen und Betriebsabläufe stehen in der [Collection-README](../../README.md).

## Prüfung und Betriebsgrenzen

`bash tests/run_checks.sh` im Repository-Root prüft Syntax und die fachlichen Unit-/Template-/Medien-Fixtures. Syntaxprüfungen führen diese Rolle nicht gegen einen Gast oder Cluster aus. Echte Proxmox-Abnahme bleibt ein ausdrücklich gestarteter E2E-Lauf.
