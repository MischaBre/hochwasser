from __future__ import annotations

import gettext
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.locale_utils import DEFAULT_LOCALE, normalize_locale


@lru_cache(maxsize=4)
def _load_translations(
    locale: str,
) -> gettext.GNUTranslations | gettext.NullTranslations:
    locales_root = Path(__file__).resolve().parent.parent / "locales"
    return gettext.translation(
        domain="emails",
        localedir=str(locales_root),
        languages=[locale],
        fallback=True,
    )


def translate(locale: str, key: str, **kwargs: Any) -> str:
    normalized = normalize_locale(locale)
    template = _load_translations(normalized).gettext(key)
    if template == key and normalized != DEFAULT_LOCALE:
        template = _load_translations(DEFAULT_LOCALE).gettext(key)
    return template.format(**kwargs)
