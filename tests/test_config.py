import pytest
import json
from pathlib import Path

from app.config import load_settings


def _set_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STATION_UUID", "station-uuid")
    monkeypatch.setenv("LIMIT_CM", "250")
    monkeypatch.setenv("ALERT_RECIPIENTS", "a@example.com,b@example.com")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_SENDER", "sender@example.com")


def test_load_settings_parses_run_hours_and_recipients(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("FORECAST_RUN_HOURS", "12,0,12")

    settings = load_settings()

    assert settings.forecast_run_hours == (0, 12)
    assert settings.alert_recipients == ("a@example.com", "b@example.com")
    assert settings.health_host == "0.0.0.0"
    assert settings.health_port == 8090
    assert settings.locale == "de"
    assert settings.jobs[0].station_uuid == "station-uuid"
    assert settings.jobs[0].limit_cm == 250.0
    assert settings.jobs[0].recipients == ("a@example.com", "b@example.com")
    assert settings.jobs[0].locale == "de"


def test_load_settings_invalid_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("PROVIDER", "elwis")

    with pytest.raises(ValueError, match="Only PROVIDER=pegelonline"):
        load_settings()


def test_load_settings_invalid_run_hour(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("FORECAST_RUN_HOURS", "24")

    with pytest.raises(ValueError, match="hours between 0 and 23"):
        load_settings()


def test_load_settings_invalid_locale(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("EMAIL_LOCALE", "fr")

    with pytest.raises(ValueError, match="EMAIL_LOCALE must be either"):
        load_settings()


def test_load_settings_from_jobs_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _set_required_env(monkeypatch)
    jobs_file = tmp_path / "jobs.json"
    jobs_file.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "name": "rhine-main",
                        "station_uuid": "station-a",
                        "limit_cm": 600,
                        "locale": "en",
                        "recipients": ["one@example.com", "two@example.com"],
                    },
                    {
                        "station_uuid": "station-a",
                        "limit_cm": 700,
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
    assert settings.jobs[0].station_uuid == "station-a"
    assert settings.jobs[0].limit_cm == 600.0
    assert settings.jobs[0].recipients == ("one@example.com", "two@example.com")
    assert settings.jobs[0].locale == "en"
    assert settings.jobs[1].name == "job-2"
    assert settings.jobs[1].limit_cm == 700.0
    assert settings.jobs[1].locale == "de"
