# SimplyAbrechnung Web

SimplyAbrechnung wird als lokale, installierbare Webanwendung (PWA) neu entwickelt. Der Server liefert ausschließlich statische Anwendungsdateien aus. Patienten-, Diagnose-, Leistungs-, Rechnungs- und Zahlungsdaten werden ausschließlich lokal im Browser beziehungsweise in einem vom Benutzer freigegebenen Praxisordner verarbeitet.

Der bisherige Desktopstand 0.5.0 ist dauerhaft im Branch [`legacy/desktop-v0.5.0`](../../tree/legacy/desktop-v0.5.0) gesichert.

## Zielbild

- installierbare Progressive Web App
- offline nutzbar nach dem ersten Laden
- kein Backend für Patientendaten
- keine Cloud-Datenbank
- SQLite als lokale Datenbank über WebAssembly
- lokale PDF-Erzeugung für Rechnungen und Mahnungen
- lokale verschlüsselte Backups
- Migration der vorhandenen JSON-Daten
- unterstützte Desktopbrowser zunächst Chrome und Edge

## Sicherheitsprinzip

Der Hostingserver darf nur statische Dateien erhalten und ausliefern. Patientendaten dürfen weder in Requests noch in Logs, Telemetrie, Fehlerberichten oder externen Diensten erscheinen.

## Dokumentation

- [Produktanforderungen](docs/PRODUCT_REQUIREMENTS.md)
- [Architektur](docs/ARCHITECTURE.md)
- [Datenmodell](docs/DATA_MODEL.md)
- [Sicherheit und Datenschutz](docs/SECURITY.md)
- [Migration der Desktopdaten](docs/MIGRATION.md)
- [Roadmap](docs/ROADMAP.md)

## Entwicklung

Die neue Webanwendung soll unter `web/` aufgebaut werden. Die bisherige Python-/Qt-Implementierung bleibt vorübergehend auf `main` als fachliche und technische Referenz erhalten. Sobald Importer, PDF-Vergleichstests und die neue Grundstruktur verfügbar sind, kann der Altcode aus `main` entfernt werden; er bleibt im Legacy-Branch erhalten.

## Zweckbestimmung

Die Software dient der lokalen Speicherung, Darstellung und Verwaltung patientenbezogener Dokumentations-, Diagnose-, Leistungs- und Abrechnungsdaten. Sie führt keine diagnostische oder therapeutische Analyse durch und gibt keine Empfehlungen für medizinische Entscheidungen.
