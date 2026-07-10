# Architektur

## Systemkontext

```text
Statischer Hostingserver
  └─ HTML, CSS, JavaScript, WebAssembly, Fonts, Icons
             │
             ▼
Browser / installierte PWA
  ├─ Benutzeroberfläche
  ├─ Geschäftslogik
  ├─ SQLite-WASM im Web Worker
  ├─ lokale PDF-Erzeugung
  ├─ lokale Verschlüsselung
  ├─ Backup und Restore
  └─ File System Access API
             │
             ▼
Lokaler Praxisordner
  ├─ database/praxis.sqlite
  ├─ documents/invoices/
  ├─ documents/reminders/
  ├─ attachments/
  └─ backups/
```

Der Server ist kein fachliches Backend. Er liefert nur unveränderliche, versionierte Programmdateien aus. Alle fachlichen Daten und Berechnungen verbleiben lokal.

## PWA

Die Anwendung besitzt ein Web-App-Manifest und einen Service Worker. Nach dem ersten erfolgreichen Laden werden alle für den Betrieb erforderlichen Dateien lokal gecacht. Ein kontrollierter Updateprozess aktiviert neue Versionen erst nach Abschluss laufender Arbeit und nach einer erforderlichen Datensicherung.

## Persistenz

SQLite ist die primäre Datenhaltung. Die Engine wird als WebAssembly ausgeliefert und in einem Web Worker betrieben. Ziel ist eine normale Datenbankdatei im freigegebenen Praxisordner. Falls die gewählte SQLite-WASM-Integration direkte persistente Zugriffe auf diesen Ordner nicht zuverlässig unterstützt, wird OPFS als Arbeitsdatenbank verwendet und transaktional in den Praxisordner gesichert. Diese Entscheidung ist vor Implementierung als ADR festzuhalten.

## Praxisordner

Vorgesehene Struktur:

```text
SimplyAbrechnung_Daten/
  app-info.json
  database/
    praxis.sqlite
  documents/
    invoices/
    reminders/
  attachments/
  backups/
```

Der Benutzer wählt den Ordner ausdrücklich. Der `FileSystemDirectoryHandle` kann in IndexedDB gespeichert werden. Beim nächsten Start wird die Berechtigung geprüft; der Browser darf eine erneute Freigabe verlangen.

## Schichten

- `domain`: reine Fachobjekte und Invarianten
- `application`: Anwendungsfälle und Transaktionsgrenzen
- `database`: Schema, Migrationen und Repositories
- `filesystem`: Praxisordner, Export, Import und Dateizugriff
- `documents`: PDF-Erzeugung und Dokument-Snapshots
- `security`: Verschlüsselung, Schlüsselableitung und Sperrlogik
- `ui`: Komponenten, Navigation und Zustandsdarstellung

Die Domain darf keine Abhängigkeit auf Browser-APIs, UI-Framework oder konkrete SQLite-Bibliotheken besitzen.

## Transaktionen

Folgende Vorgänge müssen atomar sein:

- Rechnung finalisieren
- Leistungen einer Rechnung zuordnen
- nächste Rechnungsnummer reservieren
- Zahlung erfassen und Status aktualisieren
- Storno oder Gutschrift erfassen
- JSON-Bestand importieren
- Schema migrieren

PDF-Dateien werden aus einem bereits finalisierten Rechnungs-Snapshot erzeugt. Scheitert die Dateierzeugung, bleibt der fachliche Datensatz nachvollziehbar und die Erzeugung kann wiederholt werden.

## Netzwerkgrenze

Zulässige Requests:

- statische Anwendungsdateien
- Updateprüfung derselben Origin

Unzulässige Requests:

- Patientendaten
- Diagnosen und Notizen
- Leistungen und Rechnungsdaten
- Praxisstammdaten
- Datei- oder Datenbankinhalte
- fachliche Fehlerdetails

Externe Fonts, CDNs, Analyse- und Telemetriedienste sind nicht vorgesehen.

## Hosting

GitHub Pages kann für Entwicklung und Prototyping verwendet werden. Für produktive Nutzung ist statisches Hosting mit eigener Domain und kontrollierbaren Sicherheitsheadern vorgesehen. Es bleibt auch dort eine reine statische Bereitstellung ohne fachliches Backend.
