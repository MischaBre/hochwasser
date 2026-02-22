from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import AlertJob, Settings, load_settings
from app.email_content import build_email
from app.forecasting import (
    Crossing,
    _forecast_horizon_hours_from_station,
    filter_future_forecast_points,
    find_threshold_breach,
)
from app.notifier import send_alert_email
from app.pegelonline import Measurement, PegelonlineClient, StationInfo
from app.job_scheduler import JobSchedulerManager
from app.runtime_health import RuntimeHealth, start_health_server
from app.state_store import AlertStateStore, build_dedupe_key
from app.station_data_cache import StationDataCache


_log_level_name = os.getenv("LOG_LEVEL", "DEBUG").upper()
_log_level = getattr(logging, _log_level_name, logging.DEBUG)

logging.basicConfig(level=_log_level, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("hochwasser-alert")
MAIN_LOG_TAG = "[job=main]"


def _job_log_tag(job: AlertJob) -> str:
    return f"[job={job.job_uuid}:{job.name}]"


@dataclass(frozen=True)
class StationCycleData:
    station: StationInfo
    current: Measurement
    historical_points: list[Measurement]
    future_forecast: list[Measurement]
    horizon_hours: int


def _run_job_once(
    now: datetime,
    settings: Settings,
    job: AlertJob,
    client: PegelonlineClient,
    state_store: AlertStateStore,
    station_data_cache: StationDataCache[StationCycleData],
    zone: ZoneInfo,
) -> None:
    station_data = station_data_cache.get_or_fetch(
        now=now,
        station_uuid=job.station_uuid,
        forecast_series_shortname=settings.forecast_series_shortname,
        requester=_job_log_tag(job),
        fetcher=lambda: _load_station_cycle_data(now, client, settings, job),
    )

    station = station_data.station
    current = station_data.current
    historical_points = station_data.historical_points
    future_forecast = station_data.future_forecast
    horizon_hours = station_data.horizon_hours

    crossing = find_threshold_breach(
        now=now,
        current=current,
        forecast_points=future_forecast,
        limit_cm=job.limit_cm,
        horizon_hours=horizon_hours,
    )

    if crossing:
        logger.info(
            "%s Crossing prediction found: source=%s timestamp=%s value=%.1f",
            _job_log_tag(job),
            crossing.source,
            crossing.timestamp.isoformat(),
            crossing.value,
        )
    else:
        logger.info("%s No crossing prediction found in this cycle", _job_log_tag(job))

    logger.info(
        "%s Current %.1f %s, limit %.1f %s, crossing=%s",
        _job_log_tag(job),
        current.value,
        station.unit,
        job.limit_cm,
        station.unit,
        crossing.timestamp.isoformat() if crossing else "none",
    )

    if not crossing:
        return

    dedupe_key = build_dedupe_key(job.job_uuid, crossing.timestamp, job.recipients)

    subject, body, html_body = build_email(
        now,
        station,
        current,
        historical_points,
        future_forecast,
        crossing,
        job.limit_cm,
        job.locale,
        zone,
    )

    sent = state_store.run_if_due(
        key=dedupe_key,
        now=now,
        dedupe_hours=settings.dedupe_hours,
        action=lambda: send_alert_email(
            settings, job.recipients, subject, body, html_body
        ),
    )
    if not sent:
        return

    logger.info(
        "%s Alert email sent to %s",
        _job_log_tag(job),
        ", ".join(job.recipients),
    )


def _load_station_cycle_data(
    now: datetime,
    client: PegelonlineClient,
    settings: Settings,
    job: AlertJob,
) -> StationCycleData:
    station = client.get_station_info()
    current = client.get_current_measurement()
    recent_measurements = client.get_recent_measurements(start="PT24H")
    historical_points = [
        point for point in recent_measurements if point.timestamp < now
    ]

    horizon_hours = _forecast_horizon_hours_from_station(
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


def main() -> None:
    settings = load_settings()
    zone = ZoneInfo(settings.timezone)
    runtime_health = RuntimeHealth(
        started_at=datetime.now(tz=zone),
        failure_threshold=max(1, settings.health_failure_threshold),
    )
    start_health_server(settings.health_host, settings.health_port, runtime_health)

    state_store = AlertStateStore(settings.state_file)
    station_data_cache: StationDataCache[StationCycleData] = StationDataCache()
    job_scheduler = JobSchedulerManager(
        zone=zone,
        runtime_health=runtime_health,
        state_store=state_store,
        station_data_cache=station_data_cache,
        run_job_once=_run_job_once,
        initial_job_count=len(settings.jobs),
    )
    job_scheduler.start()

    logger.info(
        "%s Starting APScheduler monitor for %d job(s)",
        MAIN_LOG_TAG,
        len(settings.jobs),
    )
    runtime_health.mark_startup_complete()

    try:
        job_scheduler.reconcile(settings)

        while True:
            try:
                reloaded = load_settings()
            except Exception as exc:  # noqa: BLE001
                logger.exception("%s Reloading settings failed: %s", MAIN_LOG_TAG, exc)
                runtime_health.mark_manager_failure(
                    now=datetime.now(tz=zone), error=str(exc)
                )
            else:
                settings = reloaded
                job_scheduler.reconcile(settings)
                runtime_health.mark_manager_success(now=datetime.now(tz=zone))
            time.sleep(60)
    finally:
        job_scheduler.shutdown()


if __name__ == "__main__":
    main()
