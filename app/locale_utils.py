from __future__ import annotations

SUPPORTED_LOCALES = {"de", "en"}
DEFAULT_LOCALE = "de"


def normalize_locale(locale: str) -> str:
    candidate = locale.strip().lower()
    if candidate in SUPPORTED_LOCALES:
        return candidate
    return DEFAULT_LOCALE


def format_float(value: float, locale: str, digits: int = 1) -> str:
    formatted = f"{value:,.{digits}f}"
    if normalize_locale(locale) == "de":
        return formatted.replace(",", "_").replace(".", ",").replace("_", ".")
    return formatted
