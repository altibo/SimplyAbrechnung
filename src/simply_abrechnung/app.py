from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from . import __version__
from .billing import create_invoice, unbilled_services
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


class ServiceDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, catalog: list[dict], service: dict | None = None):
        super().__init__(parent)
        self.title("Leistung bearbeiten" if service else "Leistung eintragen")
        self.resizable(True, False)
        self.transient(parent)
        self.grab_set()
        self.result: dict | None = None
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
        self.labels = [f"{item['nummer']} · {item['text']} · Faktor {item['faktor']} · {euro(item['betrag_cent'])}" for item in self.catalog]
        self.service = service

        frame = ttk.Frame(self, padding=16)
        frame.grid(sticky="nsew")
        ttk.Label(frame, text="Datum").grid(row=0, column=0, sticky="w", pady=4)
        self.date_var = tk.StringVar(value=service.get("datum", today_german()) if service else today_german())
        ttk.Entry(frame, textvariable=self.date_var, width=14).grid(row=0, column=1, sticky="w", pady=4)
        ttk.Label(frame, text="Leistung").grid(row=1, column=0, sticky="nw", pady=4)
        self.service_var = tk.StringVar()
        combo = ttk.Combobox(frame, textvariable=self.service_var, values=self.labels, state="readonly", width=82)
        combo.grid(row=1, column=1, sticky="ew", pady=4)
        if self.labels:
            selected = 0
            if service:
                selected = next((index for index, item in enumerate(self.catalog) if item.get("id") == service.get("katalog_id")), 0)
            combo.current(selected)
        ttk.Label(frame, text="Anzahl").grid(row=2, column=0, sticky="w", pady=4)
        self.quantity_var = tk.IntVar(value=service.get("anzahl", 1) if service else 1)
        ttk.Spinbox(frame, from_=1, to=99, textvariable=self.quantity_var, width=8).grid(row=2, column=1, sticky="w", pady=4)
        ttk.Label(frame, text="Zusatznotiz").grid(row=3, column=0, sticky="w", pady=4)
        self.note_var = tk.StringVar(value=service.get("notiz", "") if service else "")
        ttk.Entry(frame, textvariable=self.note_var, width=70).grid(row=3, column=1, sticky="ew", pady=4)
        buttons = ttk.Frame(frame)
        buttons.grid(row=4, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(buttons, text="Abbrechen", command=self.destroy).pack(side="left", padx=4)
        ttk.Button(buttons, text="Speichern" if service else "Eintragen", command=self.accept).pack(side="left", padx=4)
        frame.columnconfigure(1, weight=1)
        self.bind("<Return>", lambda _event: self.accept())
        self.wait_window()

    def accept(self) -> None:
        try:
            date_value = validate_date(self.date_var.get())
            quantity = int(self.quantity_var.get())
            if quantity < 1:
                raise ValueError("Die Anzahl muss mindestens 1 sein.")
            index = self.labels.index(self.service_var.get())
        except (ValueError, IndexError) as exc:
            messagebox.showerror("Eingabe prüfen", str(exc), parent=self)
            return
        item = self.catalog[index]
        self.result = {
            "id": self.service.get("id", str(uuid.uuid4())) if self.service else str(uuid.uuid4()),
            "katalog_id": item["id"],
            "datum": date_value,
            "nummer": item["nummer"],
            "text": item["text"],
            "faktor": item["faktor"],
            "anzahl": quantity,
            "einzelbetrag_cent": int(item["betrag_cent"]),
            "gesamt_cent": int(item["betrag_cent"]) * quantity,
            "notiz": self.note_var.get().strip(),
            "rechnungsnummer": self.service.get("rechnungsnummer") if self.service else None,
            "rechnungsdatum": self.service.get("rechnungsdatum") if self.service else None,
            "eingetragen_am": self.service.get("eingetragen_am", datetime.now().isoformat(timespec="seconds")) if self.service else datetime.now().isoformat(timespec="seconds"),
        }
        self.destroy()


class ConfigDialog(tk.Toplevel):
    FIELDS = [
        ("arzt", "Name des Arztes"), ("zusatz", "Praxisbezeichnung"), ("strasse", "Straße"),
        ("plz_ort", "PLZ / Ort"), ("telefon", "Telefon"), ("email", "E-Mail"),
        ("bank", "Bank"), ("iban", "IBAN"), ("steuernummer", "Steuernummer / Hinweis"),
        ("zahlungsziel_tage", "Zahlungsziel in Tagen"),
    ]

    def __init__(self, parent: tk.Misc, storage: Storage):
        super().__init__(parent)
        self.title("Praxis-Einstellungen")
        self.transient(parent)
        self.grab_set()
        self.storage = storage
        self.config = storage.load_config()
        self.vars: dict[str, tk.StringVar] = {}
        frame = ttk.Frame(self, padding=16)
        frame.grid(sticky="nsew")
        for row, (key, label) in enumerate(self.FIELDS):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=3)
            var = tk.StringVar(value=str(self.config["praxis"].get(key, "")))
            self.vars[key] = var
            ttk.Entry(frame, textvariable=var, width=55).grid(row=row, column=1, sticky="ew", pady=3)
        row = len(self.FIELDS)
        ttk.Label(frame, text="Nächste Rechnungsnummer").grid(row=row, column=0, sticky="w", pady=3)
        self.invoice_var = tk.StringVar(value=str(self.config["rechnung"]["naechste_nummer"]))
        ttk.Entry(frame, textvariable=self.invoice_var, width=20).grid(row=row, column=1, sticky="w", pady=3)
        row += 1
        ttk.Label(frame, text="Standardbegründung > 2,3").grid(row=row, column=0, sticky="nw", pady=3)
        self.reason = tk.Text(frame, width=55, height=4, wrap="word")
        self.reason.grid(row=row, column=1, sticky="ew", pady=3)
        self.reason.insert("1.0", self.config["praxis"].get("standard_begruendung", ""))
        buttons = ttk.Frame(frame)
        buttons.grid(row=row + 1, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="Abbrechen", command=self.destroy).pack(side="left", padx=4)
        ttk.Button(buttons, text="Speichern", command=self.save).pack(side="left", padx=4)
        frame.columnconfigure(1, weight=1)
        self.wait_window()

    def save(self) -> None:
        number = self.invoice_var.get().strip()
        if not number.isdigit():
            messagebox.showerror("Eingabe prüfen", "Die Rechnungsnummer muss nur aus Ziffern bestehen.", parent=self)
            return
        for key, var in self.vars.items():
            value: str | int = var.get().strip()
            if key == "zahlungsziel_tage":
                try:
                    value = int(value)
                except ValueError:
                    messagebox.showerror("Eingabe prüfen", "Das Zahlungsziel muss eine Zahl sein.", parent=self)
                    return
            self.config["praxis"][key] = value
        self.config["praxis"]["standard_begruendung"] = self.reason.get("1.0", "end").strip()
        self.config["rechnung"]["naechste_nummer"] = number
        self.storage.save_config(self.config)
        self.destroy()


class CatalogDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, storage: Storage):
        super().__init__(parent)
        self.title("GOÄ-Leistungskatalog")
        self.geometry("1000x560")
        self.transient(parent)
        self.grab_set()
        self.storage = storage
        self.catalog = storage.load_catalog()
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)
        columns = ("nummer", "text", "faktor", "betrag", "hinweis")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        for key, title, width in [
            ("nummer", "GOÄ-Nr.", 80), ("text", "Leistung", 410), ("faktor", "Faktor", 65),
            ("betrag", "Betrag", 90), ("hinweis", "Hinweis aus Vorlage", 260),
        ]:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor="w")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")
        buttons = ttk.Frame(self, padding=(12, 0, 12, 12))
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Neue Position", command=self.add).pack(side="left", padx=4)
        ttk.Button(buttons, text="Position bearbeiten", command=self.edit).pack(side="left", padx=4)
        ttk.Button(buttons, text="Schließen", command=self.destroy).pack(side="right", padx=4)
        self.tree.bind("<Double-1>", lambda _event: self.edit())
        self.refresh()
        self.wait_window()

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for index, item in enumerate(self.catalog):
            self.tree.insert("", "end", iid=str(index), values=(item["nummer"], item["text"], item["faktor"], euro(item["betrag_cent"]), item.get("hinweis", "")))

    def add(self) -> None:
        item = self._edit_item(None)
        if item:
            self.catalog.append(item)
            self.storage.save_catalog(self.catalog)
            self.refresh()

    def edit(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Position wählen", "Bitte zuerst eine Position auswählen.", parent=self)
            return
        index = int(selection[0])
        item = self._edit_item(self.catalog[index])
        if item:
            self.catalog[index] = item
            self.storage.save_catalog(self.catalog)
            self.refresh()
            self.tree.selection_set(str(index))

    def _edit_item(self, item: dict | None) -> dict | None:
        dialog = tk.Toplevel(self)
        dialog.title("Position bearbeiten" if item else "Neue Position")
        dialog.transient(self)
        dialog.grab_set()
        values = item or {"nummer": "", "text": "", "faktor": "2,3", "betrag_cent": 0, "hinweis": "", "aktiv": True}
        fields = [("nummer", "GOÄ-Nr."), ("text", "Leistungstext"), ("faktor", "Faktor"), ("betrag", "Betrag in Euro"), ("hinweis", "Hinweis")]
        vars_: dict[str, tk.StringVar] = {}
        frame = ttk.Frame(dialog, padding=14)
        frame.pack(fill="both", expand=True)
        for row, (key, label) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=3)
            initial = euro(values["betrag_cent"]).replace(" €", "") if key == "betrag" else str(values.get(key, ""))
            var = tk.StringVar(value=initial)
            vars_[key] = var
            ttk.Entry(frame, textvariable=var, width=70).grid(row=row, column=1, sticky="ew", pady=3)
        result: list[dict] = []

        def accept() -> None:
            try:
                cents = parse_euro(vars_["betrag"].get())
                if not vars_["nummer"].get().strip() or not vars_["text"].get().strip():
                    raise ValueError("Nummer und Leistungstext dürfen nicht leer sein.")
            except ValueError as exc:
                messagebox.showerror("Eingabe prüfen", str(exc), parent=dialog)
                return
            result.append({
                "id": values.get("id", str(uuid.uuid4())), "nummer": vars_["nummer"].get().strip(),
                "text": vars_["text"].get().strip(), "faktor": vars_["faktor"].get().strip(),
                "betrag_cent": cents, "hinweis": vars_["hinweis"].get().strip(), "aktiv": True,
            })
            dialog.destroy()

        buttons = ttk.Frame(frame)
        buttons.grid(row=len(fields), column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text="Abbrechen", command=dialog.destroy).pack(side="left", padx=4)
        ttk.Button(buttons, text="Speichern", command=accept).pack(side="left", padx=4)
        frame.columnconfigure(1, weight=1)
        dialog.wait_window()
        return result[0] if result else None


class SimplyAbrechnungApp(tk.Tk):
    def __init__(self, storage: Storage | None = None):
        super().__init__()
        self.storage = storage or Storage()
        try:
            self.storage.initialize()
        except Exception as exc:
            messagebox.showerror("Startfehler", f"Der Datenordner konnte nicht angelegt werden:\n{exc}")
            raise
        self.title(f"SimplyAbrechnung {__version__}")
        self.geometry("1220x760")
        self.minsize(980, 650)
        self.current: dict | None = None
        self.patient_by_tree_id: dict[str, dict] = {}
        self.vars = {key: tk.StringVar() for key, _label in PATIENT_FIELDS}
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value=f"Datenordner: {self.storage.root}")
        self._build_ui()
        self.refresh_patient_list()

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self, padding=8)
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Neuer Patient", command=self.new_patient).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Patient speichern", command=self.save_patient).pack(side="left", padx=3)
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(toolbar, text="Praxis-Einstellungen", command=lambda: ConfigDialog(self, self.storage)).pack(side="left", padx=3)
        ttk.Button(toolbar, text="GOÄ-Katalog", command=lambda: CatalogDialog(self, self.storage)).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Datenordner öffnen", command=lambda: open_path(self.storage.root)).pack(side="left", padx=3)
        ttk.Label(toolbar, text=f"Version {__version__}").pack(side="right", padx=6)

        pane = ttk.Panedwindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        left = ttk.Frame(pane, padding=6)
        right = ttk.Frame(pane, padding=6)
        pane.add(left, weight=1)
        pane.add(right, weight=4)

        ttk.Label(left, text="Patienten", font=("TkDefaultFont", 12, "bold")).pack(anchor="w")
        search = ttk.Entry(left, textvariable=self.search_var)
        search.pack(fill="x", pady=6)
        self.search_var.trace_add("write", lambda *_args: self.refresh_patient_list())
        self.patient_tree = ttk.Treeview(left, columns=("name", "geburt"), show="headings", height=25)
        self.patient_tree.heading("name", text="Name")
        self.patient_tree.heading("geburt", text="Geburtsdatum")
        self.patient_tree.column("name", width=180)
        self.patient_tree.column("geburt", width=90)
        self.patient_tree.pack(fill="both", expand=True)
        self.patient_tree.bind("<<TreeviewSelect>>", self.on_patient_selected)

        details = ttk.LabelFrame(right, text="Karteikarte", padding=10)
        details.pack(fill="x")
        for index, (key, label) in enumerate(PATIENT_FIELDS):
            row = index // 2
            col = (index % 2) * 2
            ttk.Label(details, text=label).grid(row=row, column=col, sticky="w", padx=(0, 6), pady=3)
            if key == "patiententyp":
                widget = ttk.Combobox(details, textvariable=self.vars[key], values=("Privatpatient", "Kassenpatient"), state="readonly", width=32)
            else:
                widget = ttk.Entry(details, textvariable=self.vars[key], width=35)
            widget.grid(row=row, column=col + 1, sticky="ew", padx=(0, 14), pady=3)
        details.columnconfigure(1, weight=1)
        details.columnconfigure(3, weight=1)
        notes_row = (len(PATIENT_FIELDS) + 1) // 2
        ttk.Label(details, text="Freie Notizen").grid(row=notes_row, column=0, sticky="nw", pady=3)
        self.notes = tk.Text(details, height=4, wrap="word")
        self.notes.grid(row=notes_row, column=1, columnspan=3, sticky="ew", padx=(0, 14), pady=3)

        services_frame = ttk.LabelFrame(right, text="Behandlungen und Abrechnung", padding=10)
        services_frame.pack(fill="both", expand=True, pady=(8, 0))
        service_buttons = ttk.Frame(services_frame)
        service_buttons.pack(fill="x", pady=(0, 7))
        ttk.Button(service_buttons, text="Leistung eintragen", command=self.add_service).pack(side="left", padx=3)
        ttk.Button(service_buttons, text="Leistung bearbeiten", command=self.edit_service).pack(side="left", padx=3)
        ttk.Button(service_buttons, text="Offene Leistung löschen", command=self.delete_service).pack(side="left", padx=3)
        ttk.Button(service_buttons, text="Rechnung aus offenen Positionen erstellen", command=self.invoice).pack(side="right", padx=3)
        columns = ("datum", "nummer", "leistung", "notiz", "faktor", "anzahl", "betrag", "rechnung")
        self.service_tree = ttk.Treeview(services_frame, columns=columns, show="headings")
        settings = [
            ("datum", "Datum", 85), ("nummer", "GOÄ-Nr.", 75), ("leistung", "Leistung", 380),
            ("notiz", "Zusatznotiz", 180), ("faktor", "Faktor", 55), ("anzahl", "Anz.", 45),
            ("betrag", "Betrag", 85), ("rechnung", "Rechnung", 90),
        ]
        for key, label, width in settings:
            self.service_tree.heading(key, text=label)
            self.service_tree.column(key, width=width, anchor="w")
        scroll = ttk.Scrollbar(services_frame, orient="vertical", command=self.service_tree.yview)
        self.service_tree.configure(yscrollcommand=scroll.set)
        self.service_tree.bind("<Double-1>", lambda _event: self.edit_service())
        self.service_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")
        ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w", padding=4).pack(fill="x")

    def refresh_patient_list(self, select_id: str | None = None) -> None:
        query = self.search_var.get().strip().casefold()
        self.patient_tree.delete(*self.patient_tree.get_children())
        self.patient_by_tree_id.clear()
        for patient in self.storage.list_patients():
            name = f"{patient.get('nachname', '')}, {patient.get('vorname', '')}".strip(", ")
            if query and query not in name.casefold():
                continue
            iid = patient["id"]
            self.patient_by_tree_id[iid] = patient
            self.patient_tree.insert("", "end", iid=iid, values=(name, patient.get("geburtsdatum", "")))
        if select_id and self.patient_tree.exists(select_id):
            self.patient_tree.selection_set(select_id)
            self.patient_tree.see(select_id)

    def new_patient(self) -> None:
        self.current = self.storage.new_patient()
        self._load_form()
        self.status_var.set("Neue Karteikarte – bitte Patientendaten eintragen und speichern.")

    def on_patient_selected(self, _event: tk.Event) -> None:
        selection = self.patient_tree.selection()
        if selection:
            self.current = self.patient_by_tree_id[selection[0]]
            self._load_form()

    def _load_form(self) -> None:
        if not self.current:
            return
        for key, _label in PATIENT_FIELDS:
            default = "Privatpatient" if key == "patiententyp" else ""
            self.vars[key].set(self.current.get(key, default))
        self.notes.delete("1.0", "end")
        self.notes.insert("1.0", self.current.get("notizen", ""))
        self.refresh_services()

    def _collect_form(self) -> None:
        if not self.current:
            raise ValueError("Bitte zuerst einen Patienten auswählen oder neu anlegen.")
        for key, _label in PATIENT_FIELDS:
            self.current[key] = self.vars[key].get().strip()
        self.current["notizen"] = self.notes.get("1.0", "end").strip()
        if not self.current["nachname"]:
            raise ValueError("Bitte mindestens den Nachnamen eintragen.")
        if self.current["geburtsdatum"]:
            validate_date(self.current["geburtsdatum"])

    def save_patient(self, quiet: bool = False) -> bool:
        try:
            self._collect_form()
            assert self.current is not None
            self.storage.save_patient(self.current)
        except Exception as exc:
            if not quiet:
                messagebox.showerror("Speichern nicht möglich", str(exc), parent=self)
            return False
        self.refresh_patient_list(self.current["id"])
        self.status_var.set(f"Karteikarte gespeichert: {self.current.get('vorname', '')} {self.current.get('nachname', '')}")
        return True

    def refresh_services(self) -> None:
        self.service_tree.delete(*self.service_tree.get_children())
        if not self.current:
            return
        for service in sorted(self.current.get("leistungen", []), key=lambda item: item.get("datum", ""), reverse=True):
            status = service.get("rechnungsnummer") or "offen"
            self.service_tree.insert("", "end", iid=service["id"], values=(
                service.get("datum", ""), service.get("nummer", ""), service.get("text", ""),
                service.get("notiz", ""), service.get("faktor", ""), service.get("anzahl", 1),
                euro(service.get("gesamt_cent", 0)), status,
            ))

    def add_service(self) -> None:
        if not self.current:
            messagebox.showinfo("Patient wählen", "Bitte zuerst einen Patienten auswählen oder neu anlegen.", parent=self)
            return
        if not self.save_patient(quiet=True):
            messagebox.showerror("Karteikarte unvollständig", "Bitte mindestens einen gültigen Nachnamen eintragen.", parent=self)
            return
        dialog = ServiceDialog(self, self.storage.load_catalog())
        if dialog.result:
            self.current.setdefault("leistungen", []).append(dialog.result)
            self.storage.save_patient(self.current)
            self.refresh_services()
            self.status_var.set("Leistung eingetragen und Karteikarte gespeichert.")

    def edit_service(self) -> None:
        if not self.current or not self.service_tree.selection():
            messagebox.showinfo("Leistung wählen", "Bitte eine offene Leistung auswählen.", parent=self)
            return
        service_id = self.service_tree.selection()[0]
        service = next((item for item in self.current["leistungen"] if item["id"] == service_id), None)
        if not service:
            return
        if service.get("rechnungsnummer"):
            messagebox.showerror(
                "Nicht bearbeitbar",
                "Bereits abgerechnete Leistungen bleiben unverändert. Bitte gegebenenfalls stornieren und neu abrechnen.",
                parent=self,
            )
            return
        dialog = ServiceDialog(self, self.storage.load_catalog(), service)
        if dialog.result:
            index = self.current["leistungen"].index(service)
            self.current["leistungen"][index] = dialog.result
            self.storage.save_patient(self.current)
            self.refresh_services()
            self.service_tree.selection_set(service_id)
            self.status_var.set("Leistung bearbeitet und Karteikarte gespeichert.")

    def delete_service(self) -> None:
        if not self.current or not self.service_tree.selection():
            messagebox.showinfo("Leistung wählen", "Bitte eine offene Leistung auswählen.", parent=self)
            return
        service_id = self.service_tree.selection()[0]
        service = next((item for item in self.current["leistungen"] if item["id"] == service_id), None)
        if not service:
            return
        if service.get("rechnungsnummer"):
            messagebox.showerror("Nicht löschbar", "Bereits abgerechnete Leistungen bleiben unverändert. Bitte gegebenenfalls stornieren und neu abrechnen.", parent=self)
            return
        if messagebox.askyesno("Leistung löschen", f"Soll die offene Position {service['nummer']} wirklich gelöscht werden?", parent=self):
            self.current["leistungen"] = [item for item in self.current["leistungen"] if item["id"] != service_id]
            self.storage.save_patient(self.current)
            self.refresh_services()

    def invoice(self) -> None:
        if not self.current or not self.save_patient():
            return
        open_items = unbilled_services(self.current)
        if not open_items:
            messagebox.showinfo("Keine offenen Positionen", "Für diesen Patienten gibt es keine offenen Leistungen.", parent=self)
            return
        total = sum(item["gesamt_cent"] for item in open_items)
        config = self.storage.load_config()
        number = config["rechnung"]["naechste_nummer"]
        prompt = f"Rechnung {number} mit {len(open_items)} offenen Position(en) über {euro(total)} erstellen?"
        if not messagebox.askyesno("Rechnung erstellen", prompt, parent=self):
            return
        invoice_date = simpledialog.askstring("Rechnungsdatum", "Rechnungsdatum:", initialvalue=today_german(), parent=self)
        if not invoice_date:
            return
        try:
            invoice_date = validate_date(invoice_date)
            number, pdf_path = create_invoice(self.storage, self.current, invoice_date)
        except Exception as exc:
            messagebox.showerror("Rechnung nicht erstellt", str(exc), parent=self)
            return
        self.refresh_services()
        self.status_var.set(f"Rechnung {number} wurde erstellt: {pdf_path}")
        if messagebox.askyesno("Rechnung erstellt", f"Rechnung {number} wurde gespeichert. PDF jetzt öffnen?", parent=self):
            open_path(pdf_path)


def main() -> None:
    app = SimplyAbrechnungApp()
    app.mainloop()
