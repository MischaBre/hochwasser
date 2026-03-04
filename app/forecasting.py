from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.state_store import (
    STATE_CROSSING_ACTIVE,
    STATE_CROSSING_INCOMING,
    STATE_CROSSING_SOON_OVER,
    STATE_NO_CROSSING,
)
from app.waterlevel_models import Measurement, StationInfo


@dataclass(frozen=True)
class Crossing:
    timestamp: datetime
    value: float
    source: str


@dataclass(frozen=True)
class LifecycleEvaluation:
    state: str
    crossing: Crossing | None
    predicted_crossing_at: datetime | None
    predicted_end_at: datetime | None
    predicted_peak_cm: float | None
    predicted_peak_at: datetime | None


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


def forecast_series_window(
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


def forecast_horizon_hours_from_station(
    now: datetime,
    station: StationInfo,
    forecast_series_shortname: str,
) -> int:
    window = forecast_series_window(station, forecast_series_shortname)
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


def evaluate_lifecycle(
    now: datetime,
    current: Measurement,
    forecast_points: list[Measurement],
    limit_cm: float,
    horizon_hours: int,
) -> LifecycleEvaluation:
    crossing = find_threshold_breach(
        now=now,
        current=current,
        forecast_points=forecast_points,
        limit_cm=limit_cm,
        horizon_hours=horizon_hours,
    )
    sorted_forecast = sorted(forecast_points, key=lambda item: item.timestamp)

    if current.value >= limit_cm:
        peak_value = current.value
        peak_at = now
        for point in sorted_forecast:
            if point.value > peak_value:
                peak_value = point.value
                peak_at = point.timestamp
        predicted_end_at = next(
            (point.timestamp for point in sorted_forecast if point.value < limit_cm),
            None,
        )
        return LifecycleEvaluation(
            state=(
                STATE_CROSSING_SOON_OVER
                if predicted_end_at is not None
                else STATE_CROSSING_ACTIVE
            ),
            crossing=Crossing(timestamp=now, value=current.value, source="current"),
            predicted_crossing_at=now,
            predicted_end_at=predicted_end_at,
            predicted_peak_cm=peak_value,
            predicted_peak_at=peak_at,
        )

    if crossing is not None:
        peak_point = max(sorted_forecast, key=lambda p: p.value, default=None)
        return LifecycleEvaluation(
            state=STATE_CROSSING_INCOMING,
            crossing=crossing,
            predicted_crossing_at=crossing.timestamp,
            predicted_end_at=None,
            predicted_peak_cm=peak_point.value if peak_point else None,
            predicted_peak_at=peak_point.timestamp if peak_point else None,
        )

    return LifecycleEvaluation(
        state=STATE_NO_CROSSING,
        crossing=None,
        predicted_crossing_at=None,
        predicted_end_at=None,
        predicted_peak_cm=None,
        predicted_peak_at=None,
    )
