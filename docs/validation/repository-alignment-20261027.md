# Repository-Angleichung vom 27.10.2026

## Abstimmung und Zuständigkeit

Infrastructure koordinierte den gemeinsamen Vertrag `degitag-collections-v1`. Database, Monitoring und Proxmox bearbeiteten jeweils ihr eigenes Repository. K3s wurde zunächst durch Infrastructure angeglichen und anschließend ausdrücklich an den neu hinzugekommenen K3s-Chat zur weiteren Verifikation übergeben. `ansible-collection-default-server` ist ein Symlink auf Infrastructure und kein sechstes Repository.

Alle acht gemeinsamen Dateien wurden direkt über die fünf Repositories verglichen und sind bytegleich. Hashes, Prüfbasis und Paketbezug stehen in [repository-standard-2026-10-27.json](repository-standard-2026-10-27.json). Der Stand liegt lokal auf `codex/collection-repository-standard`, ausgehend von `ec4a808`.

## Umgesetzter Proxmox-Umfang

- Gemeinsame Rootstruktur, README-H2-Reihenfolge, EditorConfig und Beitrags-/Sicherheitsdokumentation.
- Anforderungen unter `requirements.yml` und `requirements-test.txt`, Entwicklungswerkzeuge unter `tools/`.
- Vollständiger Einstieg `bash tests/run_checks.sh`; Make-Ziele sind Wrapper auf dieselben Stufen.
- Python 3.12 und ansible-core >=2.20.10,<2.22 als dokumentierter Controller-Supportwechsel.
- Core-Matrix 2.20/2.21, minimale Workflow-Rechte, SHA-gepinnte Actions, Dependabot und geprüfter Tag-Release-Workflow.
- Identische Repository-/Artefaktprüfer, alle Rollen-/Playbook-Syntaxchecks und Compile-/Import-Sanity.
- Bestehende Firewall-, Installer-, BIOS-/UEFI- und Mediencache-Prüfungen erhalten.
- Klare Rollen-READMEs und Metadaten; interne Rollen benötigen weiterhin `_proxmox_config`.
- Runtime-Paket ohne Tests, Caches und Entwicklungsdokumente. Drei Legacy-Symlinks werden ausschließlich im temporären Build-Staging materialisiert.

Der isolierte Paket-Smoke wurde korrigiert: Sowohl Galaxy-Installation als auch anschließende Ausführung verwenden nur das neue Installationsziel; ein geerbter Checkout kann die Installation nicht mehr überspringen. Compile-/Import-Sanity deckte außerdem den unbedingten `requests`-Import auf. Der Import ist nun optional, die API-Nutzung meldet eine fehlende Laufzeitabhängigkeit klar und wird durch einen zusätzlichen Unit-Test abgedeckt.

36 bestehende YAML-Dateien wurden ausschließlich formatiert; der semantische Vergleich gegen die Prüfbasis war identisch. Inhaltliche Änderungen betreffen die beabsichtigten Metadaten, den Prüfeinstieg, Paketbau und Workflows. Unbelegte historische Compliance- und Reaktionszeit-Zusagen wurden aus SECURITY.md entfernt.

## Tatsächlich ausgeführte Prüfungen

| Umgebung | Vollständiger Einstieg | Ergebnis |
|---|---|---|
| macOS, Python 3.12.16, Core 2.21.5 | `bash tests/run_checks.sh` | Exit 0; 67 Tests und 3 Subtests |
| macOS, Python 3.12.16, Core 2.20.10 | `bash tests/run_checks.sh` | Exit 0; 67 Tests und 3 Subtests |

Beide Läufe enthalten Repository-Vertrag, Production-Lint, YAML-Lint, Syntax aller sechs Rollen und der Test-/Betriebsplaybooks, Unit-Tests, Firewall-/Installer-Rendering, sichere Eingabevorprüfung, Medienbau mit Wiederholung und Korruptions-Rebuild, BIOS-/UEFI-Einträge, strikten Paketcheck, isolierte Neuinstallation mit Legacy-Adapter sowie `ansible-test sanity` für Compile und Import.

Zusätzlich geprüft: README-Links, Anker und YAML-Beispiele, Shell-Syntax der drei Test-Runner, Existenz der gepinnten Action-Commits per GitHub-API und `git diff --check`. Das finale Paket enthält 116 Einträge ohne Symlinks; dessen SHA256 ist im JSON-Nachweis erfasst.

## Grenzen und Veröffentlichungsstatus

Es wurden keine echten VMs installiert oder verändert und keine produktiven Systeme angesprochen. Die ISO-Fixtures enthalten absichtlich keine bootfähige Betriebssysteminstallation. Die Linux-nftables-Kernelprüfung entfällt auf macOS und wird erst im neuen Linux-CI-Lauf ausgeführt. Diese Strukturprüfung ersetzt keine Live-Abnahme.

Die neuen Workflows sind eingerichtet und statisch geprüft; sie wurden für diesen lokalen Stand nicht auf GitHub ausgeführt. Es wurden kein Push, kein Tag, kein GitHub-Release und keine Galaxy-Publikation vorgenommen. Der Repository-Name und die GitHub-Zuordnung bleiben bestehen.
