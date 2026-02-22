from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.pegelonline import Measurement, StationInfo


@dataclass(frozen=True)
class Crossing:
    timestamp: datetime
    value: float
    source: str


def find_threshold_breach(
    now: datetime,
    current: Measurement,
    forecast_points: list[Measurement],
    limit_cm: float,
    horizon_hours: int,
) -> Crossing | None:
    if current.value >= limit_cm:
        return Crossing(timestamp=now, value=current.value, source="current")

    horizon = now + timedelta(hours=horizon_hours)
    for point in forecast_points:
        if point.timestamp <= now:
            continue
        if point.timestamp > horizon:
            break
        if point.value >= limit_cm:
            return Crossing(
                timestamp=point.timestamp,
                value=point.value,
                source="official",
            )

    return None


def filter_future_forecast_points(
    forecast_points: list[Measurement], now: datetime
) -> list[Measurement]:
    return [point for point in forecast_points if point.timestamp > now]


def _get_forecast_series_window(
    station: StationInfo, forecast_series_shortname: str
) -> tuple[datetime, datetime] | None:
    for series in station.timeseries:
        if not isinstance(series, dict):
            continue
        if (
            str(series.get("shortname", "")).upper()
            != forecast_series_shortname.upper()
        ):
            continue
        start_raw = series.get("start")
        end_raw = series.get("end")
        if not start_raw or not end_raw:
            continue
        try:
            start = datetime.fromisoformat(str(start_raw))
            end = datetime.fromisoformat(str(end_raw))
        except ValueError:
            continue
        return start, end
    return None


def _forecast_horizon_hours_from_station(
    now: datetime,
    station: StationInfo,
    forecast_series_shortname: str,
) -> int:
    window = _get_forecast_series_window(station, forecast_series_shortname)
    if not window:
        return 0
    _, end = window
    remaining_hours = (end - now).total_seconds() / 3600.0
    return max(0, math.ceil(remaining_hours))


def forecast_uncertainty_cm(
    reference_time: datetime, timestamp: datetime
) -> float | None:
    horizon_hours = (timestamp - reference_time).total_seconds() / 3600.0
    if horizon_hours <= 0:
        return None
    if horizon_hours <= 48:
        return 10.0
    if horizon_hours <= 96:
        return 20.0
    return None
