# Datenmodell

Dieses Dokument beschreibt das fachliche Zielschema. Konkrete SQL-DDL wird zusammen mit der SQLite-Integration versioniert.

## Grundregeln

- Primärschlüssel sind UUIDs, außer fortlaufenden fachlichen Nummern.
- Geld wird als Integer-Cent gespeichert.
- Zeitpunkte werden als ISO-8601 mit Zeitzone gespeichert.
- Fachliche Löschungen werden bevorzugt als Statusänderung oder Storno modelliert.
- Finalisierte Rechnungen speichern Snapshots und referenzieren nicht nur veränderliche Stammdaten.

## Tabellen

### `patients`

- `id`
- Anrede, Vorname, Nachname
- Geburtsdatum
- Anschrift
- Telefon, E-Mail
- Patiententyp
- `created_at`, `updated_at`
- optional `archived_at`

### `diagnoses`

- `id`
- `patient_id`
- Bezeichnung
- optional ICD-Code
- Diagnosedatum
- Status: aktiv, inaktiv, ausgeschlossen
- Freitext
- `created_at`, `updated_at`

Diagnosen sind nicht nur ein einzelnes überschreibbares Feld. Änderungen werden zusätzlich im Audit-Log protokolliert.

### `clinical_notes`

- `id`
- `patient_id`
- Datum und Zeitpunkt
- Titel oder Typ
- Inhalt
- `created_at`, `updated_at`

### `catalog_items`

- `id`
- Nummer
- Bezeichnung
- Faktor
- Standardbetrag in Cent
- Typ oder Katalog
- aktiv/inaktiv
- `valid_from`, optional `valid_to`

### `services`

- `id`
- `patient_id`
- optional `catalog_item_id`
- Leistungsdatum
- Snapshot von Nummer, Bezeichnung, Faktor und Einzelbetrag
- Anzahl
- Gesamtbetrag in Cent
- Zusatznotiz
- optional `invoice_id`
- `created_at`, `updated_at`

### `invoices`

- `id`
- eindeutige Rechnungsnummer
- Rechnungsdatum
- Fälligkeitsdatum
- Status
- Gesamtbetrag in Cent
- finalisiert am
- Praxis-Snapshot als strukturierte Spalten oder JSON
- Patienten-Snapshot als strukturierte Spalten oder JSON
- PDF-Dateipfad und Prüfsumme
- `created_at`, `updated_at`

### `invoice_items`

- `id`
- `invoice_id`
- optional `service_id`
- Leistungsdatum
- Nummer, Bezeichnung, Faktor
- Anzahl
- Einzel- und Gesamtbetrag in Cent
- Sortierreihenfolge

Diese Werte sind nach Finalisierung unveränderlich.

### `payments`

- `id`
- `invoice_id`
- Zahlungsdatum
- Betrag in Cent
- Zahlungsart
- Referenz oder Notiz
- `created_at`

Der offene Betrag ergibt sich aus Rechnungsbetrag minus wirksamen Zahlungen und Gutschriften.

### `reminders`

- `id`
- `invoice_id`
- Mahnstufe
- Datum
- Gebühr in Cent
- PDF-Dateipfad und Prüfsumme
- `created_at`

### `invoice_events`

- `id`
- `invoice_id`
- Ereignistyp
- Zeitpunkt
- strukturierte Nutzdaten

Beispiele: finalisiert, PDF erzeugt, versendet markiert, Zahlung erfasst, Mahnung erstellt, storniert.

### `audit_log`

- `id`
- Entitätstyp und Entitäts-ID
- Aktion
- Zeitpunkt
- lokale Benutzerkennung, sofern vorhanden
- Vorher-/Nachher-Hash oder strukturierte Änderung

Das Audit-Log ist append-only. Sensible Inhalte sollen nur gespeichert werden, wenn sie für die Nachvollziehbarkeit erforderlich sind.

### `settings`

- Schlüssel
- versionierter Wert

### `schema_migrations`

- Versionsnummer
- angewendet am
- Anwendungsversion

## Wichtige Constraints

- Rechnungsnummer ist eindeutig.
- Zahlung darf nicht null oder negativ sein; Korrekturen erfolgen über Gegenbuchungen.
- Eine finalisierte Rechnung darf keine Positionsänderungen erhalten.
- Eine Leistung darf höchstens einer wirksamen Rechnung zugeordnet sein.
- Summe der Rechnungspositionen muss dem Rechnungsbetrag entsprechen.
- Fremdschlüssel werden aktiviert und geprüft.

## Abgeleitete Statuswerte

`teilbezahlt`, `bezahlt` und `überfällig` können aus Rechnungsbetrag, Zahlungen, Fälligkeit und Stornozustand abgeleitet werden. Persistierte Statuswerte dürfen diesen Berechnungen nicht widersprechen.
