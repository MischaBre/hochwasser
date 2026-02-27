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
from app.job_scheduler import JobSchedulerManager
from app.outbox_dispatcher import run_outbox_dispatch_cycle
from app.pegelonline import Measurement, PegelonlineClient, StationInfo
from app.runtime_health import RuntimeHealth, start_health_server
from app.state_store import (
    AlertStateStore,
    STATE_CROSSING_ACTIVE,
    STATE_CROSSING_INCOMING,
    STATE_CROSSING_SOON_OVER,
    STATE_NO_CROSSING,
)
from app.station_data_cache import StationDataCache
from app.i18n import format_float, tr


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


@dataclass(frozen=True)
class LifecycleEvaluation:
    state: str
    crossing: Crossing | None
    predicted_crossing_at: datetime | None
    predicted_end_at: datetime | None
    predicted_peak_cm: float | None
    predicted_peak_at: datetime | None


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

    evaluation = _evaluate_lifecycle(
        now=now,
        current=current,
        forecast_points=future_forecast,
        limit_cm=job.limit_cm,
        horizon_hours=horizon_hours,
    )
    logger.info(
        "%s State=%s current=%.1f %s limit=%.1f %s predicted_crossing=%s predicted_end=%s predicted_peak=%s@%s",
        _job_log_tag(job),
        evaluation.state,
        current.value,
        station.unit,
        job.limit_cm,
        station.unit,
        (
            evaluation.predicted_crossing_at.isoformat()
            if evaluation.predicted_crossing_at
            else "none"
        ),
        evaluation.predicted_end_at.isoformat()
        if evaluation.predicted_end_at
        else "none",
        (
            f"{evaluation.predicted_peak_cm:.1f}"
            if evaluation.predicted_peak_cm is not None
            else "none"
        ),
        evaluation.predicted_peak_at.isoformat()
        if evaluation.predicted_peak_at
        else "none",
    )

    subject, body, html_body = _build_notification_payload(
        now=now,
        station=station,
        current=current,
        historical_points=historical_points,
        future_forecast=future_forecast,
        job=job,
        state=evaluation.state,
        crossing=evaluation.crossing,
        predicted_crossing_at=evaluation.predicted_crossing_at,
        predicted_end_at=evaluation.predicted_end_at,
        zone=zone,
    )

    result = state_store.apply_job_state(
        job_uuid=job.job_uuid,
        state=evaluation.state,
        now=now,
        predicted_crossing_at=evaluation.predicted_crossing_at,
        predicted_end_at=evaluation.predicted_end_at,
        predicted_peak_cm=evaluation.predicted_peak_cm,
        predicted_peak_at=evaluation.predicted_peak_at,
        repeat_active_on_check=job.repeat_alerts_on_check,
        recipients=job.recipients,
        subject=subject,
        body_text=body,
        body_html=html_body,
    )
    if result.notification_queued:
        logger.info(
            "%s Alert email queued for %s (state=%s transitioned=%s)",
            _job_log_tag(job),
            ", ".join(job.recipients),
            evaluation.state,
            result.transitioned,
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


def _evaluate_lifecycle(
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


def _build_notification_payload(
    now: datetime,
    station: StationInfo,
    current: Measurement,
    historical_points: list[Measurement],
    future_forecast: list[Measurement],
    job: AlertJob,
    state: str,
    crossing: Crossing | None,
    predicted_crossing_at: datetime | None,
    predicted_end_at: datetime | None,
    zone: ZoneInfo,
) -> tuple[str, str, str | None]:
    subject = tr(
        job.locale,
        "subject_state_update",
        station=station.shortname,
        state=tr(job.locale, f"state_{state}"),
        limit=format_float(job.limit_cm, job.locale),
        unit=station.unit,
    )

    if crossing is not None:
        _, body, html_body = build_email(
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
        body = (
            f"{tr(job.locale, 'label_alert_state')}: {tr(job.locale, f'state_{state}')}.\n"
            f"{body}"
        )
        return subject, body, html_body

    crossing_time = (
        predicted_crossing_at.astimezone(zone).isoformat()
        if predicted_crossing_at is not None
        else tr(job.locale, "message_not_available")
    )
    end_time = (
        predicted_end_at.astimezone(zone).isoformat()
        if predicted_end_at is not None
        else tr(job.locale, "message_not_available")
    )
    body = (
        f"{tr(job.locale, 'label_alert_state')}: {tr(job.locale, f'state_{state}')}\n"
        f"{tr(job.locale, 'label_station_uuid')}: {station.uuid}\n"
        f"{tr(job.locale, 'label_current_value')}: {format_float(current.value, job.locale)} {station.unit}\n"
        f"{tr(job.locale, 'label_threshold')}: {format_float(job.limit_cm, job.locale)} {station.unit}\n"
        f"{tr(job.locale, 'label_predicted_crossing')}: {crossing_time}\n"
        f"{tr(job.locale, 'label_predicted_end')}: {end_time}\n"
    )
    return subject, body, None


def main() -> None:
    settings = load_settings()
    zone = ZoneInfo(settings.timezone)
    runtime_health = RuntimeHealth(
        started_at=datetime.now(tz=zone),
        failure_threshold=max(1, settings.health_failure_threshold),
    )
    start_health_server(settings.health_host, settings.health_port, runtime_health)

    state_store = AlertStateStore(settings.database_url)
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
                manager_failed = False
                dispatch = run_outbox_dispatch_cycle(
                    database_url=settings.database_url,
                    settings=settings,
                    now=datetime.now(tz=zone),
                )
                if dispatch.smtp_available:
                    if dispatch.sent or dispatch.failed:
                        logger.info(
                            "%s Outbox dispatch sent=%d failed=%d queued_due=%d",
                            MAIN_LOG_TAG,
                            dispatch.sent,
                            dispatch.failed,
                            dispatch.queued_due,
                        )
                    if dispatch.failed > 0:
                        manager_failed = True
                        runtime_health.mark_manager_failure(
                            now=datetime.now(tz=zone),
                            error=f"outbox dispatch failed count={dispatch.failed}",
                        )
                elif dispatch.queued_due > 0:
                    manager_failed = True
                    runtime_health.mark_manager_failure(
                        now=datetime.now(tz=zone),
                        error=f"smtp unavailable: {dispatch.smtp_error}",
                    )
                    logger.warning(
                        "%s SMTP unavailable with %d queued email(s): %s",
                        MAIN_LOG_TAG,
                        dispatch.queued_due,
                        dispatch.smtp_error,
                    )
                if not manager_failed:
                    runtime_health.mark_manager_success(now=datetime.now(tz=zone))
            time.sleep(60)
    finally:
        job_scheduler.shutdown()


if __name__ == "__main__":
    main()
