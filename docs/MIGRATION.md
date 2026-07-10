# Migration der Desktopdaten

## Quelle

Die Desktopversion 0.5.0 speichert Daten unter `SimplyAbrechnung_Daten`:

```text
praxis_config.json
goae_positionen.json
praxis_logo.png
patienten/*.json
rechnungen/*.json
sicherungen/*
```

Der unveränderte Quellstand befindet sich im Branch `legacy/desktop-v0.5.0`.

## Grundsätze

- Quelldateien werden niemals verändert oder gelöscht.
- Vor dem Import wird der gesamte Quellordner optional als zusätzliches Archiv gesichert.
- Alle JSON-Dateien werden vollständig gelesen und validiert, bevor Daten geschrieben werden.
- Der Import läuft in genau einer SQLite-Transaktion.
- Bei einem Fehler wird die gesamte Transaktion zurückgerollt.
- Jeder Import erzeugt einen lokalen Bericht mit Warnungen und Zuordnungen.
- Wiederholte Imports müssen erkannt werden und dürfen keine Duplikate erzeugen.

## Zuordnung

### `praxis_config.json`

- Praxis- und Bankdaten nach `settings` beziehungsweise strukturierte Praxistabellen
- nächste Rechnungsnummer in den Nummernkreis
- Logo wird als lokale Datei übernommen

### `goae_positionen.json`

- Einträge nach `catalog_items`
- bestehende IDs werden nach Möglichkeit erhalten
- unklare oder mit Fragezeichen markierte Beträge werden als Warnung importiert und nicht automatisch fachlich korrigiert

### `patienten/*.json`

- Stammdaten nach `patients`
- bisheriges Diagnosefeld als erste Diagnose oder als gekennzeichneter Legacy-Diagnosetext
- freie Notizen nach `clinical_notes`
- Leistungen nach `services`
- vorhandene UUIDs werden erhalten

### `rechnungen/*.json`

- Rechnungs-Snapshot nach `invoices`
- Positionen nach `invoice_items`
- bisheriger Status und Zahlungsdatum werden übernommen
- vorhandene Zahlungserinnerungen nach `reminders` und `invoice_events`
- vorhandene PDF-Datei wird übernommen und mit Prüfsumme registriert

## Datenbereinigung

Der Import darf nur technische Normalisierungen automatisch durchführen:

- Datumsformat eindeutig parsen
- Geldwerte als Integer-Cent übernehmen
- leere optionale Felder in `NULL` überführen
- Zeichenkodierung auf UTF-8 normalisieren

Fachliche Änderungen, insbesondere an GOÄ-Beträgen, Diagnosen, Faktoren oder Rechnungsinhalten, erfolgen nicht automatisch.

## Validierungen

- jede Patienten- und Rechnungs-ID eindeutig
- jede Rechnungsnummer eindeutig
- Rechnungssumme entspricht Summe ihrer Positionen
- abgerechnete Leistungen lassen sich einer Rechnung zuordnen
- PDF-Dateien und JSON-Datensätze stimmen hinsichtlich Rechnungsnummer überein
- nächste Rechnungsnummer kollidiert nicht mit vorhandenen Rechnungen
- alle Geldwerte liegen im zulässigen Integerbereich

Nicht auflösbare Abweichungen werden im Importbericht ausgewiesen. Der Benutzer entscheidet anschließend über eine manuelle Korrektur.

## Tests

Im Repository werden ausschließlich synthetische, anonymisierte Fixtures abgelegt:

- leerer Datenbestand
- ein Patient ohne Rechnung
- mehrere offene Leistungen
- bezahlte und offene Rechnungen
- Zahlungserinnerung
- umbenannter Patient mit altem Dateinamen
- beschädigte JSON-Datei
- doppelte Rechnungsnummer
- inkonsistente Rechnungssumme
- Unicode und sehr lange Freitexte

Für jedes Fixture wird geprüft, dass Importergebnis und Importbericht deterministisch sind.
