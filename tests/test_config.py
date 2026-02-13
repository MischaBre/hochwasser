import pytest

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
