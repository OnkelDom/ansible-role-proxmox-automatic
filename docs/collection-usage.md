# Zusammenspiel der Collections

| Collection | Zuständigkeit |
|---|---|
| `degitag.infrastructure` | Linux-Baseline, Host-Netzwerk, Gast-Firewall und allgemeine Dienste |
| `degitag.database` | Datenbanken, Caches und Datenbank-HA |
| `degitag.monitoring` | Monitoringdienste, Agenten, Exporter und Alarmregeln |
| `degitag.k3s` | K3s-Lifecycle und Kubernetes-Integration |
| `degitag.proxmox` | VM-Installation auf Proxmox, zentrale PVE-Firewall und begrenzte Gastkonfiguration |

Proxmox benötigt keine dieser Geschwister-Collections als implizite Laufzeitabhängigkeit. Externe Abhängigkeiten stehen in `galaxy.yml`; die reproduzierbare Entwicklerinstallation steht in `requirements.yml`. Ein anderer lokaler Checkout wird nicht stillschweigend in der CI vorausgesetzt.

Allgemeine Gast-Baselines und Patchmanagement gehören in Infrastructure, Datenbankdienste in Database und laufende Agenten-/Exporterpflege in Monitoring. Wenn diese Rollen Benutzer, Pakete, Sysctl oder Gast-Firewall verwalten, müssen die entsprechenden optionalen Proxmox-Gastschritte im Inventory gezielt abgegrenzt werden. Zwei Rollen sollen nicht dieselben Ressourcen unabhängig besitzen.

Die PVE-Firewall verwaltet Policies am Hypervisor. Die optionale Proxmox-Gast-Firewall verwendet eine eigene Tabelle; sie ist kein Ersatz für eine abgestimmte allgemeine Host-Baseline. Der eigenständige PVE-Metrikserver konfiguriert den Export aus PVE; Receiver, Dashboards und Alarme gehören zu Monitoring.

Quellen der Wahrheit für Ziele, Clusteridentitäten und Secrets sind die ausdrücklich zugeordneten Infrastruktur-Inventories. Der gemeinsame Entwicklungsvertrag liegt in [repository-standard.md](repository-standard.md); operative Anleitungen werden in Outline gepflegt.
