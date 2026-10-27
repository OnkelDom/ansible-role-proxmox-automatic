# `degitag.proxmox.deploy`

Deployment koordinieren. Öffentlicher Haupteinstieg: validiert die strukturierte und die kompatible Legacy-Konfiguration, prüft VM-Identität und orchestriert Cluster-Ressourcen, Medien, VM, Gast und HA.

## Schnittstelle

proxmox_api, proxmox_vm, proxmox_install, proxmox_guest, proxmox_deploy, proxmox_ha, proxmox_firewall und proxmox_cluster_firewall. Vollständige Beispiele stehen in der Root-README.

Öffentliche Variablen werden nicht durch Rollen-Facts ersetzt. Interne Zustände tragen das Präfix `_proxmox_`. Laufzeitvoraussetzungen, Plattformgrenzen und Betriebsabläufe stehen in der [Collection-README](../../README.md).

## Prüfung und Betriebsgrenzen

`bash tests/run_checks.sh` im Repository-Root prüft Syntax und die fachlichen Unit-/Template-/Medien-Fixtures. Syntaxprüfungen führen diese Rolle nicht gegen einen Gast oder Cluster aus. Echte Proxmox-Abnahme bleibt ein ausdrücklich gestarteter E2E-Lauf.
