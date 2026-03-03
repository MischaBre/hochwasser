from __future__ import annotations

import gettext
from functools import lru_cache
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from app.locale_utils import normalize_locale


@lru_cache(maxsize=4)
def _build_environment(locale: str) -> Environment:
    templates_root = Path(__file__).resolve().parent.parent / "templates"
    locales_root = Path(__file__).resolve().parent.parent / "locales"
    env = Environment(
        loader=FileSystemLoader(str(templates_root)),
        autoescape=select_autoescape(enabled_extensions=("html", "xml")),
        undefined=StrictUndefined,
        extensions=["jinja2.ext.i18n"],
        auto_reload=True,
    )

    translations = gettext.translation(
        domain="emails",
        localedir=str(locales_root),
        languages=[normalize_locale(locale)],
        fallback=True,
    )
    env.install_gettext_translations(translations, newstyle=False)
    return env


def render_email_template(locale: str, template_name: str, **context: Any) -> str:
    env = _build_environment(locale)
    template = env.get_template(template_name)
    return template.render(**context)
