# SimplyAbrechnung

SimplyAbrechnung ist eine bewusst einfache, lokale Patientenkartei mit PDF-Rechnungen für eine kleine Privatpraxis. Die Anwendung benötigt keinen Server und keine Cloud.

Aktuelle Programmversion: **0.4.0**

## Funktionen

- eine menschenlesbare JSON-Datei je Patient
- persönliche Daten, Diagnose, freie Notizen und datierte Behandlungen
- Kennzeichnung als Privat- oder Kassenpatient
- offene Leistungen per Doppelklick oder Schaltfläche bearbeiten, inklusive sichtbarer Zusatznotiz
- scrollbare Langtextfelder für freie Notizen und Zusatznotizen zu Leistungen
- zentraler, in der Anwendung bearbeitbarer GOÄ-Leistungskatalog
- nur noch offene Positionen werden in die nächste Rechnung übernommen
- automatische fortlaufende Rechnungsnummer
- Rechnungsübersicht mit Zahlungsstatus, Zahlungsdatum und offenen Beträgen
- Jahresübersicht mit Gesamt-, Bezahlt- und Offen-Summen
- PDF-Zahlungserinnerungen für offene Rechnungen
- aussagekräftige Rechnungsdateinamen mit Patient und Datum
- PDF-Rechnung im Stil des mitgelieferten Vordrucks und mit dessen Original-Logo
- eigener JSON-Datensatz mit Zahlungshistorie zu jeder erstellten Rechnung
- automatische Sicherungskopien vor Änderungen
- sichtbare Versionsnummer in Fenstertitel und Symbolleiste

## Bedienung

1. Unter **Praxis-Einstellungen** die Praxis-, Bank- und Rechnungsdaten prüfen.
2. Einen Patienten anlegen und speichern.
3. Über **Leistung eintragen** datierte GOÄ-Positionen hinzufügen.
4. **Rechnung aus offenen Positionen erstellen** wählen.
5. Unter **Rechnungsübersicht** Zahlungen erfassen, Jahreszahlen prüfen oder eine Zahlungserinnerung erstellen.

Die Anwendung speichert ihre Daten unter `SimplyAbrechnung_Daten` im Benutzerordner. Darin liegen:

```text
SimplyAbrechnung_Daten/
├── praxis_config.json
├── goae_positionen.json
├── patienten/
├── rechnungen/
└── sicherungen/
```

Die Originalvorlagen bleiben unverändert im Ordner `Vorlage`.

## Datenschutz und Datensicherung

Die Dateien enthalten besonders schützenswerte Gesundheitsdaten und sind absichtlich menschenlesbar, aber nicht zusätzlich durch das Programm verschlüsselt. Der Rechner sollte deshalb ein geschütztes Benutzerkonto, Festplattenverschlüsselung und eine verschlüsselte Datensicherung verwenden. Der gesamte Ordner `SimplyAbrechnung_Daten` muss regelmäßig gesichert werden.

Vor dem produktiven Einsatz müssen Praxis und Abrechnungsfachkraft den GOÄ-Katalog, Pflichtangaben, Steuernummern-Hinweise, Steigerungsfaktoren und Begründungstexte prüfen. Mehrere Beträge der gelieferten Vorlage enthielten ausdrücklich Fragezeichen; diese Hinweise wurden in den Katalog übernommen.

## Entwicklung

Python 3.11 oder neuer wird benötigt.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m simply_abrechnung
pytest
pyinstaller --noconfirm --clean SimplyAbrechnung.spec
```

Unter macOS wird die virtuelle Umgebung mit `source .venv/bin/activate` aktiviert. Nicht signierte macOS-Builds können beim ersten Start eine Gatekeeper-Warnung auslösen.

## Installation und Updates

- Unter Windows `SimplyAbrechnung-Windows-Setup.exe` aus dem Release starten.
- Unter macOS `SimplyAbrechnung-macOS.pkg` öffnen; die App wird nach `/Applications` installiert.
- Eine neue Installer-Version ersetzt die vorhandene Installation automatisch.
- Der Datenordner `SimplyAbrechnung_Daten` im Benutzerordner bleibt bei Installation und Update unverändert.

Wer bisher die portable Windows-Datei aus einem ZIP verwendet hat, installiert die neue Setup-Version einmalig und kann die alte portable Datei danach entfernen.

## Veröffentlichungen

Jeder Push auf `main` testet und baut die Anwendung auf Windows und macOS. GitHub Actions stellt einen Windows-Setup-Assistenten und ein macOS-Installationspaket als Build-Artefakte bereit und erzeugt zusätzlich eine neue Vorabveröffentlichung mit einer eindeutigen Build-Nummer.
