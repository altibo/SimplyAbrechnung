# Roadmap

## Phase 0: Architekturentscheidungen

- ADR für UI-Framework
- ADR für SQLite-WASM und Persistenzschicht
- ADR für Datenbank- und Dateiverschlüsselung
- ADR für PDF-Bibliothek
- Browser-Supportmatrix festlegen
- Netzwerk- und Content-Security-Policy festlegen

Ergebnis: reproduzierbares technisches Grundgerüst ohne fachliche Daten.

## Phase 1: PWA-Grundgerüst

- `web/` mit TypeScript, Vite und Tests anlegen
- Manifest und Icons
- Service Worker mit kontrolliertem Updateprozess
- Offline-Start testen
- GitHub-Pages-Workflow für Prototypen
- Netzwerktest: keine fachlichen Payloads

Akzeptanz: Anwendung ist installierbar, startet offline und lädt nur statische Dateien derselben Origin.

## Phase 2: Lokaler Arbeitsbereich und SQLite

- Praxisordner auswählen
- Directory Handle in IndexedDB speichern
- Berechtigungen beim Start prüfen
- SQLite-WASM in Web Worker
- Schema und Migrationen
- Transaktions- und Integritätstests
- Mehrfach-Tab-Sperre

Akzeptanz: lokaler Testpatient bleibt nach Neustart erhalten; kein Backend ist beteiligt.

## Phase 3: Patienten und Dokumentation

- Patientenliste und Suche
- Stammdaten
- Diagnosen als eigene Datensätze
- datierte Dokumentationseinträge
- Audit-Log
- Archivierung statt unbemerkter Löschung

## Phase 4: Katalog und Leistungen

- bestehenden GOÄ-Katalog importieren
- Katalog bearbeiten und versionieren
- Leistungen erfassen
- historische Snapshots
- offene und abgerechnete Positionen

## Phase 5: Rechnungen und lokale PDFs

- Rechnungsvorschau
- Finalisierung in SQLite-Transaktion
- fortlaufende eindeutige Nummern
- lokale PDF-Erzeugung
- PDF-Prüfsumme und Wiederholbarkeit
- Stornoverfahren

## Phase 6: Zahlungen, Mahnungen und Auswertungen

- mehrere Teilzahlungen
- offener Betrag und Fälligkeit
- Mahnstufen und lokale PDFs
- Ereignishistorie
- Jahres- und Zeitraumsauswertungen

## Phase 7: Migration

- Importer für Desktop-JSON
- synthetische Fixtures
- vollständiger Importbericht
- Wiederholbarkeit und Rollback
- Vergleich ausgewählter Rechnungs-PDFs mit der Desktopversion

## Phase 8: Sicherheit und Sicherung

- lokaler Tresor und Schlüsselableitung
- verschlüsselte Backups
- Restore in temporären Bereich
- CSP und weitere Sicherheitsheader
- XSS-, Import- und Netzwerkprüfungen
- Update- und Rollbacktests

## Phase 9: Produktivsetzung

- eigene Domain
- statisches Hosting mit kontrollierten Sicherheitsheadern
- signierter und dokumentierter Releaseprozess
- Datenschutz- und Zweckbestimmungsdokumentation
- externe rechtliche Prüfung vor Vermarktung
- Bedienungs- und Backuphandbuch

## Unmittelbar nächster Codex-Auftrag

Codex soll Phase 0 und Phase 1 bearbeiten:

1. vorhandenes Repository und `AGENTS.md` lesen,
2. zwei bis drei geeignete Stackvarianten bewerten,
3. ADRs anlegen,
4. ein minimales `web/`-Projekt erstellen,
5. PWA-Installierbarkeit und Offlinebetrieb testen,
6. einen automatisierten Test ergänzen, der Netzwerkrequests protokolliert und fachliche Daten im Requestinhalt ausschließt.
