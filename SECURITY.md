# Sicherheit

## Unterstützter Stand

Sicherheitskorrekturen werden für den aktuellen Collection-Stand auf `main` entwickelt. Der frühere Standalone-Rollenname wird als Adapter erhalten; daraus ergibt sich keine Zusage zur Pflege aller historischen Rollen-Releases. Unterstützte Controller-Versionen stehen in `meta/runtime.yml` und der README.

## Vertrauliche Meldungen

Sicherheitslücken mit reproduzierbarem Beispiel und betroffener Version vertraulich an den Repository-Maintainer melden. Falls GitHub private Sicherheitsmeldungen für das Repository anbietet, diese verwenden. Keine produktiven Zugangsdaten, privaten Schlüssel, vollständigen Installer-Medien oder Firewall-Journale in öffentliche Issues hochladen. Rückmelde- und Behebungsfristen werden nicht pauschal zugesagt.

## API, SSH und Geheimnisse

API-Zugänge mit passenden, begrenzten Rechten verwenden. TLS-Zertifikatsprüfung ist standardmäßig aktiv; interne CAs gehören in den Truststore. Geheimnisse über Ansible Vault oder einen externen Secret Store zuführen. Die Collection deaktiviert keine SSH-Hostkey-Prüfung. Nach Neuinstallation neue Hostkeys über einen unabhängig authentifizierten Weg abgleichen.

Installer-Konfigurationen und ISOs können Passwort-Hashes enthalten. Lokale Konfigurationen, ISOs und Manifeste werden mit `0600`, Arbeitsverzeichnisse mit `0700` angelegt. Firewall-Änderungsjournale enthalten betriebliche Ausgangszustände und geplante Operationen. Solche Dateien gehören weder ins Repository noch in das Collection-Paket. Remote-ISO-Retention muss anhand der tatsächlichen VM-Referenzen geplant werden.

## Grenzen bei Firewall und Neuinstallation

Proxmox-API-Änderungen sind keine atomare Transaktion. Journale ermöglichen eine gezielte Wiederherstellung; es gibt keinen automatischen vollständigen Rollback. Restriktive Policies benötigen funktionierende Management-Ausnahmen und einen vorbereiteten Rückweg.

`reinstall: true` erlaubt eine Neuinstallation und Neupartitionierung der konfigurierten Gastdisks. Die VM muss vorher bewusst gestoppt sein; Datenbackup und Wiederherstellungsweg gehören zur Betriebsfreigabe. Check-Mode simuliert keine vollständige Betriebssysteminstallation.

## Belegte Aussagen

Lokale und GitHub-Prüfungen umfassen Repository-Struktur, Syntax, isolierte API-Tests, Firewall-/Installer-Rendering und nicht bootfähige Medien-Fixtures. Sie sind keine vollständige Sicherheitsprüfung eines Proxmox-Clusters. CIS-, BSI- oder NIST-Konformität und eine erfolgreiche Live-Abnahme werden daraus nicht abgeleitet. Produktive Änderungen und echte E2E-Läufe sind eigene, ausdrücklich beauftragte Betriebsaktionen.
