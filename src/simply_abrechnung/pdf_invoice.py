from __future__ import annotations

import io
import zipfile
from pathlib import Path

import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .storage import resource_path
from .utils import euro


MM = 72 / 25.4
BLUE = colors.HexColor("#0A4B92")
FONT_DIR = Path(reportlab.__file__).resolve().parent / "fonts"
pdfmetrics.registerFont(TTFont("Vera", str(FONT_DIR / "Vera.ttf")))
pdfmetrics.registerFont(TTFont("VeraBd", str(FONT_DIR / "VeraBd.ttf")))


def _logo() -> ImageReader | None:
    candidates = list((resource_path("Vorlage")).glob("*Rech*.docx"))
    if not candidates:
        candidates = list((resource_path("vorlage")).glob("*Rech*.docx"))
    if not candidates:
        return None
    try:
        with zipfile.ZipFile(candidates[0]) as archive:
            return ImageReader(io.BytesIO(archive.read("word/media/image1.png")))
    except (OSError, KeyError, zipfile.BadZipFile):
        return None


def _draw_wrapped(c: canvas.Canvas, text: str, x: float, y: float, width: float, font: str, size: float, leading: float) -> float:
    lines = _wrap_lines(text, width, font, size)
    c.setFont(font, size)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def _wrap_lines(text: str, width: float, font: str, size: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or stringWidth(candidate, font, size) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _header(c: canvas.Canvas, practice: dict, page: int, logo: ImageReader | None) -> float:
    width, height = A4
    c.setFillColor(BLUE)
    c.setFont("VeraBd", 11)
    c.drawString(20 * MM, height - 19 * MM, f"Privatrechnung (GOÄ) · {practice.get('arzt', '')}")
    c.setFillColor(colors.black)
    c.setFont("Vera", 8.5)
    lines = [practice.get("zusatz", ""), practice.get("strasse", ""), practice.get("plz_ort", ""), practice.get("telefon", "")]
    y = height - 25 * MM
    for line in filter(None, lines):
        c.drawString(20 * MM, y, line)
        y -= 4 * MM
    if logo:
        c.drawImage(logo, width - 53 * MM, height - 52 * MM, width=36 * MM, height=36 * MM, preserveAspectRatio=True, mask="auto")
    c.setStrokeColor(BLUE)
    c.setLineWidth(1)
    c.line(20 * MM, height - 47 * MM, width - 20 * MM, height - 47 * MM)
    if page > 1:
        c.setFont("Vera", 8)
        c.drawRightString(width - 20 * MM, height - 53 * MM, f"Seite {page}")
    return height - 56 * MM


def _table_header(c: canvas.Canvas, y: float) -> float:
    x = 20 * MM
    widths = [21 * MM, 18 * MM, 79 * MM, 15 * MM, 13 * MM, 24 * MM]
    labels = ["Datum", "GOÄ-Nr.", "Leistung", "Faktor", "Anz.", "Betrag"]
    c.setFillColor(BLUE)
    c.rect(x, y - 7 * MM, sum(widths), 7 * MM, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("VeraBd", 8)
    pos = x
    for label, cell_width in zip(labels, widths):
        c.drawString(pos + 1.5 * MM, y - 4.7 * MM, label)
        pos += cell_width
    return y - 7 * MM


def _service_row(c: canvas.Canvas, service: dict, y: float, shade: bool) -> float:
    x = 20 * MM
    widths = [21 * MM, 18 * MM, 79 * MM, 15 * MM, 13 * MM, 24 * MM]
    desc = service.get("text", "")
    lines = _wrap_lines(desc, widths[2] - 3 * MM, "Vera", 8)
    row_height = max(7 * MM, (len(lines) * 3.7 + 3) * MM)
    if shade:
        c.setFillColor(colors.HexColor("#EDF3FA"))
        c.rect(x, y - row_height, sum(widths), row_height, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Vera", 8)
    values = [
        service.get("datum", ""), service.get("nummer", ""), None,
        service.get("faktor", ""), str(service.get("anzahl", 1)), euro(int(service.get("gesamt_cent", 0))),
    ]
    pos = x
    for value, cell_width in zip(values, widths):
        if value is not None:
            c.drawString(pos + 1.5 * MM, y - 4.5 * MM, str(value))
        pos += cell_width
    text_x = x + widths[0] + widths[1] + 1.5 * MM
    text_y = y - 4.5 * MM
    for line in lines:
        c.drawString(text_x, text_y, line)
        text_y -= 3.7 * MM
    c.setStrokeColor(colors.HexColor("#C9D5E2"))
    c.line(x, y - row_height, x + sum(widths), y - row_height)
    return y - row_height


def create_invoice_pdf(record: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output), pagesize=A4, pageCompression=1)
    c.setTitle(f"Rechnung {record['rechnungsnummer']}")
    c.setAuthor(record["praxis"].get("arzt", ""))
    logo = _logo()
    patient = record["patient"]
    practice = record["praxis"]
    width, height = A4
    page = 1
    y = _header(c, practice, page, logo)

    sender = f"{practice.get('arzt', '')} · {practice.get('strasse', '')} · {practice.get('plz_ort', '')}"
    c.setFont("Vera", 6.5)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawString(20 * MM, y, sender)
    y -= 6 * MM
    c.setFillColor(colors.black)
    c.setFont("Vera", 10)
    name = " ".join(filter(None, [patient.get("anrede", ""), patient.get("vorname", ""), patient.get("nachname", "")]))
    for line in [name, patient.get("strasse", ""), f"{patient.get('plz', '')} {patient.get('ort', '')}".strip()]:
        c.drawString(20 * MM, y, line)
        y -= 5 * MM

    info_y = height - 63 * MM
    c.setFont("VeraBd", 10)
    c.drawRightString(width - 20 * MM, info_y, f"Rechnung Nr.: {record['rechnungsnummer']}")
    c.setFont("Vera", 9)
    c.drawRightString(width - 20 * MM, info_y - 5 * MM, f"Datum: {record['rechnungsdatum']}")
    if patient.get("geburtsdatum"):
        c.drawRightString(width - 20 * MM, info_y - 10 * MM, f"Geburtsdatum: {patient['geburtsdatum']}")

    y -= 5 * MM
    if patient.get("diagnose"):
        c.setFont("VeraBd", 9)
        c.drawString(20 * MM, y, "Diagnose:")
        y = _draw_wrapped(c, patient["diagnose"], 39 * MM, y, 148 * MM, "Vera", 9, 4 * MM)
        y -= 2 * MM
    c.setFont("Vera", 9)
    c.drawString(20 * MM, y, "Für meine ärztlichen Leistungen erlaube ich mir zu berechnen:")
    y -= 7 * MM
    y = _table_header(c, y)
    for index, service in enumerate(record["leistungen"]):
        expected_lines = len(_wrap_lines(service.get("text", ""), 76 * MM, "Vera", 8))
        expected_height = max(7 * MM, (expected_lines * 3.7 + 3) * MM)
        if y - expected_height < 45 * MM:
            c.showPage()
            page += 1
            y = _header(c, practice, page, logo)
            y = _table_header(c, y)
        y = _service_row(c, service, y, index % 2 == 1)

    y -= 5 * MM
    c.setFillColor(BLUE)
    c.setFont("VeraBd", 12)
    c.drawRightString(width - 20 * MM, y, f"Gesamt: {euro(record['gesamt_cent'])}")
    c.setFillColor(colors.black)
    y -= 10 * MM

    factors = {service.get("faktor") for service in record["leistungen"]}
    if any(factor and float(str(factor).replace(",", ".")) > 2.3 for factor in factors):
        c.setFont("VeraBd", 8.5)
        c.drawString(20 * MM, y, "Begründung für Steigerungsfaktor > 2,3 (§ 5 Abs. 2 GOÄ):")
        y -= 4.5 * MM
        y = _draw_wrapped(c, practice.get("standard_begruendung", ""), 20 * MM, y, 170 * MM, "Vera", 8.5, 4 * MM)
        y -= 3 * MM

    if y < 45 * MM:
        c.showPage()
        page += 1
        y = _header(c, practice, page, logo)
    c.setFont("Vera", 8.5)
    payment = f"Zahlung bitte innerhalb von {practice.get('zahlungsziel_tage', 14)} Tagen an {practice.get('arzt', '')}, {practice.get('bank', '')}, IBAN: {practice.get('iban', '')}."
    y = _draw_wrapped(c, payment, 20 * MM, y, 170 * MM, "Vera", 8.5, 4 * MM)
    y -= 8 * MM
    c.drawString(20 * MM, y, "Mit freundlichen Grüßen")
    y -= 8 * MM
    c.setFont("VeraBd", 9)
    c.drawString(20 * MM, y, practice.get("arzt", ""))

    c.setFont("Vera", 7)
    footer = " · ".join(filter(None, [practice.get("arzt", ""), practice.get("telefon", ""), practice.get("email", ""), practice.get("steuernummer", "")]))
    c.setFillColor(colors.HexColor("#555555"))
    c.drawCentredString(width / 2, 12 * MM, footer)
    c.save()
