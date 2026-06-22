from __future__ import annotations

import json

from simply_abrechnung.billing import create_invoice, unbilled_services
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


def test_invoice_marks_only_open_services(tmp_path, monkeypatch):
    storage = Storage(tmp_path)
    storage.initialize()
    patient = storage.new_patient()
    patient.update({
        "vorname": "Erika", "nachname": "Musterfrau", "strasse": "Testweg 1", "plz": "12345", "ort": "Testort",
        "leistungen": [
            {"id": "old", "datum": "01.01.2026", "nummer": "1", "text": "Alt", "faktor": "2,3", "anzahl": 1, "gesamt_cent": 1000, "rechnungsnummer": "260100"},
            {"id": "new", "datum": "02.01.2026", "nummer": "3", "text": "Neu", "faktor": "2,3", "anzahl": 1, "gesamt_cent": 2010, "rechnungsnummer": None},
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
    record = storage.read_json(storage.invoices_dir / "Rechnung_260111.json")
    assert record["gesamt_cent"] == 2010
    assert [item["id"] for item in record["leistungen"]] == ["new"]


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
