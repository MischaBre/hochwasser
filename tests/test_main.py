from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import AlertJob, Settings
from app.main import (
    Crossing,
    _forecast_horizon_hours_from_station,
    build_email,
    filter_future_forecast_points,
    find_threshold_breach,
)
from app.pegelonline import Measurement, StationInfo
from app.state_store import AlertStateStore, build_dedupe_key
from zoneinfo import ZoneInfo


def make_settings() -> Settings:
    return Settings(
        provider="pegelonline",
        forecast_series_shortname="WV",
        dedupe_hours=24,
        timezone="Europe/Berlin",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="",
        smtp_password="",
        smtp_sender="sender@example.com",
        smtp_use_starttls=True,
        smtp_use_ssl=False,
        admin_recipients=("admin@example.com",),
        state_file=Path("/tmp/state.json"),
        health_host="0.0.0.0",
        health_port=8090,
        health_failure_threshold=3,
        jobs_file=Path("/tmp/jobs.json"),
    )


def make_job(locale: str = "en", limit_cm: float = 100.0) -> AlertJob:
    return AlertJob(
        job_uuid="job-uuid-1",
        name="job-1",
        station_uuid="station-1",
        limit_cm=limit_cm,
        recipients=("a@example.com",),
        alert_recipient="ops@example.com",
        locale=locale,
        schedule_cron="*/15 * * * *",
    )


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


def test_find_threshold_breach_ignores_non_future_points() -> None:
    now = datetime.now(tz=timezone.utc)
    current = Measurement(timestamp=now, value=90.0)
    forecast = [
        Measurement(timestamp=now - timedelta(minutes=10), value=120.0),
        Measurement(timestamp=now, value=130.0),
        Measurement(timestamp=now + timedelta(hours=1), value=101.0),
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
    assert crossing.timestamp == forecast[2].timestamp


def test_filter_future_forecast_points() -> None:
    now = datetime.now(tz=timezone.utc)
    forecast = [
        Measurement(timestamp=now - timedelta(minutes=10), value=99.0),
        Measurement(timestamp=now, value=100.0),
        Measurement(timestamp=now + timedelta(minutes=10), value=101.0),
    ]

    filtered = filter_future_forecast_points(forecast, now)

    assert filtered == [forecast[2]]


def test_forecast_horizon_hours_from_station_metadata() -> None:
    now = datetime(2026, 2, 20, 7, 0, tzinfo=timezone.utc)
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
        timeseries=(
            {
                "shortname": "WV",
                "start": "2026-02-20T07:00:00+00:00",
                "end": "2026-02-24T07:00:00+00:00",
            },
        ),
    )

    assert _forecast_horizon_hours_from_station(now, station, "WV") == 96


def test_forecast_horizon_hours_zero_without_wv() -> None:
    now = datetime(2026, 2, 20, 7, 0, tzinfo=timezone.utc)
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
        timeseries=(),
    )

    assert _forecast_horizon_hours_from_station(now, station, "WV") == 0


def test_should_send_alert_dedup(tmp_path: Path) -> None:
    settings = make_settings()
    state_store = AlertStateStore(tmp_path / "state.json")
    now = datetime(2026, 2, 13, 12, 0, tzinfo=timezone.utc)
    crossing = Crossing(timestamp=now, value=100.0, source="official")
    dedupe_key = build_dedupe_key(
        job_uuid="job-uuid-1",
        crossing_timestamp=crossing.timestamp,
        alert_recipients=make_job().recipients,
    )

    first = state_store.run_if_due(
        key=dedupe_key,
        now=now,
        dedupe_hours=settings.dedupe_hours,
        action=lambda: None,
    )
    second = state_store.run_if_due(
        key=dedupe_key,
        now=now + timedelta(hours=1),
        dedupe_hours=settings.dedupe_hours,
        action=lambda: None,
    )
    third = state_store.run_if_due(
        key=dedupe_key,
        now=now + timedelta(hours=25),
        dedupe_hours=settings.dedupe_hours,
        action=lambda: None,
    )

    assert first is True
    assert second is False
    assert third is True


def test_build_email_includes_station_details_and_forecast_table() -> None:
    job = make_job(locale="en", limit_cm=100.0)
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
        now,
        station,
        current,
        [Measurement(timestamp=now - timedelta(hours=1), value=88.0)],
        forecast_points,
        crossing,
        job.limit_cm,
        job.locale,
        zone,
    )

    assert "Station UUID: station-1" in body
    assert "Timeseries: W, WV" in body
    assert "Forecast data (fetched)" in body
    assert "80% conf." in body
    assert "91.0..111.0 cm" in body
    assert "Above limit" in body
    assert "YES" in body
    assert "Max forecast value: 101.0 cm" in body
    assert "Hydrograph" in html_body
    assert "data:image/png;base64," in html_body
    assert "gray dashed: 80% min/max forecast band" in html_body
    assert "<strong style='color:#b00020'>101.0 cm</strong>" in html_body


def test_build_email_localized_german() -> None:
    job = make_job(locale="de", limit_cm=100.0)
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
        Measurement(timestamp=now + timedelta(hours=2), value=101.0),
    ]
    crossing = Crossing(
        timestamp=now + timedelta(hours=2), value=101.0, source="official"
    )

    _, body, html_body = build_email(
        now,
        station,
        current,
        [Measurement(timestamp=now - timedelta(hours=1), value=88.0)],
        forecast_points,
        crossing,
        job.limit_cm,
        job.locale,
        zone,
    )

    assert "Stationsinformationen" in body
    assert "80% Konf." in body
    assert "91,0..111,0 cm" in body
    assert "Hydrograph" in html_body
    assert "data:image/png;base64," in html_body
