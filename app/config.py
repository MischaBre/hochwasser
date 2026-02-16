from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _get_required(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


def _get_bool(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    provider: str
    station_uuid: str
    limit_cm: float
    forecast_series_shortname: str
    run_every_minute: bool
    forecast_run_hours: tuple[int, ...]
    forecast_horizon_hours: int
    dedupe_hours: int
    timezone: str

    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_sender: str
    smtp_use_starttls: bool
    smtp_use_ssl: bool

    alert_recipients: tuple[str, ...]
    state_file: Path


def load_settings() -> Settings:
    recipients_raw = _get_required("ALERT_RECIPIENTS")
    recipients = tuple(
        addr.strip() for addr in recipients_raw.split(",") if addr.strip()
    )
    if not recipients:
        raise ValueError("ALERT_RECIPIENTS must contain at least one address")

    provider = os.getenv("PROVIDER", "pegelonline").strip().lower()
    if provider != "pegelonline":
        raise ValueError(
            "Only PROVIDER=pegelonline is supported right now. "
            "ELWIS support can be added later."
        )

    run_hours_raw = os.getenv("FORECAST_RUN_HOURS", "0,12")
    run_hours: list[int] = []
    for token in run_hours_raw.split(","):
        stripped = token.strip()
        if not stripped:
            continue
        hour = int(stripped)
        if hour < 0 or hour > 23:
            raise ValueError("FORECAST_RUN_HOURS must contain hours between 0 and 23")
        run_hours.append(hour)

    if not run_hours:
        raise ValueError("FORECAST_RUN_HOURS must contain at least one hour")

    run_hours = sorted(set(run_hours))

    return Settings(
        provider=provider,
        station_uuid=_get_required("STATION_UUID"),
        limit_cm=float(_get_required("LIMIT_CM")),
        forecast_series_shortname=os.getenv("FORECAST_SERIES_SHORTNAME", "WV")
        .strip()
        .upper(),
        run_every_minute=_get_bool("RUN_EVERY_MINUTE", False),
        forecast_run_hours=tuple(run_hours),
        forecast_horizon_hours=int(os.getenv("FORECAST_HORIZON_HOURS", "72")),
        dedupe_hours=int(os.getenv("ALERT_DEDUPE_HOURS", "24")),
        timezone=os.getenv("TZ", "Europe/Berlin"),
        smtp_host=_get_required("SMTP_HOST"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_sender=_get_required("SMTP_SENDER"),
        smtp_use_starttls=_get_bool("SMTP_USE_STARTTLS", True),
        smtp_use_ssl=_get_bool("SMTP_USE_SSL", False),
        alert_recipients=recipients,
        state_file=Path(os.getenv("STATE_FILE", "/data/state.json")),
    )
