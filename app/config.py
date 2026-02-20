from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
import json


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
class AlertJob:
    name: str
    station_uuid: str
    limit_cm: float
    recipients: tuple[str, ...]
    locale: str


@dataclass(frozen=True)
class Settings:
    provider: str
    station_uuid: str
    limit_cm: float
    forecast_series_shortname: str
    run_every_minute: bool
    forecast_run_hours: tuple[int, ...]
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
    health_host: str
    health_port: int
    health_failure_threshold: int
    locale: str
    jobs_file: Path
    jobs: tuple[AlertJob, ...] = field(default_factory=tuple)


def _parse_recipients(value: str | list[str]) -> tuple[str, ...]:
    if isinstance(value, list):
        recipients = tuple(str(addr).strip() for addr in value if str(addr).strip())
    else:
        recipients = tuple(
            addr.strip() for addr in str(value).split(",") if addr.strip()
        )
    if not recipients:
        raise ValueError("job recipients must contain at least one address")
    return recipients


def _load_jobs_from_file(path: Path) -> tuple[AlertJob, ...]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    raw_jobs = payload.get("jobs") if isinstance(payload, dict) else payload
    if not isinstance(raw_jobs, list) or not raw_jobs:
        raise ValueError("JOBS_FILE must contain a non-empty 'jobs' array")

    jobs: list[AlertJob] = []
    for idx, item in enumerate(raw_jobs):
        if not isinstance(item, dict):
            raise ValueError(f"job at index {idx} must be an object")

        station_uuid = str(item.get("station_uuid", "")).strip()
        if not station_uuid:
            raise ValueError(f"job at index {idx} missing station_uuid")

        limit_raw = item.get("limit_cm")
        if limit_raw is None:
            raise ValueError(f"job at index {idx} missing limit_cm")

        recipients_raw = item.get("recipients")
        if recipients_raw is None:
            raise ValueError(f"job at index {idx} missing recipients")

        job_name = str(item.get("name", f"job-{idx + 1}")).strip() or f"job-{idx + 1}"
        locale = str(item.get("locale", "de")).strip().lower()
        if locale not in {"de", "en"}:
            raise ValueError(f"job at index {idx} has invalid locale: {locale}")
        jobs.append(
            AlertJob(
                name=job_name,
                station_uuid=station_uuid,
                limit_cm=float(limit_raw),
                recipients=_parse_recipients(recipients_raw),
                locale=locale,
            )
        )

    return tuple(jobs)


def _load_jobs_from_legacy_env() -> tuple[AlertJob, ...]:
    recipients = _parse_recipients(_get_required("ALERT_RECIPIENTS"))
    return (
        AlertJob(
            name="default",
            station_uuid=_get_required("STATION_UUID"),
            limit_cm=float(_get_required("LIMIT_CM")),
            recipients=recipients,
            locale=os.getenv("EMAIL_LOCALE", "de").strip().lower(),
        ),
    )


def load_settings() -> Settings:
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

    locale = os.getenv("EMAIL_LOCALE", "de").strip().lower()
    if locale not in {"de", "en"}:
        raise ValueError("EMAIL_LOCALE must be either 'de' or 'en'")

    jobs_file = Path(os.getenv("JOBS_FILE", "/data/jobs.json"))
    if jobs_file.exists():
        jobs = _load_jobs_from_file(jobs_file)
    else:
        jobs = _load_jobs_from_legacy_env()

    default_job = jobs[0]

    return Settings(
        provider=provider,
        station_uuid=default_job.station_uuid,
        limit_cm=default_job.limit_cm,
        forecast_series_shortname=os.getenv("FORECAST_SERIES_SHORTNAME", "WV")
        .strip()
        .upper(),
        run_every_minute=_get_bool("DEBUG_RUN_EVERY_MINUTE", False),
        forecast_run_hours=tuple(run_hours),
        dedupe_hours=int(os.getenv("ALERT_DEDUPE_HOURS", "24")),
        timezone=os.getenv("TZ", "Europe/Berlin"),
        smtp_host=_get_required("SMTP_HOST"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_sender=_get_required("SMTP_SENDER"),
        smtp_use_starttls=_get_bool("SMTP_USE_STARTTLS", True),
        smtp_use_ssl=_get_bool("SMTP_USE_SSL", False),
        alert_recipients=default_job.recipients,
        state_file=Path(os.getenv("STATE_FILE", "/data/state.json")),
        health_host=os.getenv("HEALTH_HOST", "0.0.0.0"),
        health_port=int(os.getenv("HEALTH_PORT", "8090")),
        health_failure_threshold=int(os.getenv("HEALTH_FAILURE_THRESHOLD", "3")),
        locale=locale,
        jobs_file=jobs_file,
        jobs=jobs,
    )
