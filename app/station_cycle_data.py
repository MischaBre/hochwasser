from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from app.config import AlertJob, Settings
from app.forecasting import (
    forecast_horizon_hours_from_station,
    filter_future_forecast_points,
)
from app.provider_client import WaterLevelProviderClient
from app.waterlevel_models import Measurement, StationInfo


logger = logging.getLogger("hochwasser-alert")


def _job_log_tag(job: AlertJob) -> str:
    return f"[job={job.job_uuid}:{job.name}]"


@dataclass(frozen=True)
class StationCycleData:
    station: StationInfo
    current: Measurement
    historical_points: list[Measurement]
    future_forecast: list[Measurement]
    horizon_hours: int


def load_station_cycle_data(
    now: datetime,
    client: WaterLevelProviderClient,
    settings: Settings,
    job: AlertJob,
) -> StationCycleData:
    station = client.get_station_info()
    current = client.get_current_measurement()
    recent_measurements = client.get_recent_measurements(start="PT24H")
    historical_points = [
        point for point in recent_measurements if point.timestamp < now
    ]

    horizon_hours = forecast_horizon_hours_from_station(
        now,
        station,
        settings.forecast_series_shortname,
    )

    official_forecast = []
    if horizon_hours > 0:
        official_forecast = client.get_official_forecast()
    else:
        logger.info(
            "%s No active forecast timeseries '%s' in station metadata; evaluating current value only",
            _job_log_tag(job),
            settings.forecast_series_shortname,
        )

    future_forecast = filter_future_forecast_points(official_forecast, now)

    logger.info(
        "%s Fetched station data: station=%s current=%s %.1f history_count=%d forecast_count=%d future_forecast_count=%d horizon_hours=%d",
        _job_log_tag(job),
        job.station_uuid,
        current.timestamp.isoformat(),
        current.value,
        len(historical_points),
        len(official_forecast),
        len(future_forecast),
        horizon_hours,
    )

    return StationCycleData(
        station=station,
        current=current,
        historical_points=historical_points,
        future_forecast=future_forecast,
        horizon_hours=horizon_hours,
    )
