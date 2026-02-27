from __future__ import annotations

import os
from dataclasses import dataclass, field

import psycopg

from apscheduler.triggers.cron import CronTrigger


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
    repeat_alerts_on_check: bool = False


@dataclass(frozen=True)
class Settings:
    provider: str
    database_url: str
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

    health_host: str
    health_port: int
    health_failure_threshold: int
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
    try:
        CronTrigger.from_crontab(expression)
    except ValueError as exc:
        raise ValueError(
            f"{context} schedule_cron must be a valid 5-field crontab expression"
        ) from exc
    return expression


def _load_jobs_from_db(database_url: str) -> tuple[AlertJob, ...]:
    query = """
        SELECT
            job_uuid,
            name,
            station_uuid,
            limit_cm,
            recipients,
            alert_recipient,
            locale,
            schedule_cron,
            repeat_alerts_on_check
        FROM public.alert_jobs
        WHERE enabled = TRUE
        ORDER BY created_at ASC, job_uuid ASC
    """

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

    if not rows:
        return ()

    jobs: list[AlertJob] = []
    seen_job_uuids: set[str] = set()
    for idx, row in enumerate(rows):
        (
            job_uuid_raw,
            name_raw,
            station_uuid_raw,
            limit_raw,
            recipients_raw,
            alert_recipient_raw,
            locale_raw,
            schedule_cron_raw,
            repeat_alerts_on_check_raw,
        ) = row

        station_uuid = str(station_uuid_raw).strip()
        if not station_uuid:
            raise ValueError(f"job at index {idx} missing station_uuid")

        if limit_raw is None:
            raise ValueError(f"job at index {idx} missing limit_cm")

        if recipients_raw is None:
            raise ValueError(f"job at index {idx} missing recipients")
        if alert_recipient_raw is None:
            raise ValueError(f"job at index {idx} missing alert_recipient")
        alert_recipient = str(alert_recipient_raw).strip()
        if not alert_recipient:
            raise ValueError(f"job at index {idx} has invalid alert_recipient")

        job_uuid = str(job_uuid_raw).strip()
        if not job_uuid:
            raise ValueError(f"job at index {idx} missing job_uuid")
        if job_uuid in seen_job_uuids:
            raise ValueError(f"duplicate job_uuid: {job_uuid}")
        seen_job_uuids.add(job_uuid)

        job_name = str(name_raw).strip() or f"job-{idx + 1}"
        if locale_raw is None:
            raise ValueError(f"job at index {idx} missing locale")
        locale = str(locale_raw).strip().lower()
        if locale not in {"de", "en"}:
            raise ValueError(f"job at index {idx} has invalid locale: {locale}")
        schedule_cron = _validate_cron_expression(
            str(schedule_cron_raw),
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
                repeat_alerts_on_check=bool(repeat_alerts_on_check_raw),
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

    database_url = _get_required("DATABASE_URL")
    jobs = _load_jobs_from_db(database_url)

    return Settings(
        provider=provider,
        database_url=database_url,
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
        health_host=os.getenv("HEALTH_HOST", "0.0.0.0"),
        health_port=int(os.getenv("HEALTH_PORT", "8090")),
        health_failure_threshold=int(os.getenv("HEALTH_FAILURE_THRESHOLD", "3")),
        jobs=jobs,
    )
