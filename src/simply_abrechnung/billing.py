from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from .pdf_invoice import create_invoice_pdf
from .storage import Storage
from .utils import next_invoice_number


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
    if (storage.invoices_dir / f"Rechnung_{number}.json").exists() or (storage.invoices_dir / f"Rechnung_{number}.pdf").exists():
        raise FileExistsError(f"Die Rechnungsnummer {number} wurde bereits verwendet.")

    service_ids = {service["id"] for service in services}
    record = {
        "schema_version": 1,
        "id": str(uuid.uuid4()),
        "rechnungsnummer": number,
        "rechnungsdatum": invoice_date,
        "erstellt_am": datetime.now().isoformat(timespec="seconds"),
        "patient": {key: value for key, value in patient.items() if key not in {"leistungen", "_path"}},
        "praxis": deepcopy(config["praxis"]),
        "leistungen": deepcopy(services),
        "gesamt_cent": sum(int(item["gesamt_cent"]) for item in services),
    }
    pdf_path = storage.invoices_dir / f"Rechnung_{number}.pdf"
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
