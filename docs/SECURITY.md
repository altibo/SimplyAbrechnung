# Sicherheit und Datenschutz

## Schutzbedarf

Die Anwendung verarbeitet Gesundheitsdaten, Identitätsdaten und Abrechnungsdaten. Vertraulichkeit, Integrität, Verfügbarkeit und Nachvollziehbarkeit sind daher zentrale Produktanforderungen, unabhängig von einer möglichen medizinprodukterechtlichen Einordnung.

## Vertrauensgrenzen

### Hostingserver

Der Server liefert ausschließlich statische, versionierte Programmdateien. Er erhält keine fachlichen Daten. Normale technische Zugriffsdaten des Hosters, insbesondere IP-Adresse und Abrufzeit, lassen sich nicht vollständig vermeiden.

### Browser/PWA

Der geladene Anwendungscode kann auf entschlüsselte Daten zugreifen. Ein kompromittierter Build, Account oder Hostingkanal könnte Daten exfiltrieren. Releaseprozess und Updatekontrolle sind daher sicherheitskritisch.

### Lokaler Rechner

Die Anwendung setzt ein geschütztes Betriebssystemkonto und aktivierte Festplattenverschlüsselung voraus. Diese Anforderungen müssen dokumentiert werden, ersetzen aber nicht die Anwendungssicherheit.

## Verbindliche Maßnahmen

- keine Analytics, Werbung, Session-Replays oder externe Telemetrie
- keine extern geladenen Fonts, Skripte oder CDNs
- restriktive Content Security Policy
- `connect-src` grundsätzlich nur eigene Origin; für den Offlinebetrieb möglichst keine Verbindung erforderlich
- versionierte, reproduzierbare Builds
- Dependency-Lockfile und automatisierte Schwachstellenprüfung
- kontrollierte Aktivierung von PWA-Updates
- automatische Datensicherung vor Schema-Migrationen
- Sperre nach Inaktivität
- keine fachlichen Daten in URLs, Browser-History oder externen Logs
- lokale Fehlerprotokolle nur nach explizitem Export und mit Datenminimierung
- Integritätsprüfungen für Datenbank, PDFs und Backups

## Verschlüsselung

Die Anwendung soll einen lokalen Datentresor unterstützen. Zielkonzept:

- Schlüsselableitung aus einem lokalen Passwort mit Argon2id oder vergleichbarer etablierter KDF
- zufälliger Salt
- authentifizierte Verschlüsselung, beispielsweise AES-GCM
- Schlüssel nur im Arbeitsspeicher während einer entsperrten Sitzung
- keine Speicherung des Klartextpassworts
- dokumentiertes Wiederherstellungskonzept

Die konkrete SQLite-Verschlüsselung ist vor Implementierung als ADR zu entscheiden. Eine nur verschlüsselte Backup-Datei schützt nicht die laufende Datenbank; eine nur verschlüsselte Datenbank schützt nicht automatisch separat gespeicherte PDFs und Anhänge.

## Backups

Backups enthalten mindestens:

- Manifest mit Format-, Schema- und Anwendungsversion
- Datenbank
- Dokumente und Anhänge
- SHA-256-Prüfsummen
- Erstellungszeitpunkt

Backups werden vor dem Schreiben validiert und nach dem Schreiben erneut geprüft. Restore erfolgt zunächst in einen temporären Bereich und wird erst nach vollständiger Prüfung aktiviert.

## Änderungsnachvollziehbarkeit

Medizinisch und kaufmännisch relevante Änderungen werden protokolliert. Finalisierte Rechnungen werden nicht überschrieben. Diagnosen und Dokumentationseinträge dürfen nicht ohne nachvollziehbaren Änderungsvermerk verschwinden.

## Bedrohungen, die getestet werden müssen

- XSS über Freitextfelder
- manipulierte Importdateien
- beschädigte oder teilweise geschriebene Backups
- konkurrierende Schreibzugriffe aus mehreren Tabs
- fehlerhafte oder abgebrochene Schema-Migration
- Exfiltration durch versehentliche Netzwerkrequests
- manipulierte PDF-Inhalte oder Dateinamen
- Verlust der Ordnerberechtigung
- Löschen von Browserdaten oder OPFS
- Rollback auf inkompatible Anwendungsversion

## Incident-Grundsatz

Die Anwendung darf Datenfehler nicht stillschweigend überspringen. Inkonsistenzen müssen den Betrieb in einen sicheren, möglichst schreibgeschützten Zustand versetzen und einen lokalen Diagnoseexport ermöglichen, der vor Weitergabe geprüft werden kann.
