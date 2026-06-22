from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from .pdf_invoice import create_invoice_pdf, create_payment_reminder_pdf
from .storage import Storage, invoice_file_stem
from .utils import next_invoice_number, safe_filename


def unbilled_services(patient: dict) -> list[dict]:
    return [service for service in patient.get("leistungen", []) if not service.get("rechnungsnummer")]


def create_invoice(storage: Storage, patient: dict, invoice_date: str) -> tuple[str, Path]:
    services = unbilled_services(patient)
    if not services:
        raise ValueError("Für diesen Patienten gibt es keine offenen Leistungen.")
    if not patient.get("nachname") or not patient.get("strasse") or not patient.get("ort"):
        raise ValueError("Bitte Name und vollständige Anschrift des Patienten eintragen.")

    config = storage.load_config()
    number = str(config["rechnung"]["naechste_nummer"])
    if storage.invoice_number_exists(number):
        raise FileExistsError(f"Die Rechnungsnummer {number} wurde bereits verwendet.")

    service_ids = {service["id"] for service in services}
    record = {
        "schema_version": 2,
        "id": str(uuid.uuid4()),
        "rechnungsnummer": number,
        "rechnungsdatum": invoice_date,
        "erstellt_am": datetime.now().isoformat(timespec="seconds"),
        "patient": {key: value for key, value in patient.items() if key not in {"leistungen", "_path"}},
        "praxis": deepcopy(config["praxis"]),
        "leistungen": deepcopy(services),
        "gesamt_cent": sum(int(item["gesamt_cent"]) for item in services),
        "zahlungsstatus": "offen",
        "bezahlt_am": None,
        "zahlungserinnerungen": [],
    }
    pdf_path = storage.invoices_dir / f"{invoice_file_stem(record)}.pdf"
    create_invoice_pdf(record, pdf_path)
    try:
        storage.save_invoice_record(number, record)
        for service in patient["leistungen"]:
            if service["id"] in service_ids:
                service["rechnungsnummer"] = number
                service["rechnungsdatum"] = invoice_date
        storage.save_patient(patient)
        config["rechnung"]["naechste_nummer"] = next_invoice_number(number)
        storage.save_config(config)
    except Exception:
        pdf_path.unlink(missing_ok=True)
        raise
    return number, pdf_path


def invoice_payment_status(record: dict) -> str:
    return "bezahlt" if record.get("zahlungsstatus") == "bezahlt" or record.get("bezahlt_am") else "offen"


def set_invoice_payment(storage: Storage, record: dict, paid_date: str | None) -> None:
    record["zahlungsstatus"] = "bezahlt" if paid_date else "offen"
    record["bezahlt_am"] = paid_date
    storage.update_invoice_record(record)


def invoice_year(record: dict) -> str:
    date_value = str(record.get("rechnungsdatum", ""))
    return date_value[-4:] if len(date_value) >= 4 and date_value[-4:].isdigit() else "Unbekannt"


def annual_totals(records: list[dict], year: str) -> dict[str, int]:
    selected = [record for record in records if invoice_year(record) == year]
    paid = [record for record in selected if invoice_payment_status(record) == "bezahlt"]
    return {
        "anzahl": len(selected),
        "gesamt_cent": sum(int(record.get("gesamt_cent", 0)) for record in selected),
        "bezahlt_cent": sum(int(record.get("gesamt_cent", 0)) for record in paid),
        "offen_cent": sum(
            int(record.get("gesamt_cent", 0))
            for record in selected
            if invoice_payment_status(record) == "offen"
        ),
    }


def create_payment_reminder(storage: Storage, record: dict, reminder_date: str) -> Path:
    if invoice_payment_status(record) == "bezahlt":
        raise ValueError("Für eine bereits bezahlte Rechnung kann keine Zahlungserinnerung erstellt werden.")
    patient = record.get("patient", {})
    filename = (
        f"Zahlungserinnerung_{record.get('rechnungsnummer', '')}_"
        f"{patient.get('nachname', '')}_{patient.get('vorname', '')}_{reminder_date}"
    )
    output = storage.invoices_dir / f"{safe_filename(filename)}.pdf"
    create_payment_reminder_pdf(record, output, reminder_date)
    record.setdefault("zahlungserinnerungen", []).append({
        "datum": reminder_date,
        "datei": output.name,
        "erstellt_am": datetime.now().isoformat(timespec="seconds"),
    })
    storage.update_invoice_record(record)
    return output
