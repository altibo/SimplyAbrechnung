from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


GERMAN_DATE = "%d.%m.%Y"


def today_german() -> str:
    return date.today().strftime(GERMAN_DATE)


def validate_date(value: str) -> str:
    value = value.strip()
    datetime.strptime(value, GERMAN_DATE)
    return value


def parse_euro(value: str) -> int:
    normalized = value.strip().replace("€", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        amount = Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError("Bitte einen gültigen Euro-Betrag eingeben, z. B. 20,10.") from exc
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def euro(cents: int) -> str:
    return f"{cents / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9ÄÖÜäöüß_-]+", "_", value.strip())
    return cleaned.strip("_") or "Patient"


def next_invoice_number(current: str) -> str:
    current = current.strip()
    if not current.isdigit():
        raise ValueError("Die Rechnungsnummer muss nur aus Ziffern bestehen.")
    return str(int(current) + 1).zfill(len(current))
