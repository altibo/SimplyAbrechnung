# Produktanforderungen

## Produktziel

SimplyAbrechnung ist eine lokale Praxis- und Abrechnungsanwendung für kleine Privatpraxen. Sie verwaltet Patienten, Diagnosen, Dokumentation, Leistungen, Rechnungen, Zahlungen und Mahnungen, ohne fachliche Daten an einen Server zu übertragen.

## Zweckbestimmung

Die Software dient der lokalen Speicherung, Darstellung und Verwaltung patientenbezogener Dokumentations-, Diagnose-, Leistungs- und Abrechnungsdaten. Sie führt keine diagnostische oder therapeutische Analyse durch und gibt keine Empfehlungen für medizinische Entscheidungen.

## Zielplattform

- Desktop unter Windows und macOS
- aktuelle Versionen von Chrome und Edge
- installierbare PWA
- Betrieb nach Erstinstallation auch offline

Mobile Browser und Mehrgeräte-Synchronisation gehören nicht zum ersten Produktumfang.

## Muss-Funktionen

### Praxis

- Praxis-, Arzt-, Kontakt- und Bankdaten verwalten
- Logo und Rechnungsdarstellung konfigurieren
- Zahlungsziel und Rechnungsnummernkreis verwalten

### Patienten

- Stammdaten erfassen und bearbeiten
- Privat-/Kassenkennzeichnung
- mehrere Diagnosen mit Datum, Status und Freitext
- freie und datierte Dokumentationseinträge
- nachvollziehbare Änderungshistorie für medizinisch relevante Angaben

### Leistungskatalog

- GOÄ- und benutzerdefinierte Positionen verwalten
- Positionen aktivieren und deaktivieren
- Änderungen am Katalog dürfen historische Leistungen nicht verändern

### Leistungen

- Leistung mit Datum, Position, Faktor, Anzahl, Betrag und Zusatznotiz erfassen
- offene und abgerechnete Leistungen unterscheiden
- abgerechnete Leistungen nicht unbemerkt verändern

### Rechnungen

- Rechnung aus ausgewählten offenen Leistungen erstellen
- eindeutige fortlaufende Rechnungsnummer
- unveränderlicher Snapshot von Patient, Praxis und Positionen
- lokale PDF-Erzeugung
- Rechnungsstatus und Fälligkeit verwalten
- Storno statt unprotokollierter Löschung finalisierter Rechnungen

### Zahlungen und Mahnungen

- mehrere Teilzahlungen pro Rechnung
- offener Betrag automatisch berechnen
- Status: Entwurf, finalisiert, versendet, teilbezahlt, bezahlt, überfällig, gemahnt, storniert, abgeschrieben
- Zahlungserinnerungen und Mahnungen lokal als PDF erzeugen
- Ereignishistorie je Rechnung

### Auswertungen

- erbrachte Leistungen nach Leistungsdatum
- fakturierte Beträge nach Rechnungsdatum
- Zahlungseingänge nach Zahlungsdatum
- offene und überfällige Forderungen
- Auswertung nach Jahr und frei wählbarem Zeitraum

### Daten und Sicherung

- lokalen Praxisordner auswählen
- Ordner beim Folgestart wiederverwenden, soweit der Browser dies erlaubt
- lokale SQLite-Datenbank
- verschlüsselte Backups mit Integritätsprüfung
- Restore mit Vorschau und Validierung
- Import der bisherigen JSON-Struktur

## Qualitätsanforderungen

- keine fachlichen Daten im Netzwerkverkehr
- alle Geldwerte als Integer-Cent
- atomare Geschäftsoperationen
- versioniertes Datenbankschema
- Wiederherstellbarkeit nach fehlgeschlagenem Update
- keine stillen Datenverluste
- barrierearme Bedienung per Tastatur
- druckstabile Rechnungen auf A4
- nachvollziehbare Fehleranzeigen ohne Patientendaten in externen Logs

## Nicht im ersten Umfang

- Cloud-Synchronisation
- gemeinsamer Mehrbenutzerbetrieb auf mehreren Rechnern
- automatische Diagnose-, Therapie- oder Dosierungsvorschläge
- KI-Auswertung medizinischer Inhalte
- serverseitige PDF-Erzeugung
- E-Mail-Versand über einen Betreiber-Server
- Anbindung an Praxis-, Kassen- oder Telematikinfrastruktur
