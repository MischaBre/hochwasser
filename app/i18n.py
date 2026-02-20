from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

SUPPORTED_LOCALES = {"de", "en"}
DEFAULT_LOCALE = "de"


@lru_cache(maxsize=4)
def _load_catalog(locale: str) -> dict[str, str]:
    catalog_path = (
        Path(__file__).resolve().parent.parent / "localization" / f"{locale}.json"
    )
    with catalog_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return {str(key): str(value) for key, value in data.items()}


def normalize_locale(locale: str) -> str:
    candidate = locale.strip().lower()
    if candidate in SUPPORTED_LOCALES:
        return candidate
    return DEFAULT_LOCALE


def tr(locale: str, key: str, **kwargs: Any) -> str:
    normalized = normalize_locale(locale)
    catalog = _load_catalog(normalized)
    template = catalog.get(key)
    if template is None:
        fallback_catalog = _load_catalog(DEFAULT_LOCALE)
        template = fallback_catalog.get(key, key)
    return template.format(**kwargs)


def format_float(value: float, locale: str, digits: int = 1) -> str:
    formatted = f"{value:,.{digits}f}"
    if normalize_locale(locale) == "de":
        return formatted.replace(",", "_").replace(".", ",").replace("_", ".")
    return formatted
