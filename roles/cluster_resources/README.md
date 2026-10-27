# `degitag.proxmox.cluster_resources`

Zentrale Cluster-Ressourcen. Eigenständiger Haupteinstieg für zentrale Proxmox-Firewall-Policies. Das Deployment verwendet zusätzlich interne Task-Einstiege für Pools, VM-Firewall und HA.

## Schnittstelle

Der eigenständige Einstieg verwendet proxmox_api und proxmox_cluster_firewall. Die internen Einstiege benötigen den normalisierten _proxmox_config-Kontext aus deploy.

Öffentliche Variablen werden nicht durch Rollen-Facts ersetzt. Interne Zustände tragen das Präfix `_proxmox_`. Laufzeitvoraussetzungen, Plattformgrenzen und Betriebsabläufe stehen in der [Collection-README](../../README.md).

## Prüfung und Betriebsgrenzen

`bash tests/run_checks.sh` im Repository-Root prüft Syntax und die fachlichen Unit-/Template-/Medien-Fixtures. Syntaxprüfungen führen diese Rolle nicht gegen einen Gast oder Cluster aus. Echte Proxmox-Abnahme bleibt ein ausdrücklich gestarteter E2E-Lauf.
