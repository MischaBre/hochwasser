from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import Settings
from app.main import (
    Crossing,
    _next_run_at,
    extrapolate_crossing,
    find_crossing_from_forecast,
    remember_sent,
    should_send_alert,
)
from app.pegelonline import Measurement


def make_settings() -> Settings:
    return Settings(
        provider="pegelonline",
        station_uuid="station-1",
        limit_cm=100.0,
        forecast_run_hours=(0, 12),
        forecast_horizon_hours=72,
        rising_points=12,
        min_slope_cm_per_hour=0.1,
        dedupe_hours=24,
        timezone="Europe/Berlin",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="",
        smtp_password="",
        smtp_sender="sender@example.com",
        smtp_use_starttls=True,
        smtp_use_ssl=False,
        alert_recipients=("a@example.com",),
        state_file=Path("/tmp/state.json"),
    )


def test_next_run_same_day() -> None:
    now = datetime(2026, 2, 13, 10, 30, tzinfo=timezone.utc)
    result = _next_run_at(now, (0, 12))
    assert result == datetime(2026, 2, 13, 12, 0, tzinfo=timezone.utc)


def test_next_run_next_day() -> None:
    now = datetime(2026, 2, 13, 13, 1, tzinfo=timezone.utc)
    result = _next_run_at(now, (0, 12))
    assert result == datetime(2026, 2, 14, 0, 0, tzinfo=timezone.utc)


def test_find_crossing_from_forecast_within_horizon() -> None:
    now = datetime.now(tz=timezone.utc)
    points = [
        Measurement(timestamp=now + timedelta(hours=1), value=95.0),
        Measurement(timestamp=now + timedelta(hours=2), value=101.0),
    ]

    crossing = find_crossing_from_forecast(points, limit_cm=100.0, horizon_hours=3)
    assert crossing is not None
    assert crossing.value == 101.0
    assert crossing.source == "official"


def test_find_crossing_from_forecast_outside_horizon() -> None:
    now = datetime.now(tz=timezone.utc)
    points = [Measurement(timestamp=now + timedelta(hours=5), value=120.0)]

    crossing = find_crossing_from_forecast(points, limit_cm=100.0, horizon_hours=3)
    assert crossing is None


def test_extrapolate_crossing_trend() -> None:
    now = datetime.now(tz=timezone.utc)
    recent = [
        Measurement(timestamp=now - timedelta(hours=2), value=90.0),
        Measurement(timestamp=now - timedelta(hours=1), value=95.0),
        Measurement(timestamp=now, value=100.0),
    ]
    current = Measurement(timestamp=now, value=100.0)

    crossing = extrapolate_crossing(
        recent_points=recent,
        current=current,
        limit_cm=110.0,
        horizon_hours=5,
        rising_points=3,
        min_slope_cm_per_hour=0.1,
    )
    assert crossing is not None
    assert crossing.source == "trend"
    assert crossing.value == 110.0


def test_should_send_alert_dedup() -> None:
    settings = make_settings()
    state = {"sent_keys": {}}
    now = datetime(2026, 2, 13, 12, 0, tzinfo=timezone.utc)
    crossing = Crossing(timestamp=now, value=100.0, source="official")

    assert should_send_alert(settings, state, crossing, now) is True
    remember_sent(state, now)
    assert (
        should_send_alert(settings, state, crossing, now + timedelta(hours=1)) is False
    )
    assert (
        should_send_alert(settings, state, crossing, now + timedelta(hours=25)) is True
    )
