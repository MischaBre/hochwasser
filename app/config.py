from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
import json


CRON_VALIDATION_REGEX = re.compile(
    r"^(@every (\d+(ns|us|µs|ms|s|m|h))+)|((((\d+,)+\d+|(\d+(\/|-)\d+)|(\*(\/\d+)?)|\d+) ?){5,7})$"
)


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
    job_uuid: str
    name: str
    station_uuid: str
    limit_cm: float
    recipients: tuple[str, ...]
    alert_recipient: str
    locale: str
    schedule_cron: str


@dataclass(frozen=True)
class Settings:
    provider: str
    forecast_series_shortname: str
    dedupe_hours: int
    timezone: str

    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_sender: str
    smtp_use_starttls: bool
    smtp_use_ssl: bool
    admin_recipients: tuple[str, ...]

    state_file: Path
    health_host: str
    health_port: int
    health_failure_threshold: int
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


def _validate_cron_expression(value: str, context: str) -> str:
    expression = value.strip()
    if not expression:
        raise ValueError(f"{context} has invalid schedule_cron")
    if CRON_VALIDATION_REGEX.fullmatch(expression) is None:
        raise ValueError(f"{context} schedule_cron must match cron validation regex")
    return expression


def _parse_schedule_cron(raw_job: dict[str, object], context: str) -> str:
    schedule_cron_raw = raw_job.get("schedule_cron")
    if schedule_cron_raw is None:
        raise ValueError(f"{context} missing schedule_cron")
    return _validate_cron_expression(str(schedule_cron_raw), context)


def _load_jobs_from_file(path: Path) -> tuple[AlertJob, ...]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    raw_jobs = payload.get("jobs") if isinstance(payload, dict) else payload
    if not isinstance(raw_jobs, list) or not raw_jobs:
        raise ValueError("JOBS_FILE must contain a non-empty 'jobs' array")

    jobs: list[AlertJob] = []
    seen_job_uuids: set[str] = set()
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
        alert_recipient_raw = item.get("alert_recipient")
        if alert_recipient_raw is None:
            raise ValueError(f"job at index {idx} missing alert_recipient")
        alert_recipient = str(alert_recipient_raw).strip()
        if not alert_recipient:
            raise ValueError(f"job at index {idx} has invalid alert_recipient")

        job_uuid = str(item.get("job_uuid", "")).strip()
        if not job_uuid:
            raise ValueError(f"job at index {idx} missing job_uuid")
        if job_uuid in seen_job_uuids:
            raise ValueError(f"duplicate job_uuid: {job_uuid}")
        seen_job_uuids.add(job_uuid)

        job_name = str(item.get("name", f"job-{idx + 1}")).strip() or f"job-{idx + 1}"
        locale_raw = item.get("locale")
        if locale_raw is None:
            raise ValueError(f"job at index {idx} missing locale")
        locale = str(locale_raw).strip().lower()
        if locale not in {"de", "en"}:
            raise ValueError(f"job at index {idx} has invalid locale: {locale}")
        schedule_cron = _parse_schedule_cron(
            item,
            context=f"job at index {idx}",
        )
        jobs.append(
            AlertJob(
                job_uuid=job_uuid,
                name=job_name,
                station_uuid=station_uuid,
                limit_cm=float(limit_raw),
                recipients=_parse_recipients(recipients_raw),
                alert_recipient=alert_recipient,
                locale=locale,
                schedule_cron=schedule_cron,
            )
        )

    return tuple(jobs)


def load_settings() -> Settings:
    provider = os.getenv("PROVIDER", "pegelonline").strip().lower()
    if provider != "pegelonline":
        raise ValueError(
            "Only PROVIDER=pegelonline is supported right now. "
            "ELWIS support can be added later."
        )

    jobs_file = Path(os.getenv("JOBS_FILE", "/data/jobs.json"))
    if not jobs_file.exists():
        raise ValueError(f"JOBS_FILE does not exist: {jobs_file}")
    jobs = _load_jobs_from_file(jobs_file)

    return Settings(
        provider=provider,
        forecast_series_shortname=os.getenv("FORECAST_SERIES_SHORTNAME", "WV")
        .strip()
        .upper(),
        dedupe_hours=int(os.getenv("ALERT_DEDUPE_HOURS", "24")),
        timezone=_get_required("TZ"),
        smtp_host=_get_required("SMTP_HOST"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_sender=_get_required("SMTP_SENDER"),
        smtp_use_starttls=_get_bool("SMTP_USE_STARTTLS", True),
        smtp_use_ssl=_get_bool("SMTP_USE_SSL", False),
        admin_recipients=_parse_recipients(_get_required("ALERT_RECIPIENTS")),
        state_file=Path(os.getenv("STATE_FILE", "/data/state.json")),
        health_host=os.getenv("HEALTH_HOST", "0.0.0.0"),
        health_port=int(os.getenv("HEALTH_PORT", "8090")),
        health_failure_threshold=int(os.getenv("HEALTH_FAILURE_THRESHOLD", "3")),
        jobs_file=jobs_file,
        jobs=jobs,
    )
