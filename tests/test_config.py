import pytest

from app.config import AlertJob, load_settings


def _set_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_SENDER", "sender@example.com")
    monkeypatch.setenv("TZ", "Europe/Berlin")


def test_load_settings_parses_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)

    monkeypatch.setattr(
        "app.config._load_jobs_from_db",
        lambda _database_url: (
            AlertJob(
                job_uuid="job-default-uuid",
                name="default-job",
                station_uuid="station-uuid",
                limit_cm=250,
                recipients=("a@example.com", "b@example.com"),
                alert_recipient="ops@example.com",
                locale="de",
                schedule_cron="*/30 * * * *",
                repeat_alerts_on_check=False,
            ),
        ),
    )

    settings = load_settings()

    assert settings.health_host == "0.0.0.0"
    assert settings.health_port == 8090
    assert settings.database_url == "postgresql://user:pass@localhost:5432/db"
    assert settings.jobs[0].station_uuid == "station-uuid"
    assert settings.jobs[0].job_uuid == "job-default-uuid"
    assert settings.jobs[0].limit_cm == 250.0
    assert settings.jobs[0].recipients == ("a@example.com", "b@example.com")
    assert settings.jobs[0].alert_recipient == "ops@example.com"
    assert settings.jobs[0].locale == "de"
    assert settings.jobs[0].schedule_cron == "*/30 * * * *"


def test_load_settings_invalid_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_env(monkeypatch)
    monkeypatch.setenv("PROVIDER", "elwis")

    with pytest.raises(ValueError, match="Only PROVIDER=pegelonline"):
        load_settings()


def test_load_settings_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_SENDER", "sender@example.com")
    monkeypatch.setenv("TZ", "Europe/Berlin")

    with pytest.raises(ValueError, match="Missing required environment variable"):
        load_settings()


def test_load_settings_accepts_empty_enabled_jobs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_required_env(monkeypatch)

    monkeypatch.setattr("app.config._load_jobs_from_db", lambda _database_url: ())

    settings = load_settings()
    assert settings.jobs == ()
