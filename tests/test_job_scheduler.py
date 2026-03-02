from datetime import datetime, timezone
from dataclasses import replace
from types import MethodType
from typing import Any, cast
from zoneinfo import ZoneInfo

from app.config import AlertJob, Settings
from app.job_scheduler import JobSchedulerManager, ManagedScheduledJob
from app.runtime_health import RuntimeHealth
from app.state_store import AlertStateStore
from app.station_data_cache import StationDataCache


class _FakeStateStore:
    def __init__(self) -> None:
        self.invalidate_calls: list[str] = []

    def invalidate_job_dedupe_keys(self, job_uuid: str) -> int:
        self.invalidate_calls.append(job_uuid)
        return 1


def _make_job(job_uuid: str, name: str) -> AlertJob:
    return AlertJob(
        job_uuid=job_uuid,
        name=name,
        station_uuid=f"station-{job_uuid}",
        limit_cm=100.0,
        recipients=("alerts@example.com",),
        alert_recipient="ops@example.com",
        locale="en",
        schedule_cron="*/15 * * * *",
        repeat_alerts_on_check=False,
    )


def _make_settings(jobs: tuple[AlertJob, ...]) -> Settings:
    return Settings(
        provider="pegelonline",
        database_url="postgresql://user:pass@localhost:5432/db",
        forecast_series_shortname="WV",
        dedupe_hours=24,
        timezone="UTC",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="",
        smtp_password="",
        smtp_sender="sender@example.com",
        smtp_use_starttls=True,
        smtp_use_ssl=False,
        admin_recipients=("admin@example.com",),
        health_host="0.0.0.0",
        health_port=8090,
        health_failure_threshold=1,
        jobs=jobs,
    )


def test_reconcile_continues_if_one_job_schedule_fails() -> None:
    zone = ZoneInfo("UTC")
    runtime_health = RuntimeHealth(
        started_at=datetime(2026, 2, 24, 10, 0, tzinfo=timezone.utc),
        failure_threshold=1,
    )
    runtime_health.mark_startup_complete()
    state_store = AlertStateStore("postgresql://user:pass@localhost:5432/db")
    manager = JobSchedulerManager(
        zone=zone,
        runtime_health=runtime_health,
        state_store=state_store,
        station_data_cache=StationDataCache(),
        run_job_once=lambda **_: None,
        initial_job_count=2,
    )

    bad_job = _make_job("bad", "Bad Job")
    good_job = _make_job("good", "Good Job")
    settings = _make_settings((bad_job, good_job))

    def fake_schedule(
        self: JobSchedulerManager,
        settings: Settings,
        job: AlertJob,
        runtime_signature: tuple[tuple[str, object], ...],
        dedupe_signature: tuple[tuple[str, object], ...],
    ) -> ManagedScheduledJob:
        if job.job_uuid == "bad":
            raise RuntimeError("boom")
        return ManagedScheduledJob(
            job=job,
            scheduler_job_id=f"job-{job.job_uuid}",
            runtime_signature=runtime_signature,
            dedupe_signature=dedupe_signature,
        )

    manager._schedule_job = MethodType(fake_schedule, manager)

    manager.reconcile(settings)

    assert "good" in manager._managed_jobs
    assert "bad" not in manager._managed_jobs

    snapshot = runtime_health.snapshot()
    jobs_snapshot = cast(dict[str, dict[str, Any]], snapshot["jobs"])
    assert jobs_snapshot["good"]["status"] == "ok"
    assert jobs_snapshot["bad"]["status"] == "degraded"


def test_reconcile_unrelated_setting_change_does_not_invalidate_dedupe() -> None:
    zone = ZoneInfo("UTC")
    runtime_health = RuntimeHealth(
        started_at=datetime(2026, 2, 24, 10, 0, tzinfo=timezone.utc),
        failure_threshold=1,
    )
    runtime_health.mark_startup_complete()
    state_store = _FakeStateStore()
    manager = JobSchedulerManager(
        zone=zone,
        runtime_health=runtime_health,
        state_store=state_store,  # type: ignore[arg-type]
        station_data_cache=StationDataCache(),
        run_job_once=lambda **_: None,
        initial_job_count=1,
    )
    job = _make_job("job-a", "Job A")
    settings = _make_settings((job,))
    changed = replace(settings, smtp_host="smtp.changed.example.com")

    unscheduled: list[str] = []

    def fake_schedule(
        self: JobSchedulerManager,
        settings: Settings,
        job: AlertJob,
        runtime_signature: tuple[tuple[str, object], ...],
        dedupe_signature: tuple[tuple[str, object], ...],
    ) -> ManagedScheduledJob:
        return ManagedScheduledJob(
            job=job,
            scheduler_job_id=f"job-{job.job_uuid}",
            runtime_signature=runtime_signature,
            dedupe_signature=dedupe_signature,
        )

    def fake_unschedule(
        self: JobSchedulerManager, managed: ManagedScheduledJob
    ) -> None:
        unscheduled.append(managed.job.job_uuid)

    manager._schedule_job = MethodType(fake_schedule, manager)
    manager._unschedule_managed_job = MethodType(fake_unschedule, manager)

    manager.reconcile(settings)
    manager.reconcile(changed)

    assert unscheduled == ["job-a"]
    assert state_store.invalidate_calls == []


def test_reconcile_dedupe_change_invalidates_state() -> None:
    zone = ZoneInfo("UTC")
    runtime_health = RuntimeHealth(
        started_at=datetime(2026, 2, 24, 10, 0, tzinfo=timezone.utc),
        failure_threshold=1,
    )
    runtime_health.mark_startup_complete()
    state_store = _FakeStateStore()
    manager = JobSchedulerManager(
        zone=zone,
        runtime_health=runtime_health,
        state_store=state_store,  # type: ignore[arg-type]
        station_data_cache=StationDataCache(),
        run_job_once=lambda **_: None,
        initial_job_count=1,
    )
    job = _make_job("job-a", "Job A")
    changed_job = replace(job, limit_cm=120.0)
    settings = _make_settings((job,))
    changed = _make_settings((changed_job,))

    def fake_schedule(
        self: JobSchedulerManager,
        settings: Settings,
        job: AlertJob,
        runtime_signature: tuple[tuple[str, object], ...],
        dedupe_signature: tuple[tuple[str, object], ...],
    ) -> ManagedScheduledJob:
        return ManagedScheduledJob(
            job=job,
            scheduler_job_id=f"job-{job.job_uuid}",
            runtime_signature=runtime_signature,
            dedupe_signature=dedupe_signature,
        )

    manager._schedule_job = MethodType(fake_schedule, manager)
    manager._unschedule_managed_job = MethodType(lambda self, _managed: None, manager)

    manager.reconcile(settings)
    manager.reconcile(changed)

    assert state_store.invalidate_calls == ["job-a"]


def test_schedule_job_does_not_force_immediate_run() -> None:
    zone = ZoneInfo("UTC")
    runtime_health = RuntimeHealth(
        started_at=datetime(2026, 2, 24, 10, 0, tzinfo=timezone.utc),
        failure_threshold=1,
    )
    state_store = AlertStateStore("postgresql://user:pass@localhost:5432/db")
    manager = JobSchedulerManager(
        zone=zone,
        runtime_health=runtime_health,
        state_store=state_store,
        station_data_cache=StationDataCache(),
        run_job_once=lambda **_: None,
        initial_job_count=1,
    )
    job = _make_job("job-a", "Job A")
    settings = _make_settings((job,))

    captured_kwargs: dict[str, object] = {}

    def fake_add_job(*_args: object, **kwargs: object) -> None:
        captured_kwargs.update(kwargs)

    manager._scheduler.add_job = fake_add_job  # type: ignore[method-assign]

    runtime_signature = manager._runtime_settings_signature(settings)
    dedupe_signature = manager._dedupe_signature(settings, job)
    managed = manager._schedule_job(
        settings=settings,
        job=job,
        runtime_signature=runtime_signature,
        dedupe_signature=dedupe_signature,
    )

    assert managed.scheduler_job_id == "job-job-a"
    assert "next_run_time" not in captured_kwargs
