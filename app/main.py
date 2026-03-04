from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import AlertJob, Settings, load_settings
from app.email_content import build_notification_payload
from app.forecasting import evaluate_lifecycle
from app.job_scheduler import JobSchedulerManager
from app.outbox_dispatcher import run_outbox_dispatch_cycle
from app.provider_client import WaterLevelProviderClient
from app.runtime_health import RuntimeHealth, start_health_server
from app.state_store import AlertStateStore
from app.station_data_cache import StationDataCache
from app.station_cycle_data import StationCycleData, load_station_cycle_data


_log_level_name = os.getenv("LOG_LEVEL", "DEBUG").upper()
_log_level = getattr(logging, _log_level_name, logging.DEBUG)

logging.basicConfig(level=_log_level, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("hochwasser-alert")
MAIN_LOG_TAG = "[job=main]"


def _job_log_tag(job: AlertJob) -> str:
    return f"[job={job.job_uuid}:{job.name}]"


def _run_job_once(
    now: datetime,
    settings: Settings,
    job: AlertJob,
    client: WaterLevelProviderClient,
    state_store: AlertStateStore,
    station_data_cache: StationDataCache[StationCycleData],
    zone: ZoneInfo,
) -> None:
    station_data = station_data_cache.get_or_fetch(
        now=now,
        station_uuid=job.station_uuid,
        forecast_series_shortname=settings.forecast_series_shortname,
        requester=_job_log_tag(job),
        fetcher=lambda: load_station_cycle_data(now, client, settings, job),
    )

    station = station_data.station
    current = station_data.current
    historical_points = station_data.historical_points
    future_forecast = station_data.future_forecast
    horizon_hours = station_data.horizon_hours

    evaluation = evaluate_lifecycle(
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

    subject, body, html_body = build_notification_payload(
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
