from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from datetime import date

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QLineEdit

import simply_abrechnung.app as app_module
from simply_abrechnung import __version__
from simply_abrechnung.app import (
    FreeNotesDialog,
    InvoiceOverviewDialog,
    OPEN_ROW_COLOR,
    PAID_ROW_COLOR,
    REMINDER_ROW_COLOR,
    ServiceDetailsDialog,
    SimplyAbrechnungApp,
    TEXT_COLOR,
    app_icon,
    invoice_status_color,
    patient_age,
    unbilled_total,
)
from simply_abrechnung.storage import Storage
from simply_abrechnung.utils import euro


def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_qt_theme_uses_dark_content_text(tmp_path):
    app = qt_app()
    window = SimplyAbrechnungApp(Storage(tmp_path))
    try:
        text_color = app.palette().color(QPalette.ColorRole.Text).name().upper()
        window_text_color = app.palette().color(QPalette.ColorRole.WindowText).name().upper()
        button_text_color = app.palette().color(QPalette.ColorRole.ButtonText).name().upper()

        assert text_color == TEXT_COLOR.upper()
        assert window_text_color == TEXT_COLOR.upper()
        assert button_text_color == "#FFFFFF"
    finally:
        window.close()


def test_qt_stylesheet_sets_readable_widget_text_colors(tmp_path):
    qt_app()
    window = SimplyAbrechnungApp(Storage(tmp_path))
    try:
        style = window.styleSheet()
        assert f"QWidget {{ color: {TEXT_COLOR}; }}" in style
        assert f"QLabel {{ color: {TEXT_COLOR};" in style
        assert f"QLineEdit, QComboBox, QTextEdit, QPlainTextEdit" in style
        assert f"color: {TEXT_COLOR};" in style
        assert f"QTableWidget::item {{ color: {TEXT_COLOR}; }}" in style
        assert "QToolButton, QPushButton { background: #0A4B92; color: #FFFFFF;" in style
    finally:
        window.close()


def billed_service() -> dict:
    return {
        "id": "svc-1",
        "datum": "22.06.2026",
        "nummer": "3",
        "text": "Eingehende Beratung",
        "faktor": "2,3",
        "anzahl": 1,
        "gesamt_cent": 2010,
        "notiz": "Ausführliche Verlaufsnotiz mit wichtiger Info.",
        "rechnungsnummer": "260111",
        "rechnungsdatum": "23.06.2026",
    }


def test_billed_service_details_are_read_only(tmp_path):
    qt_app()
    dialog = ServiceDetailsDialog(None, billed_service())
    try:
        assert dialog.windowTitle() == "Abgerechnete Leistung ansehen"
        assert dialog.note.isReadOnly()
        assert "wichtiger Info" in dialog.note.toPlainText()
        assert all(field.isReadOnly() for field in dialog.findChildren(QLineEdit))
    finally:
        dialog.close()


def test_editing_billed_service_opens_read_only_details(tmp_path, monkeypatch):
    qt_app()
    window = SimplyAbrechnungApp(Storage(tmp_path))
    opened: list[dict] = []

    class FakeDetailsDialog:
        def __init__(self, _parent, service):
            opened.append(service)

        def exec(self):
            return 1

    monkeypatch.setattr(app_module, "ServiceDetailsDialog", FakeDetailsDialog)
    try:
        window.current = window.storage.new_patient()
        window.current["nachname"] = "Muster"
        window.current["leistungen"] = [billed_service()]
        window.load_form()
        window.service_table.selectRow(0)

        window.edit_service()

        assert len(opened) == 1
        assert opened[0]["notiz"] == "Ausführliche Verlaufsnotiz mit wichtiger Info."
        assert opened[0]["rechnungsnummer"] == "260111"
    finally:
        window.close()


def test_patient_age_and_unbilled_total_helpers():
    patient = {
        "geburtsdatum": "24.06.1986",
        "leistungen": [
            {"gesamt_cent": 1000, "rechnungsnummer": None},
            {"gesamt_cent": 2500, "rechnungsnummer": ""},
            {"gesamt_cent": 9999, "rechnungsnummer": "260100"},
        ],
    }

    assert patient_age(patient, date(2026, 6, 23)) == "39"
    assert patient_age(patient, date(2026, 6, 24)) == "40"
    assert unbilled_total(patient) == 3500


def test_patient_list_shows_age_and_open_amount(tmp_path):
    qt_app()
    storage = Storage(tmp_path)
    storage.initialize()
    patient = storage.new_patient()
    patient.update({
        "vorname": "Erika",
        "nachname": "Muster",
        "geburtsdatum": "01.01.1980",
        "leistungen": [
            {"id": "open", "gesamt_cent": 2010, "rechnungsnummer": None},
            {"id": "billed", "gesamt_cent": 1072, "rechnungsnummer": "260111"},
        ],
    })
    storage.save_patient(patient)
    window = SimplyAbrechnungApp(storage)
    try:
        assert window.patient_table.columnCount() == 3
        assert window.patient_table.horizontalHeaderItem(1).text() == "Alter"
        assert window.patient_table.horizontalHeaderItem(2).text() == "Offen"
        assert window.patient_table.item(0, 1).text().isdigit()
        assert window.patient_table.item(0, 2).text() == euro(2010)
    finally:
        window.close()


def test_free_notes_preview_is_compact_and_dialog_is_large(tmp_path):
    qt_app()
    window = SimplyAbrechnungApp(Storage(tmp_path))
    try:
        assert window.notes.isReadOnly()
        assert window.notes.maximumHeight() < 120

        dialog = FreeNotesDialog(window, "viel\ntext")
        try:
            line_height = dialog.editor.fontMetrics().lineSpacing()
            assert dialog.editor.minimumHeight() >= line_height * 20
            assert dialog.editor.toPlainText() == "viel\ntext"
        finally:
            dialog.close()
    finally:
        window.close()


def test_version_is_only_shown_in_window_title(tmp_path):
    qt_app()
    window = SimplyAbrechnungApp(Storage(tmp_path))
    try:
        assert __version__ in window.windowTitle()
        assert all(label.text() != f"  Version {__version__}" for label in window.findChildren(app_module.QLabel))
    finally:
        window.close()


def test_app_icon_assets_are_loaded(tmp_path):
    qt_app()
    window = SimplyAbrechnungApp(Storage(tmp_path))
    try:
        assert not app_icon().isNull()
        assert not window.windowIcon().isNull()
        assert Path("assets/icons/app_icon.png").is_file()
        assert Path("assets/icons/app_icon.ico").is_file()
        assert Path("assets/icons/app_icon.icns").is_file()
        spec = Path("SimplyAbrechnung.spec").read_text(encoding="utf-8")
        assert "app_icon.ico" in spec
        assert "app_icon.icns" in spec
    finally:
        window.close()


def invoice_record(number: str, status: str = "offen", reminders: list[dict] | None = None) -> dict:
    return {
        "schema_version": 2,
        "id": f"invoice-{number}",
        "rechnungsnummer": number,
        "rechnungsdatum": "23.06.2026",
        "erstellt_am": "2026-06-23T10:00:00",
        "gesamt_cent": 2010,
        "zahlungsstatus": status,
        "bezahlt_am": "24.06.2026" if status == "bezahlt" else None,
        "zahlungserinnerungen": reminders or [],
        "praxis": {},
        "patient": {"vorname": "Erika", "nachname": f"Muster{number}"},
        "leistungen": [],
    }


def test_invoice_status_colors():
    assert invoice_status_color(invoice_record("1", "bezahlt")).name().upper() == PAID_ROW_COLOR.upper()
    assert invoice_status_color(invoice_record("2")).name().upper() == OPEN_ROW_COLOR.upper()
    assert invoice_status_color(invoice_record("3", reminders=[{"datum": "30.06.2026"}])).name().upper() == REMINDER_ROW_COLOR.upper()


def test_invoice_overview_colors_rows_by_payment_status(tmp_path):
    qt_app()
    storage = Storage(tmp_path)
    storage.initialize()
    for record in [
        invoice_record("260101", "bezahlt"),
        invoice_record("260102"),
        invoice_record("260103", reminders=[{"datum": "30.06.2026"}]),
    ]:
        storage.save_invoice_record(record["rechnungsnummer"], record)

    dialog = InvoiceOverviewDialog(None, storage)
    try:
        colors = {
            dialog.table.item(row, 0).text(): dialog.table.item(row, 4).background().color().name().upper()
            for row in range(dialog.table.rowCount())
        }
        assert colors["260101"] == PAID_ROW_COLOR.upper()
        assert colors["260102"] == OPEN_ROW_COLOR.upper()
        assert colors["260103"] == REMINDER_ROW_COLOR.upper()
    finally:
        dialog.close()


def test_invoice_overview_patient_column_is_narrower(tmp_path):
    qt_app()
    storage = Storage(tmp_path)
    storage.initialize()
    storage.save_invoice_record("260101", invoice_record("260101"))

    dialog = InvoiceOverviewDialog(None, storage)
    try:
        header = dialog.table.horizontalHeader()
        assert header.sectionResizeMode(2) == app_module.QHeaderView.ResizeMode.Interactive
        assert header.sectionSize(2) <= 190
        assert header.sectionResizeMode(6) == app_module.QHeaderView.ResizeMode.Stretch
    finally:
        dialog.close()
