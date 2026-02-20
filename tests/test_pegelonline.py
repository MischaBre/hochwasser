from __future__ import annotations

from datetime import datetime, timezone

from app.pegelonline import PegelonlineClient


def test_get_official_forecast_returns_empty_on_primary_404() -> None:
    client = PegelonlineClient("station-1", forecast_series_shortname="WV")

    def fake_get_json(endpoint: str):
        raise RuntimeError(f"HTTP 404 for https://example.invalid{endpoint}")

    client._get_json = fake_get_json  # type: ignore[method-assign]

    forecast = client.get_official_forecast()

    assert forecast == []


def test_get_official_forecast_parses_primary_series() -> None:
    client = PegelonlineClient("station-1", forecast_series_shortname="WV")

    def fake_get_json(endpoint: str):
        assert endpoint == "/stations/station-1/WV/measurements.json"
        return [
            {"timestamp": "2026-02-20T12:00:00+00:00", "value": 101.0},
            {"timestamp": "2026-02-20T10:00:00+00:00", "value": 99.0},
        ]

    client._get_json = fake_get_json  # type: ignore[method-assign]

    forecast = client.get_official_forecast()

    assert len(forecast) == 2
    assert forecast[0].timestamp == datetime(2026, 2, 20, 10, 0, tzinfo=timezone.utc)
    assert forecast[1].value == 101.0
