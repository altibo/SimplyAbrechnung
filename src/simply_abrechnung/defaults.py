from __future__ import annotations


DEFAULT_CONFIG = {
    "schema_version": 1,
    "praxis": {
        "arzt": "Dr. Rena Bolz",
        "zusatz": "Allgemeinmedizin - Naturheilverfahren",
        "strasse": "Guttenberger Str. 25",
        "plz_ort": "97234 Reichenberg",
        "telefon": "0049 173 650 1633",
        "email": "",
        "bank": "VR Bank Würzburg",
        "iban": "DE63 7909 0000 0103 7272 97",
        "steuernummer": "",
        "zahlungsziel_tage": 14,
        "logo_datei": "",
        "akzentfarbe": "#0A4B92",
        "standard_begruendung": (
            "Überdurchschnittlicher Zeitaufwand sowie erhöhte Schwierigkeit "
            "aufgrund der individuellen medizinischen Situation."
        ),
    },
    "rechnung": {"naechste_nummer": "260111"},
}


def item(code: str, description: str, factor: str, cents: int, note: str = "") -> dict:
    key = f"{code}-{factor}-{cents}-{len(description)}".replace(" ", "_").replace(",", "_")
    return {
        "id": key,
        "nummer": code,
        "text": description,
        "faktor": factor,
        "betrag_cent": cents,
        "hinweis": note,
        "aktiv": True,
    }


DEFAULT_CATALOG = [
    item("1", "Beratung, auch telefonisch", "2,3", 1072),
    item("3", "Eingehende, das gewöhnliche Maß übersteigende Beratung", "2,3", 2010),
    item("3", "Eingehende, das gewöhnliche Maß übersteigende Beratung", "3,5", 3060),
    item("4", "Erhebung einer Fremdanamnese und/oder Unterweisung von Bezugspersonen", "2,3", 2967),
    item("5", "Symptombezogene Untersuchung", "2,3", 1619),
    item("7", "Vollständige Untersuchung mindestens eines Organsystems", "3,5", 3264),
    item("8", "Untersuchung zur Erhebung des Ganzkörperstatus", "2,3", 3637),
    item("15", "Einleitung und Koordination flankierender Maßnahmen bei chronisch Kranken", "2,3", 4023, "Vorlage enthält zusätzlich den Prüfhinweis '24,15?'."),
    item("30", "Homöopathische Erstanamnese", "2,3", 12065),
    item("30", "Homöopathische Erstanamnese", "3,5", 18360),
    item("A 30", "Homöopathische Erstanamnese, analog", "3,5", 18360),
    item("31", "Homöopathische Folgeanamnese (mindestens 30 Minuten)", "2,3", 6033),
    item("31", "Homöopathische Folgeanamnese (mindestens 30 Minuten)", "3,5", 9180),
    item("34", "Erörterung der Auswirkungen einer Krankheit auf die Lebensgestaltung", "2,3", 4023, "Vorlage enthält zusätzlich den Prüfhinweis '24,15?'."),
    item("60", "Eingehende Erörterung einer Krankheit auf die Lebensführung, mindestens 10 Minuten", "3,5", 4480),
    item("76", "Individueller Therapie- oder Diätplan mit Erläuterung", "2,3", 997),
    item("269a", "Intrakutane Reiztherapie / Akupunktur", "2,3", 4825),
    item("269a", "Intrakutane Reiztherapie / Akupunktur", "3,5", 7342),
    item("A 269", "Analoge komplexe therapeutische Sitzung", "2,3", 4825),
    item("A 269", "Anpassung und Optimierung der Therapie", "3,5", 7300),
    item("A 385", "Bioenergetischer Test, analog", "2,3", 1180),
    item("806", "Behandlung durch gezielte Exploration und eingehendes therapeutisches Gespräch", "2,3", 3351, "Vorlage enthält zusätzlich den Prüfhinweis '23,30?'."),
    item("812", "Psychotherapeutische Notfallbehandlung", "2,3", 6702, "Vorlage enthält zusätzlich den Prüfhinweis '18,50?'."),
    item("A 825", "Neurologischer Test Hirnnerven", "2,3", 2010),
    item("A 826", "Neurologischer Test Koordination", "2,3", 2682),
    item("A 832", "Frequenzbasierte Regulationsdiagnostik und -therapie, analog GOÄ 832", "2,3", 6300),
    item("A 839", "Frequenzbasierte Regulationsdiagnostik und -therapie, analog GOÄ 839", "2,3", 9384),
    item("A 839", "Frequenzbasierte Regulationsdiagnostik und -therapie, analog", "5,0", 20640),
    item("A 839", "Analoge apparative Funktionsdiagnostik (z. B. vegetative Reaktion)", "3,5", 14300),
    item("A 839", "Analoge apparative Funktionsdiagnostik (z. B. vegetative Reaktion)", "4,4", 18000),
    item("849", "Psychische Behandlung bei psychoreaktiven und psychosomatischen Störungen", "3,5", 4692),
    item("70", "Dokumentation", "1,5", 1000),
    item("A 60", "Analoge intensive Therapieplanung", "3,5", 4480),
]
