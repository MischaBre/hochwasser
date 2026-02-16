from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import Settings
from app.main import (
    Crossing,
    _next_minute_run_at,
    _next_run_at,
    build_email,
    find_threshold_breach,
    find_crossing_from_forecast,
    remember_sent,
    should_send_alert,
)
from app.pegelonline import Measurement, StationInfo
from zoneinfo import ZoneInfo


def make_settings() -> Settings:
    return Settings(
        provider="pegelonline",
        station_uuid="station-1",
        limit_cm=100.0,
        forecast_series_shortname="WV",
        run_every_minute=False,
        forecast_run_hours=(0, 12),
        forecast_horizon_hours=72,
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


def test_next_minute_run() -> None:
    now = datetime(2026, 2, 13, 13, 1, 27, tzinfo=timezone.utc)
    result = _next_minute_run_at(now)
    assert result == datetime(2026, 2, 13, 13, 2, 0, tzinfo=timezone.utc)


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


def test_find_threshold_breach_uses_call_time_for_current() -> None:
    now = datetime(2026, 2, 13, 12, 0, tzinfo=timezone.utc)
    current = Measurement(timestamp=now - timedelta(minutes=5), value=105.0)

    crossing = find_threshold_breach(
        now=now,
        current=current,
        forecast_points=[],
        limit_cm=100.0,
        horizon_hours=72,
    )

    assert crossing is not None
    assert crossing.source == "current"
    assert crossing.timestamp == now


def test_find_threshold_breach_from_forecast() -> None:
    now = datetime.now(tz=timezone.utc)
    current = Measurement(timestamp=now, value=90.0)
    forecast = [
        Measurement(timestamp=now + timedelta(hours=2), value=95.0),
        Measurement(timestamp=now + timedelta(hours=3), value=101.0),
    ]

    crossing = find_threshold_breach(
        now=now,
        current=current,
        forecast_points=forecast,
        limit_cm=100.0,
        horizon_hours=24,
    )

    assert crossing is not None
    assert crossing.source == "official"
    assert crossing.value == 101.0


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


def test_build_email_includes_station_details_and_forecast_table() -> None:
    settings = make_settings()
    zone = ZoneInfo("UTC")
    now = datetime(2026, 2, 13, 12, 0, tzinfo=timezone.utc)
    station = StationInfo(
        uuid="station-1",
        number="12345",
        shortname="TEST",
        longname="TEST STATION",
        km=12.3,
        agency="WSA TEST",
        longitude=10.1,
        latitude=52.5,
        water_shortname="ELBE",
        water_longname="ELBE",
        unit="cm",
        timeseries=({"shortname": "W"}, {"shortname": "WV"}),
    )
    current = Measurement(timestamp=now, value=90.0)
    forecast_points = [
        Measurement(timestamp=now + timedelta(hours=1), value=95.0),
        Measurement(timestamp=now + timedelta(hours=2), value=101.0),
    ]
    crossing = Crossing(
        timestamp=now + timedelta(hours=2), value=101.0, source="official"
    )

    _, body, html_body = build_email(
        station,
        current,
        forecast_points,
        crossing,
        settings,
        zone,
    )

    assert "Station UUID: station-1" in body
    assert "Timeseries: W, WV" in body
    assert "Forecast data (fetched)" in body
    assert "Above limit" in body
    assert "YES" in body
    assert "Max forecast value: 101.0 cm" in body
    assert "<strong style='color:#b00020'>101.0 cm</strong>" in html_body
