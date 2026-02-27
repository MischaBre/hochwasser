from datetime import datetime, timezone
from types import MethodType
from zoneinfo import ZoneInfo

from app.config import AlertJob, Settings
from app.job_scheduler import JobSchedulerManager, ManagedScheduledJob
from app.runtime_health import RuntimeHealth
from app.state_store import AlertStateStore
from app.station_data_cache import StationDataCache


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
        settings_signature: tuple[tuple[str, object], ...],
    ) -> ManagedScheduledJob:
        if job.job_uuid == "bad":
            raise RuntimeError("boom")
        return ManagedScheduledJob(
            job=job,
            scheduler_job_id=f"job-{job.job_uuid}",
            settings_signature=settings_signature,
        )

    manager._schedule_job = MethodType(fake_schedule, manager)

    manager.reconcile(settings)

    assert "good" in manager._managed_jobs
    assert "bad" not in manager._managed_jobs

    snapshot = runtime_health.snapshot()
    assert snapshot["jobs"]["good"]["status"] == "ok"
    assert snapshot["jobs"]["bad"]["status"] == "degraded"
