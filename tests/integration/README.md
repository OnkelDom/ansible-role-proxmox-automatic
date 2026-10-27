# Proxmox-Integrationsprüfungen

Die vorhandenen Playbook-Pfade bleiben als stabile Entwicklungseinstiege erhalten. `bash tests/run_checks.sh` führt die sicheren lokalen Fixtures aus:

| Einstieg | Aussage |
|---|---|
| `tests/configuration.yml` | strukturierte Konfiguration, Firewall-Templates und Reinstall-Verhalten rendern |
| `tests/render_templates.yml` | Rocky-/Debian-Installer, Netzwerk- und Storage-Varianten rendern |
| `tests/build_media.yml` | isolierte ISO-Fixtures, BIOS/UEFI, Mediencache, Korruptions-Wiederaufbau und Pfade mit Leerzeichen prüfen |
| `tests/preflight.yml --tags proxmox_validate` | neuen Collection- und alten Rollenaufruf ohne API-Zugriff validieren |

`tests/proxmox_e2e*.yml` sind gesonderte Live-Tests mit echten VMs. Sie gehören nicht zum automatischen Prüfeinstieg. Die ISO-Fixtures enthalten keine bootfähige Betriebssysteminstallation und ersetzen diese Live-Abnahme nicht.
