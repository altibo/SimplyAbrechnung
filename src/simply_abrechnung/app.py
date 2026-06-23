from __future__ import annotations

import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QColorDialog,
)

from . import __version__
from .billing import (
    annual_totals,
    create_invoice,
    create_payment_reminder,
    invoice_payment_status,
    invoice_year,
    set_invoice_payment,
    unbilled_services,
)
from .storage import Storage
from .utils import euro, parse_euro, today_german, validate_date


PATIENT_FIELDS = [
    ("anrede", "Anrede"), ("vorname", "Vorname"), ("nachname", "Nachname"),
    ("geburtsdatum", "Geburtsdatum"), ("strasse", "Straße"), ("plz", "PLZ"),
    ("ort", "Ort"), ("telefon", "Telefon"), ("email", "E-Mail"),
    ("patiententyp", "Patiententyp"), ("diagnose", "Diagnose"),
]


def open_path(path: Path) -> None:
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def ask_error(parent: QWidget, title: str, text: str) -> None:
    QMessageBox.critical(parent, title, text)


def selected_row(table: QTableWidget) -> int:
    rows = table.selectionModel().selectedRows()
    return rows[0].row() if rows else -1


class ServiceDialog(QDialog):
    def __init__(self, parent: QWidget, catalog: list[dict], service: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Leistung bearbeiten" if service else "Leistung eintragen")
        self.setModal(True)
        self.resize(820, 430)
        self.result: dict | None = None
        self.service = service or {}
        self.catalog = [item for item in catalog if item.get("aktiv", True)]
        if service and not any(item.get("id") == service.get("katalog_id") for item in self.catalog):
            self.catalog.append({
                "id": service.get("katalog_id", f"bestand-{service['id']}"),
                "nummer": service.get("nummer", ""),
                "text": service.get("text", ""),
                "faktor": service.get("faktor", ""),
                "betrag_cent": int(service.get("einzelbetrag_cent", service.get("gesamt_cent", 0))),
                "aktiv": True,
            })

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.date_edit = QLineEdit(service.get("datum", today_german()) if service else today_german())
        self.service_combo = QComboBox()
        self.labels = [
            f"{item['nummer']} · {item['text']} · Faktor {item['faktor']} · {euro(item['betrag_cent'])}"
            for item in self.catalog
        ]
        self.service_combo.addItems(self.labels)
        if service:
            index = next((i for i, item in enumerate(self.catalog) if item.get("id") == service.get("katalog_id")), 0)
            self.service_combo.setCurrentIndex(index)
        self.quantity = QSpinBox()
        self.quantity.setRange(1, 99)
        self.quantity.setValue(int(service.get("anzahl", 1)) if service else 1)
        self.note = QTextEdit()
        self.note.setMinimumHeight(210)
        self.note.setPlaceholderText("Zusatznotiz zur Leistung")
        self.note.setPlainText(service.get("notiz", "") if service else "")
        form.addRow("Datum", self.date_edit)
        form.addRow("Leistung", self.service_combo)
        form.addRow("Anzahl", self.quantity)
        form.addRow("Zusatznotiz", self.note)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("Abbrechen")
        save = QPushButton("Speichern" if service else "Eintragen")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept_values)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def accept_values(self) -> None:
        try:
            date_value = validate_date(self.date_edit.text())
            index = self.service_combo.currentIndex()
            if index < 0:
                raise ValueError("Bitte eine Leistung auswählen.")
        except ValueError as exc:
            ask_error(self, "Eingabe prüfen", str(exc))
            return
        item = self.catalog[index]
        quantity = self.quantity.value()
        self.result = {
            "id": self.service.get("id", str(uuid.uuid4())),
            "katalog_id": item["id"],
            "datum": date_value,
            "nummer": item["nummer"],
            "text": item["text"],
            "faktor": item["faktor"],
            "anzahl": quantity,
            "einzelbetrag_cent": int(item["betrag_cent"]),
            "gesamt_cent": int(item["betrag_cent"]) * quantity,
            "notiz": self.note.toPlainText().strip(),
            "rechnungsnummer": self.service.get("rechnungsnummer"),
            "rechnungsdatum": self.service.get("rechnungsdatum"),
            "eingetragen_am": self.service.get("eingetragen_am", datetime.now().isoformat(timespec="seconds")),
        }
        self.accept()


class ConfigDialog(QDialog):
    FIELDS = [
        ("arzt", "Name des Arztes"), ("zusatz", "Praxisbezeichnung"), ("strasse", "Straße"),
        ("plz_ort", "PLZ / Ort"), ("telefon", "Telefon"), ("email", "E-Mail"),
        ("bank", "Bank"), ("iban", "IBAN"), ("steuernummer", "Steuernummer / Hinweis"),
        ("zahlungsziel_tage", "Zahlungsziel in Tagen"),
    ]

    def __init__(self, parent: QWidget, storage: Storage):
        super().__init__(parent)
        self.setWindowTitle("Praxis-Einstellungen")
        self.setModal(True)
        self.resize(760, 560)
        self.storage = storage
        self.config = storage.load_config()
        self.logo_source: Path | None = None
        self.remove_logo = False

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.fields: dict[str, QLineEdit] = {}
        for key, label in self.FIELDS:
            edit = QLineEdit(str(self.config["praxis"].get(key, "")))
            self.fields[key] = edit
            form.addRow(label, edit)

        self.invoice = QLineEdit(str(self.config["rechnung"]["naechste_nummer"]))
        form.addRow("Nächste Rechnungsnummer", self.invoice)

        accent_row = QHBoxLayout()
        self.accent = QLineEdit(str(self.config["praxis"].get("akzentfarbe", "#0A4B92")))
        pick_color = QPushButton("Farbe wählen")
        pick_color.clicked.connect(self.choose_color)
        accent_row.addWidget(self.accent)
        accent_row.addWidget(pick_color)
        form.addRow("Akzentfarbe Rechnung", accent_row)

        logo_row = QHBoxLayout()
        self.logo_label = QLabel(self.config["praxis"].get("logo_datei") or "Default-Logo")
        choose_logo = QPushButton("Eigenes Logo wählen")
        clear_logo = QPushButton("Default verwenden")
        choose_logo.clicked.connect(self.choose_logo)
        clear_logo.clicked.connect(self.clear_logo)
        logo_row.addWidget(self.logo_label, 1)
        logo_row.addWidget(choose_logo)
        logo_row.addWidget(clear_logo)
        form.addRow("Praxislogo", logo_row)

        self.reason = QTextEdit()
        self.reason.setMinimumHeight(96)
        self.reason.setPlainText(self.config["praxis"].get("standard_begruendung", ""))
        form.addRow("Standardbegründung > 2,3", self.reason)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("Abbrechen")
        save = QPushButton("Speichern")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.save)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def choose_color(self) -> None:
        initial = QColor(self.accent.text()) if QColor.isValidColor(self.accent.text()) else QColor("#0A4B92")
        color = QColorDialog.getColor(initial, self, "Akzentfarbe wählen")
        if color.isValid():
            self.accent.setText(color.name().upper())

    def choose_logo(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Logo wählen", str(Path.home()), "Bilder (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if filename:
            self.logo_source = Path(filename)
            self.remove_logo = False
            self.logo_label.setText(self.logo_source.name)

    def clear_logo(self) -> None:
        self.logo_source = None
        self.remove_logo = True
        self.logo_label.setText("Default-Logo")

    def save(self) -> None:
        number = self.invoice.text().strip()
        if not number.isdigit():
            ask_error(self, "Eingabe prüfen", "Die Rechnungsnummer muss nur aus Ziffern bestehen.")
            return
        if not QColor.isValidColor(self.accent.text().strip()):
            ask_error(self, "Eingabe prüfen", "Die Akzentfarbe muss ein gültiger Farbwert sein, z. B. #0A4B92.")
            return
        for key, edit in self.fields.items():
            value: str | int = edit.text().strip()
            if key == "zahlungsziel_tage":
                try:
                    value = int(value)
                except ValueError:
                    ask_error(self, "Eingabe prüfen", "Das Zahlungsziel muss eine Zahl sein.")
                    return
            self.config["praxis"][key] = value
        if self.logo_source:
            suffix = self.logo_source.suffix.lower() or ".png"
            target = self.storage.root / f"praxis_logo{suffix}"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.logo_source, target)
            self.config["praxis"]["logo_datei"] = target.name
        elif self.remove_logo:
            old = self.config["praxis"].get("logo_datei")
            if old:
                (self.storage.root / old).unlink(missing_ok=True)
            self.config["praxis"]["logo_datei"] = ""
        self.config["praxis"]["akzentfarbe"] = self.accent.text().strip().upper()
        self.config["praxis"]["standard_begruendung"] = self.reason.toPlainText().strip()
        self.config["rechnung"]["naechste_nummer"] = number
        self.storage.save_config(self.config)
        self.accept()


class CatalogDialog(QDialog):
    def __init__(self, parent: QWidget, storage: Storage):
        super().__init__(parent)
        self.setWindowTitle("GOÄ-Leistungskatalog")
        self.setModal(True)
        self.resize(1040, 600)
        self.storage = storage
        self.catalog = storage.load_catalog()
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["GOÄ-Nr.", "Leistung", "Faktor", "Betrag", "Hinweis aus Vorlage"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit)
        layout.addWidget(self.table)
        buttons = QHBoxLayout()
        add = QPushButton("Neue Position")
        edit = QPushButton("Position bearbeiten")
        close = QPushButton("Schließen")
        add.clicked.connect(self.add)
        edit.clicked.connect(self.edit)
        close.clicked.connect(self.accept)
        buttons.addWidget(add)
        buttons.addWidget(edit)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.refresh()

    def refresh(self) -> None:
        self.table.setRowCount(len(self.catalog))
        for row, item in enumerate(self.catalog):
            for col, value in enumerate([item["nummer"], item["text"], item["faktor"], euro(item["betrag_cent"]), item.get("hinweis", "")]):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))

    def add(self) -> None:
        item = self.edit_item(None)
        if item:
            self.catalog.append(item)
            self.storage.save_catalog(self.catalog)
            self.refresh()

    def edit(self) -> None:
        row = selected_row(self.table)
        if row < 0:
            QMessageBox.information(self, "Position wählen", "Bitte zuerst eine Position auswählen.")
            return
        item = self.edit_item(self.catalog[row])
        if item:
            self.catalog[row] = item
            self.storage.save_catalog(self.catalog)
            self.refresh()
            self.table.selectRow(row)

    def edit_item(self, item: dict | None) -> dict | None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Position bearbeiten" if item else "Neue Position")
        dialog.setModal(True)
        values = item or {"nummer": "", "text": "", "faktor": "2,3", "betrag_cent": 0, "hinweis": "", "aktiv": True}
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        fields: dict[str, QLineEdit] = {}
        for key, label in [("nummer", "GOÄ-Nr."), ("text", "Leistungstext"), ("faktor", "Faktor"), ("betrag", "Betrag in Euro"), ("hinweis", "Hinweis")]:
            initial = euro(values["betrag_cent"]).replace(" €", "") if key == "betrag" else str(values.get(key, ""))
            edit = QLineEdit(initial)
            fields[key] = edit
            form.addRow(label, edit)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("Abbrechen")
        save = QPushButton("Speichern")
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)
        result: list[dict] = []

        def accept_values() -> None:
            try:
                cents = parse_euro(fields["betrag"].text())
                if not fields["nummer"].text().strip() or not fields["text"].text().strip():
                    raise ValueError("Nummer und Leistungstext dürfen nicht leer sein.")
            except ValueError as exc:
                ask_error(dialog, "Eingabe prüfen", str(exc))
                return
            result.append({
                "id": values.get("id", str(uuid.uuid4())),
                "nummer": fields["nummer"].text().strip(),
                "text": fields["text"].text().strip(),
                "faktor": fields["faktor"].text().strip(),
                "betrag_cent": cents,
                "hinweis": fields["hinweis"].text().strip(),
                "aktiv": True,
            })
            dialog.accept()

        cancel.clicked.connect(dialog.reject)
        save.clicked.connect(accept_values)
        dialog.exec()
        return result[0] if result else None


class InvoiceOverviewDialog(QDialog):
    def __init__(self, parent: QWidget, storage: Storage):
        super().__init__(parent)
        self.setWindowTitle("Rechnungs- und Jahresübersicht")
        self.setModal(True)
        self.resize(1100, 640)
        self.storage = storage
        self.records: list[dict] = []
        self.visible: list[dict] = []
        layout = QVBoxLayout(self)

        filters = QHBoxLayout()
        self.year = QComboBox()
        self.status = QComboBox()
        self.status.addItems(["Alle", "offen", "bezahlt"])
        self.summary = QLabel()
        self.year.currentTextChanged.connect(self.refresh)
        self.status.currentTextChanged.connect(self.refresh)
        filters.addWidget(QLabel("Jahr:"))
        filters.addWidget(self.year)
        filters.addWidget(QLabel("Status:"))
        filters.addWidget(self.status)
        filters.addWidget(self.summary, 1)
        layout.addLayout(filters)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Rechnung", "Datum", "Patient", "Betrag", "Status", "Bezahlt am", "Letzte Erinnerung"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.open_invoice)
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        for label, callback in [
            ("Als bezahlt markieren", self.mark_paid),
            ("Als offen markieren", self.mark_open),
            ("Zahlungserinnerung erstellen", self.reminder),
            ("Rechnungs-PDF öffnen", self.open_invoice),
        ]:
            button = QPushButton(label)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        buttons.addStretch(1)
        close = QPushButton("Schließen")
        close.clicked.connect(self.accept)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.reload()

    def reload(self) -> None:
        self.records = self.storage.list_invoice_records()
        years = sorted({invoice_year(record) for record in self.records}, reverse=True)
        self.year.blockSignals(True)
        self.year.clear()
        self.year.addItems(["Alle Jahre", *years])
        self.year.blockSignals(False)
        self.refresh()

    def refresh(self) -> None:
        year = self.year.currentText() or "Alle Jahre"
        year_records = self.records if year == "Alle Jahre" else [record for record in self.records if invoice_year(record) == year]
        status_filter = self.status.currentText() or "Alle"
        self.visible = year_records if status_filter == "Alle" else [
            record for record in year_records if invoice_payment_status(record) == status_filter
        ]
        self.table.setRowCount(len(self.visible))
        for row, record in enumerate(self.visible):
            patient = record.get("patient", {})
            name = f"{patient.get('nachname', '')}, {patient.get('vorname', '')}".strip(", ")
            reminders = record.get("zahlungserinnerungen", [])
            reminder_date = reminders[-1].get("datum", "") if reminders else ""
            values = [
                record.get("rechnungsnummer", ""), record.get("rechnungsdatum", ""), name,
                euro(int(record.get("gesamt_cent", 0))), invoice_payment_status(record),
                record.get("bezahlt_am") or "", reminder_date,
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
        if year == "Alle Jahre":
            total = sum(int(record.get("gesamt_cent", 0)) for record in year_records)
            paid = sum(int(record.get("gesamt_cent", 0)) for record in year_records if invoice_payment_status(record) == "bezahlt")
            self.summary.setText(f"{len(year_records)} Rechnungen · Gesamt {euro(total)} · Bezahlt {euro(paid)} · Offen {euro(total - paid)}")
        else:
            totals = annual_totals(self.records, year)
            self.summary.setText(
                f"Jahresübersicht {year}: {totals['anzahl']} Rechnungen · Gesamt {euro(totals['gesamt_cent'])} · "
                f"Bezahlt {euro(totals['bezahlt_cent'])} · Offen {euro(totals['offen_cent'])}"
            )

    def current_record(self) -> dict | None:
        row = selected_row(self.table)
        if row < 0:
            QMessageBox.information(self, "Rechnung wählen", "Bitte zuerst eine Rechnung auswählen.")
            return None
        return self.visible[row]

    def mark_paid(self) -> None:
        record = self.current_record()
        if not record:
            return
        date, ok = QInputDialog.getText(self, "Zahlungseingang", "Bezahlt am:", text=record.get("bezahlt_am") or today_german())
        if not ok or not date:
            return
        try:
            set_invoice_payment(self.storage, record, validate_date(date))
        except Exception as exc:
            ask_error(self, "Zahlungsstatus nicht gespeichert", str(exc))
            return
        self.reload()

    def mark_open(self) -> None:
        record = self.current_record()
        if not record:
            return
        if QMessageBox.question(self, "Zahlungsstatus", "Diese Rechnung wieder als offen markieren?") != QMessageBox.StandardButton.Yes:
            return
        try:
            set_invoice_payment(self.storage, record, None)
        except Exception as exc:
            ask_error(self, "Zahlungsstatus nicht gespeichert", str(exc))
            return
        self.reload()

    def reminder(self) -> None:
        record = self.current_record()
        if not record:
            return
        date, ok = QInputDialog.getText(self, "Zahlungserinnerung", "Datum der Zahlungserinnerung:", text=today_german())
        if not ok or not date:
            return
        try:
            output = create_payment_reminder(self.storage, record, validate_date(date))
        except Exception as exc:
            ask_error(self, "Zahlungserinnerung nicht erstellt", str(exc))
            return
        self.reload()
        if QMessageBox.question(self, "Zahlungserinnerung erstellt", f"PDF wurde gespeichert:\n{output}\n\nJetzt öffnen?") == QMessageBox.StandardButton.Yes:
            open_path(output)

    def open_invoice(self) -> None:
        record = self.current_record()
        if not record:
            return
        pdf_path = self.storage.find_invoice_pdf(record)
        if not pdf_path:
            ask_error(self, "PDF nicht gefunden", "Die PDF-Datei dieser Rechnung wurde nicht gefunden.")
            return
        open_path(pdf_path)


class SimplyAbrechnungApp(QMainWindow):
    def __init__(self, storage: Storage | None = None):
        super().__init__()
        self.storage = storage or Storage()
        self.storage.initialize()
        self.current: dict | None = None
        self.patients: list[dict] = []
        self.service_rows: list[dict] = []
        self.setWindowTitle(f"SimplyAbrechnung {__version__}")
        self.resize(1240, 780)
        self.setMinimumSize(980, 660)
        self.build_ui()
        self.refresh_patient_list()

    def build_ui(self) -> None:
        toolbar = QToolBar("Hauptaktionen")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        for label, callback in [
            ("Neuer Patient", self.new_patient),
            ("Patient speichern", self.save_patient),
            ("Praxis-Einstellungen", self.open_config),
            ("GOÄ-Katalog", self.open_catalog),
            ("Rechnungsübersicht", self.open_invoices),
            ("Datenordner öffnen", lambda: open_path(self.storage.root)),
        ]:
            action = toolbar.addAction(label)
            action.triggered.connect(lambda _checked=False, cb=callback: cb())
        self.version_label = QLabel(f"  Version {__version__}")
        toolbar.addWidget(self.version_label)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        outer.addWidget(splitter, 1)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        title = QLabel("Patienten")
        title.setObjectName("sectionTitle")
        left_layout.addWidget(title)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Suchen…")
        self.search.textChanged.connect(self.refresh_patient_list)
        left_layout.addWidget(self.search)
        self.patient_table = QTableWidget(0, 2)
        self.patient_table.setHorizontalHeaderLabels(["Name", "Geburtsdatum"])
        self.patient_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.patient_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.patient_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.patient_table.itemSelectionChanged.connect(self.on_patient_selected)
        left_layout.addWidget(self.patient_table, 1)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        details = QFrame()
        details.setObjectName("card")
        details_layout = QGridLayout(details)
        details_layout.addWidget(QLabel("Karteikarte"), 0, 0, 1, 4)
        self.fields: dict[str, QLineEdit | QComboBox] = {}
        for index, (key, label) in enumerate(PATIENT_FIELDS):
            row = 1 + index // 2
            col = (index % 2) * 2
            details_layout.addWidget(QLabel(label), row, col)
            if key == "patiententyp":
                widget = QComboBox()
                widget.addItems(["Privatpatient", "Kassenpatient"])
            else:
                widget = QLineEdit()
            self.fields[key] = widget
            details_layout.addWidget(widget, row, col + 1)
        notes_row = 1 + (len(PATIENT_FIELDS) + 1) // 2
        details_layout.addWidget(QLabel("Freie Notizen"), notes_row, 0, alignment=Qt.AlignmentFlag.AlignTop)
        self.notes = QTextEdit()
        self.notes.setMinimumHeight(150)
        self.notes.setPlaceholderText("Freie Notizen zur Karteikarte")
        details_layout.addWidget(self.notes, notes_row, 1, 1, 3)
        right_layout.addWidget(details)

        services = QFrame()
        services.setObjectName("card")
        service_layout = QVBoxLayout(services)
        service_buttons = QHBoxLayout()
        for label, callback in [
            ("Leistung eintragen", self.add_service),
            ("Leistung bearbeiten", self.edit_service),
            ("Offene Leistung löschen", self.delete_service),
        ]:
            button = QPushButton(label)
            button.clicked.connect(callback)
            service_buttons.addWidget(button)
        service_buttons.addStretch(1)
        invoice_button = QPushButton("Rechnung aus offenen Positionen erstellen")
        invoice_button.clicked.connect(self.invoice)
        service_buttons.addWidget(invoice_button)
        service_layout.addLayout(service_buttons)
        self.service_table = QTableWidget(0, 8)
        self.service_table.setHorizontalHeaderLabels(["Datum", "GOÄ-Nr.", "Leistung", "Zusatznotiz", "Faktor", "Anz.", "Betrag", "Rechnung"])
        header = self.service_table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.service_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.service_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.service_table.doubleClicked.connect(self.edit_service)
        service_layout.addWidget(self.service_table, 1)
        right_layout.addWidget(services, 1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([300, 940])
        self.status = QLabel(f"Datenordner: {self.storage.root}")
        self.status.setObjectName("status")
        outer.addWidget(self.status)
        self.apply_style()

    def apply_style(self) -> None:
        self.setStyleSheet("""
            QMainWindow { background: #F4F7FB; }
            QToolBar { background: #FFFFFF; border: 0; padding: 8px; spacing: 8px; }
            QToolButton, QPushButton { background: #0A4B92; color: white; border: 0; border-radius: 8px; padding: 8px 12px; }
            QPushButton:hover, QToolButton:hover { background: #1265BD; }
            QLineEdit, QComboBox, QTextEdit, QTableWidget { background: white; border: 1px solid #D8E0EA; border-radius: 8px; padding: 5px; }
            QHeaderView::section { background: #EAF1F8; color: #18324A; border: 0; padding: 7px; font-weight: 600; }
            QTableWidget { gridline-color: #EEF2F6; selection-background-color: #D7E9FF; selection-color: #102A43; }
            QFrame#card { background: white; border: 1px solid #E0E7EF; border-radius: 14px; padding: 8px; }
            QLabel#sectionTitle { font-size: 18px; font-weight: 700; color: #18324A; }
            QLabel#status { background: #FFFFFF; border-top: 1px solid #D8E0EA; padding: 6px; color: #40566D; }
        """)

    def refresh_patient_list(self, select_id: str | None = None) -> None:
        query = self.search.text().strip().casefold()
        self.patients = []
        for patient in self.storage.list_patients():
            name = f"{patient.get('nachname', '')}, {patient.get('vorname', '')}".strip(", ")
            if query and query not in name.casefold():
                continue
            self.patients.append(patient)
        self.patient_table.blockSignals(True)
        self.patient_table.setRowCount(len(self.patients))
        for row, patient in enumerate(self.patients):
            name = f"{patient.get('nachname', '')}, {patient.get('vorname', '')}".strip(", ")
            self.patient_table.setItem(row, 0, QTableWidgetItem(name))
            self.patient_table.setItem(row, 1, QTableWidgetItem(patient.get("geburtsdatum", "")))
            if select_id and patient["id"] == select_id:
                self.patient_table.selectRow(row)
        self.patient_table.blockSignals(False)

    def new_patient(self) -> None:
        self.current = self.storage.new_patient()
        self.load_form()
        self.status.setText("Neue Karteikarte – bitte Patientendaten eintragen und speichern.")

    def on_patient_selected(self) -> None:
        row = selected_row(self.patient_table)
        if row >= 0 and row < len(self.patients):
            self.current = self.patients[row]
            self.load_form()

    def load_form(self) -> None:
        if not self.current:
            return
        for key, _label in PATIENT_FIELDS:
            widget = self.fields[key]
            value = self.current.get(key, "Privatpatient" if key == "patiententyp" else "")
            if isinstance(widget, QComboBox):
                widget.setCurrentText(value or "Privatpatient")
            else:
                widget.setText(value)
        self.notes.setPlainText(self.current.get("notizen", ""))
        self.refresh_services()

    def collect_form(self) -> None:
        if not self.current:
            raise ValueError("Bitte zuerst einen Patienten auswählen oder neu anlegen.")
        for key, _label in PATIENT_FIELDS:
            widget = self.fields[key]
            self.current[key] = widget.currentText().strip() if isinstance(widget, QComboBox) else widget.text().strip()
        self.current["notizen"] = self.notes.toPlainText().strip()
        if not self.current["nachname"]:
            raise ValueError("Bitte mindestens den Nachnamen eintragen.")
        if self.current["geburtsdatum"]:
            validate_date(self.current["geburtsdatum"])

    def save_patient(self, quiet: bool = False) -> bool:
        try:
            self.collect_form()
            assert self.current is not None
            self.storage.save_patient(self.current)
        except Exception as exc:
            if not quiet:
                ask_error(self, "Speichern nicht möglich", str(exc))
            return False
        self.refresh_patient_list(self.current["id"])
        self.status.setText(f"Karteikarte gespeichert: {self.current.get('vorname', '')} {self.current.get('nachname', '')}")
        return True

    def refresh_services(self) -> None:
        self.service_rows = []
        if self.current:
            self.service_rows = sorted(self.current.get("leistungen", []), key=lambda item: item.get("datum", ""), reverse=True)
        self.service_table.setRowCount(len(self.service_rows))
        for row, service in enumerate(self.service_rows):
            status = service.get("rechnungsnummer") or "offen"
            values = [
                service.get("datum", ""), service.get("nummer", ""), service.get("text", ""),
                service.get("notiz", ""), service.get("faktor", ""), service.get("anzahl", 1),
                euro(service.get("gesamt_cent", 0)), status,
            ]
            for col, value in enumerate(values):
                self.service_table.setItem(row, col, QTableWidgetItem(str(value)))
        self.service_table.resizeRowsToContents()

    def selected_service(self) -> dict | None:
        row = selected_row(self.service_table)
        if row < 0 or row >= len(self.service_rows):
            QMessageBox.information(self, "Leistung wählen", "Bitte eine offene Leistung auswählen.")
            return None
        return self.service_rows[row]

    def add_service(self) -> None:
        if not self.current:
            QMessageBox.information(self, "Patient wählen", "Bitte zuerst einen Patienten auswählen oder neu anlegen.")
            return
        if not self.save_patient(quiet=True):
            ask_error(self, "Karteikarte unvollständig", "Bitte mindestens einen gültigen Nachnamen eintragen.")
            return
        dialog = ServiceDialog(self, self.storage.load_catalog())
        if dialog.exec() and dialog.result:
            self.current.setdefault("leistungen", []).append(dialog.result)
            self.storage.save_patient(self.current)
            self.refresh_services()
            self.status.setText("Leistung eingetragen und Karteikarte gespeichert.")

    def edit_service(self) -> None:
        if not self.current:
            QMessageBox.information(self, "Patient wählen", "Bitte zuerst einen Patienten auswählen.")
            return
        service = self.selected_service()
        if not service:
            return
        if service.get("rechnungsnummer"):
            ask_error(self, "Nicht bearbeitbar", "Bereits abgerechnete Leistungen bleiben unverändert. Bitte gegebenenfalls stornieren und neu abrechnen.")
            return
        dialog = ServiceDialog(self, self.storage.load_catalog(), service)
        if dialog.exec() and dialog.result:
            index = self.current["leistungen"].index(service)
            self.current["leistungen"][index] = dialog.result
            self.storage.save_patient(self.current)
            self.refresh_services()
            self.status.setText("Leistung bearbeitet und Karteikarte gespeichert.")

    def delete_service(self) -> None:
        if not self.current:
            return
        service = self.selected_service()
        if not service:
            return
        if service.get("rechnungsnummer"):
            ask_error(self, "Nicht löschbar", "Bereits abgerechnete Leistungen bleiben unverändert. Bitte gegebenenfalls stornieren und neu abrechnen.")
            return
        if QMessageBox.question(self, "Leistung löschen", f"Soll die offene Position {service['nummer']} wirklich gelöscht werden?") == QMessageBox.StandardButton.Yes:
            self.current["leistungen"] = [item for item in self.current["leistungen"] if item["id"] != service["id"]]
            self.storage.save_patient(self.current)
            self.refresh_services()

    def invoice(self) -> None:
        if not self.current or not self.save_patient():
            return
        open_items = unbilled_services(self.current)
        if not open_items:
            QMessageBox.information(self, "Keine offenen Positionen", "Für diesen Patienten gibt es keine offenen Leistungen.")
            return
        total = sum(item["gesamt_cent"] for item in open_items)
        config = self.storage.load_config()
        number = config["rechnung"]["naechste_nummer"]
        prompt = f"Rechnung {number} mit {len(open_items)} offenen Position(en) über {euro(total)} erstellen?"
        if QMessageBox.question(self, "Rechnung erstellen", prompt) != QMessageBox.StandardButton.Yes:
            return
        invoice_date, ok = QInputDialog.getText(self, "Rechnungsdatum", "Rechnungsdatum:", text=today_german())
        if not ok or not invoice_date:
            return
        try:
            number, pdf_path = create_invoice(self.storage, self.current, validate_date(invoice_date))
        except Exception as exc:
            ask_error(self, "Rechnung nicht erstellt", str(exc))
            return
        self.refresh_services()
        self.status.setText(f"Rechnung {number} wurde erstellt: {pdf_path}")
        if QMessageBox.question(self, "Rechnung erstellt", f"Rechnung {number} wurde gespeichert. PDF jetzt öffnen?") == QMessageBox.StandardButton.Yes:
            open_path(pdf_path)

    def open_config(self) -> None:
        ConfigDialog(self, self.storage).exec()

    def open_catalog(self) -> None:
        CatalogDialog(self, self.storage).exec()

    def open_invoices(self) -> None:
        InvoiceOverviewDialog(self, self.storage).exec()


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("SimplyAbrechnung")
    app.setOrganizationName("altibo")
    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#0A4B92"))
    app.setPalette(palette)
    window = SimplyAbrechnungApp()
    window.show()
    sys.exit(app.exec())
