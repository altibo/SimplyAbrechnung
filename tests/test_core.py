from __future__ import annotations

import json

from simply_abrechnung.billing import (
    annual_totals,
    create_invoice,
    create_payment_reminder,
    invoice_payment_status,
    set_invoice_payment,
    unbilled_services,
)
from simply_abrechnung.defaults import DEFAULT_CONFIG
from simply_abrechnung.pdf_invoice import create_invoice_pdf
from simply_abrechnung.storage import Storage
from simply_abrechnung.utils import euro, next_invoice_number, parse_euro


def test_money_and_invoice_number():
    assert parse_euro("1.234,56 €") == 123456
    assert euro(123456) == "1.234,56 €"
    assert next_invoice_number("0099") == "0100"


def test_patient_is_human_readable_json(tmp_path):
    storage = Storage(tmp_path)
    storage.initialize()
    patient = storage.new_patient()
    patient.update({"vorname": "Erika", "nachname": "Musterfrau", "geburtsdatum": "01.02.1980"})
    path = storage.save_patient(patient)
    content = path.read_text(encoding="utf-8")
    assert "Erika" in content
    assert "\n  \"vorname\"" in content
    assert json.loads(content)["nachname"] == "Musterfrau"
    assert json.loads(content)["patiententyp"] == "Privatpatient"


def test_invoice_marks_only_open_services(tmp_path, monkeypatch):
    storage = Storage(tmp_path)
    storage.initialize()
    patient = storage.new_patient()
    patient.update({
        "vorname": "Erika", "nachname": "Musterfrau", "strasse": "Testweg 1", "plz": "12345", "ort": "Testort",
        "leistungen": [
            {"id": "old", "datum": "01.01.2026", "nummer": "1", "text": "Alt", "faktor": "2,3", "anzahl": 1, "gesamt_cent": 1000, "rechnungsnummer": "260100"},
            {"id": "new", "datum": "02.01.2026", "nummer": "3", "text": "Neu", "notiz": "Hausbesuch", "faktor": "2,3", "anzahl": 1, "gesamt_cent": 2010, "rechnungsnummer": None},
        ],
    })
    storage.save_patient(patient)

    def fake_pdf(record, output):
        output.write_bytes(b"%PDF-test")

    monkeypatch.setattr("simply_abrechnung.billing.create_invoice_pdf", fake_pdf)
    number, pdf = create_invoice(storage, patient, "03.01.2026")
    assert number == "260111"
    assert pdf.exists()
    assert patient["leistungen"][0]["rechnungsnummer"] == "260100"
    assert patient["leistungen"][1]["rechnungsnummer"] == "260111"
    assert not unbilled_services(patient)
    assert storage.load_config()["rechnung"]["naechste_nummer"] == "260112"
    records = storage.list_invoice_records()
    assert len(records) == 1
    record = records[0]
    assert record["gesamt_cent"] == 2010
    assert [item["id"] for item in record["leistungen"]] == ["new"]
    assert record["leistungen"][0]["notiz"] == "Hausbesuch"
    assert record["zahlungsstatus"] == "offen"
    assert pdf.name == "Rechnung_260111_Musterfrau_Erika_03_01_2026.pdf"

    set_invoice_payment(storage, record, "10.01.2026")
    assert invoice_payment_status(record) == "bezahlt"
    assert annual_totals(storage.list_invoice_records(), "2026") == {
        "anzahl": 1, "gesamt_cent": 2010, "bezahlt_cent": 2010, "offen_cent": 0,
    }


def test_old_invoice_names_remain_readable(tmp_path):
    storage = Storage(tmp_path)
    storage.initialize()
    old_record = {
        "id": "old-invoice", "rechnungsnummer": "100", "rechnungsdatum": "01.02.2025",
        "erstellt_am": "2025-02-01T12:00:00", "gesamt_cent": 5000,
        "patient": {"vorname": "Max", "nachname": "Alt"},
    }
    old_json = storage.invoices_dir / "Rechnung_100.json"
    storage.write_json(old_json, old_record, backup=False)
    old_pdf = storage.invoices_dir / "Rechnung_100.pdf"
    old_pdf.write_bytes(b"%PDF-old")
    loaded = storage.list_invoice_records()[0]
    assert invoice_payment_status(loaded) == "offen"
    assert storage.find_invoice_pdf(loaded) == old_pdf


def test_payment_reminder_pdf_and_history(tmp_path):
    storage = Storage(tmp_path)
    storage.initialize()
    record = {
        "schema_version": 2, "id": "invoice-1", "rechnungsnummer": "101",
        "rechnungsdatum": "01.03.2026", "erstellt_am": "2026-03-01T12:00:00",
        "gesamt_cent": 1072, "zahlungsstatus": "offen", "bezahlt_am": None,
        "zahlungserinnerungen": [], "praxis": DEFAULT_CONFIG["praxis"],
        "patient": {"anrede": "Frau", "vorname": "Änne", "nachname": "Müller", "strasse": "Ölweg 1", "plz": "12345", "ort": "Würzburg"},
        "leistungen": [],
    }
    storage.save_invoice_record("101", record)
    output = create_payment_reminder(storage, record, "15.03.2026")
    assert output.read_bytes().startswith(b"%PDF")
    assert "Müller_Änne_15_03_2026" in output.name
    loaded = storage.list_invoice_records()[0]
    assert loaded["zahlungserinnerungen"][0]["datum"] == "15.03.2026"


def test_pdf_is_created_with_unicode_text(tmp_path):
    output = tmp_path / "rechnung.pdf"
    record = {
        "rechnungsnummer": "1", "rechnungsdatum": "22.06.2026", "gesamt_cent": 1072,
        "praxis": DEFAULT_CONFIG["praxis"],
        "patient": {"anrede": "Frau", "vorname": "Änne", "nachname": "Müller", "geburtsdatum": "", "strasse": "Ölweg 1", "plz": "12345", "ort": "Würzburg", "diagnose": "Prüfung"},
        "leistungen": [{"datum": "22.06.2026", "nummer": "1", "text": "Beratung, auch telefonisch", "faktor": "2,3", "anzahl": 1, "gesamt_cent": 1072}],
    }
    create_invoice_pdf(record, output)
    assert output.read_bytes().startswith(b"%PDF")
    assert output.stat().st_size > 10_000
