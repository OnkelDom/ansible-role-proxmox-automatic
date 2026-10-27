# Gemeinsamer Repository-Standard

Vertrag: `degitag-collections-v1`, abgestimmt am 2026-10-27 zwischen den Verantwortlichen fuer Infrastructure, Database, Monitoring, K3s und Proxmox. Diese Datei und die generischen Pruefwerkzeuge werden identisch in den fuenf Repositories gepflegt. Aenderungen daran werden zuerst zwischen den Repository-Verantwortlichen abgestimmt und anschliessend mit identischem Inhalt uebernommen.

## Verantwortung

| Collection | Verantwortungsbereich |
| --- | --- |
| `degitag.infrastructure` | Linux-Baseline, Host-Netzwerk, Firewall und allgemeine Dienste |
| `degitag.database` | Datenbanken, Caches und Datenbank-HA |
| `degitag.monitoring` | Monitoringdienste, Agenten, Exporter und Alarmregeln |
| `degitag.k3s` | K3s-Lifecycle und Kubernetes-Integrationen |
| `degitag.proxmox` | Proxmox-Installation und Host-/Gastkonfiguration |

`ansible-collection-default-server` ist lokal ein Symlink auf Infrastructure und kein zusaetzliches Repository. Jede Arbeitsgruppe schreibt nur in ihr zugewiesenes Repository. Bestehende lokale Aenderungen bleiben erhalten. Eine Strukturangleichung autorisiert keine produktiven Deployments, Datenmigrationen, Repository-Transfers oder Veroeffentlichungen.

## Struktur

Verbindliche Rootdateien: `README.md`, `CHANGELOG.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `.editorconfig`, `Makefile`, `galaxy.yml`, `ansible.cfg`, `requirements.yml`, `requirements-test.txt` und die Ansible-/YAML-Lint-Konfiguration. Hinzu kommen `meta/runtime.yml`, `.github/dependabot.yml` sowie `.github/workflows/ci.yml` und `release.yml`.

| Pfad | Inhalt |
| --- | --- |
| `roles/` | Oeffentliche Rollen mit typisierter API; interne Rollen klar kennzeichnen |
| `plugins/` | Collection-Plugins, sofern vorhanden |
| `playbooks/`, `examples/` | Ausfuehrbare Einstiege bzw. Beispiele, sofern vorhanden |
| `tests/unit/` | Isolierte Unit- und Vertragspruefungen |
| `tests/integration/` | Fachliche Integrationstests, soweit vorhanden |
| `tests/run_checks.sh` | Einziger vollstaendiger lokaler und CI-Pruefeinstieg |
| `tools/` | Generatoren, Formatter und Vertrags-/Artefaktpruefer |
| `docs/migration.md` | Inkompatible Aenderungen und Betreiber-Migration |
| `docs/repository-standard.md` | Dieser gemeinsame Vertrag |
| `docs/validation/` | Datierte Nachweise, Artefaktbezug und offene Testluecken |

Leere Verzeichnisse und leere Abhaengigkeitsdateien werden nicht als Platzhalter angelegt. `requirements-dev.yml` enthaelt ausschliesslich benoetigte Test-Collections. Lokale `.venv`, `.ansible`, Caches, Artefakte und Secrets sind ignoriert und gelangen nicht ins Release-Artefakt. Lizenzen importierter Rollen und Plugins bleiben erhalten; keine pauschale Umlizenzierung.

## README und Mitarbeit

Die README beginnt mit Collection-Identitaet, Badges und einer kurzen Aufgabenbeschreibung. Die H2-Kapitel stehen in dieser Reihenfolge:

1. Verantwortung und Architektur
2. Plattformen und Laufzeit
3. Installation
4. Verwendung
5. Rollen
6. Repository-Struktur
7. Entwicklung und Checks
8. CI und Releases
9. Migration
10. Sicherheit
11. Lizenz

Fachliche Erlaeuterungen werden darunter als H3 gegliedert. Installation, Quellen der Wahrheit, Abhaengigkeiten, Betriebsgrenzen und belegte Testluecken muessen erkennbar sein. Dokumentation wird aus DevOps-/Systemarchitektur-Sicht geschrieben; Anleitungen verwenden `vim`. `CONTRIBUTING.md` beschreibt lokale Einrichtung und Review-Ablauf. `SECURITY.md` beschreibt den vertraulichen Meldeweg und den Umgang mit Secrets. Betriebsdokumentation in Outline entsteht nur im ausdruecklichen Auftragsumfang.

## Rollenvertrag und Ausnahmen

Infrastructure, Database, Monitoring und K3s verwenden den bestehenden Scaffold-Generator: Defaults, Rollenmetadaten, typisierte Argument-Specs, README, Fact-sammelndes Testplaybook, generierter Einstieg mit Preflight und Import von `configuration.yml`, geschichtete Plattformvariablen. Oeffentliche Defaults sind vor dem Preflight auswertbar. Facts werden ueber `ansible_facts` verwendet. Dienstschalter gelten auch fuer Handler. Plattform- und Rollen-Lizenzen bleiben individuell konfigurierbar.

Proxmox ist eine vollwertige Collection mit einem zusaetzlichen Legacy-Rollenadapter in den Rootpfaden. Interne Rollen mit `_proxmox_config` versprechen keinen eigenstaendigen oeffentlichen Aufruf. Vorbereitungsadapter und Installer-/BIOS-/UEFI-Medientests bleiben bestehen. Diese dokumentierte Ausnahme erzwingt keinen fachlich falschen Scaffold. Abweichende Mindestversionen oder Zusatzmatrizen werden in README, Metadaten und Migration konsistent dokumentiert.

## Toolchain und Pruefeinstiege

Die gemeinsame CI-Basis ist Python 3.12 mit Ansible Core 2.20 und 2.21. Zusaetzliche aeltere Kombinationen sind nur mit passenden Python-/Core-Paaren und belegten Tests zulaessig. `requirements-test.txt` definiert die Controller-Werkzeuge, `requirements.yml` die Collection-Abhaengigkeiten. Auf macOS wird Homebrew Python ohne sudo fuer `.venv` verwendet.

`make prepare`, `lint`, `syntax`, `unit`, `test`, `ci`, `build` und `package-smoke` bilden die gemeinsame Bedienoberflaeche. Make ist ein duenner Wrapper: `make test` und `make ci` rufen `bash tests/run_checks.sh` auf. Dieses Skript ruft nicht wieder Make auf. `make prepare` installiert Entwicklungsabhaengigkeiten; erforderliche lokale Geschwister-Collections werden zuvor gebaut und installiert. Fachliche Zusatzpruefungen bleiben als benannte Hooks im Skript oder als nachgelagerte CI-Jobs erhalten.

Der vollstaendige Prueflauf umfasst Repository-Vertrag, Scaffold (soweit verwendet), Unit-Tests, YAML-Lint, Build, Artefaktidentitaet/-Version/-Dateihashes/-Grenzen, Installation, vorhandene sichere Preflight-/Renderpruefungen, alle Rollen-Syntaxchecks mit Facts, Ansible-Lint `production` sowie `ansible-test sanity` fuer Compile und Import. Sanity laeuft mit Python 3.12 in einem temporaeren Collection-Verzeichnis ausserhalb ignorierter Checkoutpfade. Artefaktnamen und Installationspfade werden aus `galaxy.yml` abgeleitet. Monitoring fuehrt zusaetzlich eigene Binaer-Provenienz- und Regelpruefungen aus; Proxmox prueft Legacy-Adapter und Installer-Medien.

## CI, Release und Abnahme

CI verwendet nach dem Dependency-Setup denselben `bash tests/run_checks.sh`-Einstieg. Actions werden nach Commit-SHA referenziert, Checkout-Credentials nicht persistiert, Berechtigungen minimal gesetzt und Dependabot fuer Actions/Python gepflegt. Workflow-Shelltexte bleiben lesbare Blockskalare. Die Core-Matrix umfasst 2.20/2.21 unter Python 3.12. Ein internes Geschwister-Repository wird explizit ausgecheckt und vorab gebaut; ein benoetigtes Lesetoken ist dokumentiert. Es gibt keine stillschweigende Abhaengigkeit von einem lokalen Geschwisterpfad im CI-Runner.

Releases erfordern einen expliziten `v<galaxy-version>`-Tag und erfolgreich abgeschlossene Checks. Das konkret benannte Artefakt wird geprueft und als GitHub-Release angehaengt. Keine implizite Galaxy-Publikation. Controller-, Dokumentations- und Entwicklungsdateien gehoeren nicht ins Collection-Artefakt.

Container-Smoke und vorhandene Functional-Tests bleiben fachlich passend: Infrastructure/Database pruefen ihre freie Plattformmatrix mit zweitem Lauf `changed=0`; Monitoring prueft native Agenten, Exporter, Alarm- und Inhibition-Regeln; K3s benoetigt dedizierte Cluster-VMs; Proxmox prueft Installer-Medien und separat echte Installationen. Netzwerk, Firewall, Dienste, SELinux und Reboots brauchen echte Testgaeste. Keine Fake-Smokes und keine pauschale Laufzeitabnahme aus Syntaxchecks. Fehlende Docker-/VM-/Repository-Zugaenge werden im datierten Nachweis benannt. Historische Berichte und Hashes werden nicht nachtraeglich umetikettiert.
