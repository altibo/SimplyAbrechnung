from __future__ import annotations

import json
import os
import shutil
import sys
import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from .defaults import DEFAULT_CATALOG, DEFAULT_CONFIG
from .utils import safe_filename


def invoice_file_stem(record: dict) -> str:
    patient = record.get("patient", {})
    return safe_filename(
        f"Rechnung_{record.get('rechnungsnummer', '')}_"
        f"{patient.get('nachname', '')}_{patient.get('vorname', '')}_"
        f"{record.get('rechnungsdatum', '')}"
    )


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base / relative


def default_data_dir() -> Path:
    override = os.environ.get("SIMPLYABRECHNUNG_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / "SimplyAbrechnung_Daten"


class Storage:
    def __init__(self, root: Path | None = None):
        self.root = root or default_data_dir()
        self.patients_dir = self.root / "patienten"
        self.invoices_dir = self.root / "rechnungen"
        self.backups_dir = self.root / "sicherungen"
        self.config_path = self.root / "praxis_config.json"
        self.catalog_path = self.root / "goae_positionen.json"

    def initialize(self) -> None:
        for folder in (self.root, self.patients_dir, self.invoices_dir, self.backups_dir):
            folder.mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            self.write_json(self.config_path, deepcopy(DEFAULT_CONFIG), backup=False)
        if not self.catalog_path.exists():
            self.write_json(self.catalog_path, deepcopy(DEFAULT_CATALOG), backup=False)

    @staticmethod
    def read_json(path: Path) -> Any:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def backup(self, path: Path) -> None:
        if not path.exists():
            return
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        target = self.backups_dir / f"{path.stem}-{stamp}{path.suffix}"
        shutil.copy2(path, target)

    def write_json(self, path: Path, data: Any, backup: bool = True) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if backup:
            self.backup(path)
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        temporary.replace(path)

    def load_config(self) -> dict:
        return self.read_json(self.config_path)

    def save_config(self, config: dict) -> None:
        self.write_json(self.config_path, config)

    def load_catalog(self) -> list[dict]:
        return self.read_json(self.catalog_path)

    def save_catalog(self, catalog: list[dict]) -> None:
        self.write_json(self.catalog_path, catalog)

    def patient_path(self, patient: dict) -> Path:
        name = safe_filename(f"{patient.get('nachname', '')}_{patient.get('vorname', '')}")
        return self.patients_dir / f"{name}_{patient['id'][:8]}.json"

    def list_patients(self) -> list[dict]:
        patients = []
        for path in self.patients_dir.glob("*.json"):
            try:
                patient = self.read_json(path)
                patient["_path"] = str(path)
                patients.append(patient)
            except (OSError, ValueError):
                continue
        return sorted(patients, key=lambda p: (p.get("nachname", "").casefold(), p.get("vorname", "").casefold()))

    def new_patient(self) -> dict:
        return {
            "schema_version": 1,
            "id": str(uuid.uuid4()),
            "anrede": "",
            "vorname": "",
            "nachname": "",
            "geburtsdatum": "",
            "strasse": "",
            "plz": "",
            "ort": "",
            "telefon": "",
            "email": "",
            "patiententyp": "Privatpatient",
            "diagnose": "",
            "notizen": "",
            "leistungen": [],
            "erstellt_am": datetime.now().isoformat(timespec="seconds"),
            "geaendert_am": datetime.now().isoformat(timespec="seconds"),
        }

    def save_patient(self, patient: dict) -> Path:
        old_path_text = patient.pop("_path", None)
        patient["geaendert_am"] = datetime.now().isoformat(timespec="seconds")
        new_path = self.patient_path(patient)
        if old_path_text:
            old_path = Path(old_path_text)
            if old_path.exists() and old_path != new_path:
                self.backup(old_path)
                old_path.unlink()
        self.write_json(new_path, patient)
        patient["_path"] = str(new_path)
        return new_path

    def invoice_number_exists(self, number: str) -> bool:
        safe_number = safe_filename(number)
        if any(self.invoices_dir.glob(f"Rechnung_{safe_number}*.pdf")):
            return True
        for record in self.list_invoice_records():
            if str(record.get("rechnungsnummer", "")) == str(number):
                return True
        return False

    def list_invoice_records(self) -> list[dict]:
        records = []
        for path in self.invoices_dir.glob("Rechnung_*.json"):
            try:
                record = self.read_json(path)
                record["_path"] = str(path)
                records.append(record)
            except (OSError, ValueError):
                continue
        return sorted(records, key=lambda item: item.get("erstellt_am", ""), reverse=True)

    def save_invoice_record(self, number: str, record: dict) -> Path:
        if any(str(item.get("rechnungsnummer", "")) == str(number) for item in self.list_invoice_records()):
            raise FileExistsError(f"Die Rechnung {number} existiert bereits.")
        path = self.invoices_dir / f"{invoice_file_stem(record)}.json"
        self.write_json(path, record, backup=False)
        record["_path"] = str(path)
        return path

    def update_invoice_record(self, record: dict) -> Path:
        path_text = record.pop("_path", None)
        if not path_text:
            raise ValueError("Der Rechnungsdatensatz hat keinen Speicherpfad.")
        path = Path(path_text)
        self.write_json(path, record)
        record["_path"] = str(path)
        return path

    def find_invoice_pdf(self, record: dict) -> Path | None:
        preferred = self.invoices_dir / f"{invoice_file_stem(record)}.pdf"
        if preferred.exists():
            return preferred
        number = safe_filename(str(record.get("rechnungsnummer", "")))
        return next(self.invoices_dir.glob(f"Rechnung_{number}*.pdf"), None)
