import json
from pathlib import Path

import pytest

from app.config import load_settings


def _set_required_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, jobs_payload: dict | None = None
) -> None:
    if jobs_payload is None:
        jobs_payload = {
            "jobs": [
                {
                    "job_uuid": "job-default-uuid",
                    "name": "default-job",
                    "station_uuid": "station-uuid",
                    "limit_cm": 250,
                    "alert_recipient": "ops@example.com",
                    "locale": "de",
                    "schedule_cron": "*/30 * * * *",
                    "recipients": ["a@example.com", "b@example.com"],
                }
            ]
        }
    jobs_file = tmp_path / "jobs.json"
    jobs_file.write_text(json.dumps(jobs_payload), encoding="utf-8")
    monkeypatch.setenv("JOBS_FILE", str(jobs_file))
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_SENDER", "sender@example.com")
    monkeypatch.setenv("ALERT_RECIPIENTS", "admin@example.com")
    monkeypatch.setenv("TZ", "Europe/Berlin")


def test_load_settings_parses_recipients_and_defaults(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _set_required_env(monkeypatch, tmp_path)

    settings = load_settings()

    assert settings.health_host == "0.0.0.0"
    assert settings.health_port == 8090
    assert settings.jobs[0].station_uuid == "station-uuid"
    assert settings.jobs[0].job_uuid == "job-default-uuid"
    assert settings.jobs[0].limit_cm == 250.0
    assert settings.jobs[0].recipients == ("a@example.com", "b@example.com")
    assert settings.jobs[0].alert_recipient == "ops@example.com"
    assert settings.jobs[0].locale == "de"
    assert settings.jobs[0].schedule_cron == "*/30 * * * *"
    assert settings.admin_recipients == ("admin@example.com",)


def test_load_settings_invalid_provider(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _set_required_env(monkeypatch, tmp_path)
    monkeypatch.setenv("PROVIDER", "elwis")

    with pytest.raises(ValueError, match="Only PROVIDER=pegelonline"):
        load_settings()


def test_load_settings_rejects_invalid_job_locale(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _set_required_env(monkeypatch, tmp_path)
    jobs_file = tmp_path / "jobs.json"
    jobs_file.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "job_uuid": "bad-locale-uuid",
                        "name": "bad-locale",
                        "station_uuid": "station-a",
                        "limit_cm": 600,
                        "alert_recipient": "ops@example.com",
                        "locale": "fr",
                        "schedule_cron": "*/15 * * * *",
                        "recipients": ["one@example.com"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("JOBS_FILE", str(jobs_file))

    with pytest.raises(ValueError, match="invalid locale"):
        load_settings()


def test_load_settings_from_jobs_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _set_required_env(monkeypatch, tmp_path)
    jobs_file = tmp_path / "jobs.json"
    jobs_file.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "job_uuid": "job-uuid-1",
                        "name": "rhine-main",
                        "station_uuid": "station-a",
                        "limit_cm": 600,
                        "alert_recipient": "ops-1@example.com",
                        "locale": "en",
                        "schedule_cron": "*/15 * * * *",
                        "recipients": ["one@example.com", "two@example.com"],
                    },
                    {
                        "job_uuid": "job-uuid-2",
                        "station_uuid": "station-a",
                        "limit_cm": 700,
                        "alert_recipient": "ops-2@example.com",
                        "locale": "de",
                        "schedule_cron": "0 * * * *",
                        "recipients": "three@example.com",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("JOBS_FILE", str(jobs_file))

    settings = load_settings()

    assert len(settings.jobs) == 2
    assert settings.jobs[0].name == "rhine-main"
    assert settings.jobs[0].job_uuid == "job-uuid-1"
    assert settings.jobs[0].station_uuid == "station-a"
    assert settings.jobs[0].limit_cm == 600.0
    assert settings.jobs[0].recipients == ("one@example.com", "two@example.com")
    assert settings.jobs[0].alert_recipient == "ops-1@example.com"
    assert settings.jobs[0].locale == "en"
    assert settings.jobs[0].schedule_cron == "*/15 * * * *"
    assert settings.jobs[1].name == "job-2"
    assert settings.jobs[1].job_uuid == "job-uuid-2"
    assert settings.jobs[1].limit_cm == 700.0
    assert settings.jobs[1].alert_recipient == "ops-2@example.com"
    assert settings.jobs[1].locale == "de"
    assert settings.jobs[1].schedule_cron == "0 * * * *"


def test_load_settings_rejects_duplicate_job_uuids(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _set_required_env(monkeypatch, tmp_path)
    jobs_file = tmp_path / "jobs.json"
    jobs_file.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "job_uuid": "dup-uuid",
                        "name": "one",
                        "station_uuid": "station-a",
                        "limit_cm": 600,
                        "alert_recipient": "ops-1@example.com",
                        "locale": "de",
                        "schedule_cron": "*/5 * * * *",
                        "recipients": ["one@example.com"],
                    },
                    {
                        "job_uuid": "dup-uuid",
                        "name": "two",
                        "station_uuid": "station-b",
                        "limit_cm": 700,
                        "alert_recipient": "ops-2@example.com",
                        "locale": "de",
                        "schedule_cron": "*/10 * * * *",
                        "recipients": ["two@example.com"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("JOBS_FILE", str(jobs_file))

    with pytest.raises(ValueError, match="duplicate job_uuid"):
        load_settings()


def test_load_settings_accepts_job_schedule_cron(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _set_required_env(monkeypatch, tmp_path)
    jobs_file = tmp_path / "jobs.json"
    jobs_file.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "job_uuid": "cron-uuid",
                        "name": "cron-job",
                        "station_uuid": "station-a",
                        "limit_cm": 600,
                        "alert_recipient": "ops@example.com",
                        "locale": "de",
                        "schedule_cron": "0 */6 * * *",
                        "recipients": ["one@example.com"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("JOBS_FILE", str(jobs_file))

    settings = load_settings()

    assert settings.jobs[0].schedule_cron == "0 */6 * * *"


def test_load_settings_rejects_invalid_job_schedule_cron(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _set_required_env(monkeypatch, tmp_path)
    jobs_file = tmp_path / "jobs.json"
    jobs_file.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "job_uuid": "bad-cron-uuid",
                        "name": "bad-cron-job",
                        "station_uuid": "station-a",
                        "limit_cm": 600,
                        "alert_recipient": "ops@example.com",
                        "locale": "de",
                        "schedule_cron": "*/5 * * *",
                        "recipients": ["one@example.com"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("JOBS_FILE", str(jobs_file))

    with pytest.raises(
        ValueError, match="schedule_cron must match cron validation regex"
    ):
        load_settings()


def test_load_settings_requires_schedule_cron_in_jobs_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _set_required_env(monkeypatch, tmp_path)
    jobs_file = tmp_path / "jobs.json"
    jobs_file.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "job_uuid": "missing-cron-uuid",
                        "name": "missing-cron",
                        "station_uuid": "station-a",
                        "limit_cm": 600,
                        "alert_recipient": "ops@example.com",
                        "locale": "de",
                        "recipients": ["one@example.com"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("JOBS_FILE", str(jobs_file))

    with pytest.raises(ValueError, match="missing schedule_cron"):
        load_settings()


def test_load_settings_requires_job_uuid_in_jobs_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _set_required_env(monkeypatch, tmp_path)
    jobs_file = tmp_path / "jobs.json"
    jobs_file.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "name": "missing-uuid",
                        "station_uuid": "station-a",
                        "limit_cm": 600,
                        "alert_recipient": "ops@example.com",
                        "locale": "de",
                        "schedule_cron": "*/15 * * * *",
                        "recipients": ["one@example.com"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("JOBS_FILE", str(jobs_file))

    with pytest.raises(ValueError, match="missing job_uuid"):
        load_settings()


def test_load_settings_requires_job_locale_in_jobs_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _set_required_env(monkeypatch, tmp_path)
    jobs_file = tmp_path / "jobs.json"
    jobs_file.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "job_uuid": "missing-locale-uuid",
                        "name": "missing-locale",
                        "station_uuid": "station-a",
                        "limit_cm": 600,
                        "alert_recipient": "ops@example.com",
                        "schedule_cron": "*/15 * * * *",
                        "recipients": ["one@example.com"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("JOBS_FILE", str(jobs_file))

    with pytest.raises(ValueError, match="missing locale"):
        load_settings()


def test_load_settings_requires_job_alert_recipient_in_jobs_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _set_required_env(monkeypatch, tmp_path)
    jobs_file = tmp_path / "jobs.json"
    jobs_file.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "job_uuid": "missing-alert-recipient-uuid",
                        "name": "missing-alert-recipient",
                        "station_uuid": "station-a",
                        "limit_cm": 600,
                        "locale": "de",
                        "schedule_cron": "*/15 * * * *",
                        "recipients": ["one@example.com"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("JOBS_FILE", str(jobs_file))

    with pytest.raises(ValueError, match="missing alert_recipient"):
        load_settings()


def test_load_settings_requires_jobs_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    missing_jobs = tmp_path / "missing-jobs.json"
    monkeypatch.setenv("JOBS_FILE", str(missing_jobs))
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_SENDER", "sender@example.com")
    monkeypatch.setenv("ALERT_RECIPIENTS", "admin@example.com")

    with pytest.raises(ValueError, match="JOBS_FILE does not exist"):
        load_settings()
