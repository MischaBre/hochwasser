from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from zoneinfo import ZoneInfo

from apscheduler.executors.pool import (
    ThreadPoolExecutor as APSchedulerThreadPoolExecutor,
)
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import AlertJob, Settings
from app.notifier import send_alert_email
from app.pegelonline import PegelonlineClient
from app.runtime_health import RuntimeHealth
from app.state_store import AlertStateStore
from app.station_data_cache import StationDataCache


JobRunner = Callable[..., None]


def _job_log_tag(job: AlertJob) -> str:
    return f"[job={job.job_uuid}:{job.name}]"


@dataclass
class ManagedScheduledJob:
    job: AlertJob
    scheduler_job_id: str
    settings_signature: tuple[tuple[str, object], ...]


class JobSchedulerManager:
    def __init__(
        self,
        zone: ZoneInfo,
        runtime_health: RuntimeHealth,
        state_store: AlertStateStore,
        station_data_cache: StationDataCache,
        run_job_once: JobRunner,
        initial_job_count: int,
    ) -> None:
        self._zone = zone
        self._runtime_health = runtime_health
        self._state_store = state_store
        self._station_data_cache = station_data_cache
        self._run_job_once = run_job_once
        self._logger = logging.getLogger("hochwasser-alert")
        self._managed_jobs: dict[str, ManagedScheduledJob] = {}
        self._scheduler = BackgroundScheduler(
            timezone=zone,
            executors={
                "default": APSchedulerThreadPoolExecutor(
                    max_workers=max(4, initial_job_count + 2)
                )
            },
            job_defaults={"coalesce": True},
        )

    def start(self) -> None:
        self._scheduler.start()

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)

    def reconcile(self, settings: Settings) -> None:
        desired_jobs = {job.job_uuid: job for job in settings.jobs}
        settings_signature = self._global_settings_signature(settings)

        removed_names = sorted(set(self._managed_jobs) - set(desired_jobs))
        for job_uuid in removed_names:
            removed = self._managed_jobs.pop(job_uuid)
            self._unschedule_managed_job(removed)
            self._runtime_health.remove_job(job_uuid)
            self._logger.info(
                "%s Stopped deleted job",
                _job_log_tag(removed.job),
            )

        for job_uuid, job in desired_jobs.items():
            existing = self._managed_jobs.get(job_uuid)
            if (
                existing
                and existing.job == job
                and existing.settings_signature == settings_signature
            ):
                continue
            if existing:
                invalidated = self._state_store.invalidate_job_dedupe_keys(job.job_uuid)
                self._unschedule_managed_job(existing)
                self._runtime_health.upsert_job(job.job_uuid, job.name)
                self._logger.info(
                    "%s Restarting updated job, invalidated %d dedupe key(s)",
                    _job_log_tag(job),
                    invalidated,
                )
            else:
                self._runtime_health.upsert_job(job.job_uuid, job.name)
                self._logger.info("%s Starting new job", _job_log_tag(job))
            self._managed_jobs[job_uuid] = self._schedule_job(
                settings=settings,
                job=job,
                settings_signature=settings_signature,
            )

    @staticmethod
    def _global_settings_signature(
        settings: Settings,
    ) -> tuple[tuple[str, object], ...]:
        excluded_keys = {"jobs"}
        return tuple(
            (key, value)
            for key, value in sorted(settings.__dict__.items())
            if key not in excluded_keys
        )

    def _schedule_job(
        self,
        settings: Settings,
        job: AlertJob,
        settings_signature: tuple[tuple[str, object], ...],
    ) -> ManagedScheduledJob:
        scheduler_job_id = f"job-{job.job_uuid}"
        client = PegelonlineClient(
            job.station_uuid,
            forecast_series_shortname=settings.forecast_series_shortname,
        )
        self._scheduler.add_job(
            self._execute_scheduled_job,
            trigger=CronTrigger.from_crontab(job.schedule_cron, timezone=self._zone),
            id=scheduler_job_id,
            replace_existing=True,
            next_run_time=datetime.now(tz=self._zone),
            max_instances=1,
            kwargs={
                "settings": settings,
                "job": job,
                "client": client,
            },
        )
        self._logger.info(
            "%s Scheduled with cron '%s'",
            _job_log_tag(job),
            job.schedule_cron,
        )
        return ManagedScheduledJob(
            job=job,
            scheduler_job_id=scheduler_job_id,
            settings_signature=settings_signature,
        )

    def _unschedule_managed_job(self, managed: ManagedScheduledJob) -> None:
        try:
            self._scheduler.remove_job(managed.scheduler_job_id)
        except JobLookupError:
            return

    def _execute_scheduled_job(
        self,
        settings: Settings,
        job: AlertJob,
        client: PegelonlineClient,
    ) -> None:
        now = datetime.now(tz=self._zone)
        try:
            self._run_job_once(
                now=now,
                settings=settings,
                job=job,
                client=client,
                state_store=self._state_store,
                station_data_cache=self._station_data_cache,
                zone=self._zone,
            )
        except Exception as exc:  # noqa: BLE001
            self._logger.exception("%s Cycle failed: %s", _job_log_tag(job), exc)
            became_degraded = self._runtime_health.mark_job_failure(
                job_uuid=job.job_uuid,
                now=datetime.now(tz=self._zone),
                error=str(exc),
            )
            if became_degraded:
                self._send_job_down_alert(settings=settings, job=job, error=str(exc))
        else:
            self._runtime_health.mark_job_success(
                job_uuid=job.job_uuid,
                now=datetime.now(tz=self._zone),
            )

    def _send_job_down_alert(
        self, settings: Settings, job: AlertJob, error: str
    ) -> None:
        recipients = tuple(
            dict.fromkeys((*settings.admin_recipients, job.alert_recipient))
        )
        subject = f"[DOWN] Job {job.name} ({job.job_uuid}) degraded"
        body = (
            "A job crossed the configured health failure threshold.\n\n"
            f"Job UUID: {job.job_uuid}\n"
            f"Job name: {job.name}\n"
            f"Station UUID: {job.station_uuid}\n"
            f"Schedule: {job.schedule_cron}\n"
            f"Failure threshold: {self._runtime_health.failure_threshold}\n"
            f"Last error: {error}\n"
        )
        try:
            send_alert_email(
                settings=settings,
                recipients=recipients,
                subject=subject,
                body=body,
            )
        except Exception as alert_exc:  # noqa: BLE001
            self._logger.exception(
                "%s Sending down alert failed: %s",
                _job_log_tag(job),
                alert_exc,
            )
