from datetime import datetime, timezone

from app.runtime_health import RuntimeHealth


def _new_health() -> RuntimeHealth:
    health = RuntimeHealth(
        started_at=datetime(2026, 2, 22, 10, 0, tzinfo=timezone.utc),
        failure_threshold=2,
    )
    health.mark_startup_complete()
    return health


def test_runtime_health_tracks_jobs_independently() -> None:
    health = _new_health()
    now = datetime(2026, 2, 22, 10, 5, tzinfo=timezone.utc)

    health.upsert_job("job-a", "Job A")
    health.upsert_job("job-b", "Job B")
    health.mark_job_failure("job-a", now=now, error="api timeout")
    health.mark_job_failure("job-a", now=now, error="api timeout")
    health.mark_job_success("job-b", now=now)

    snapshot = health.snapshot()

    assert snapshot["status"] == "degraded"
    assert snapshot["jobs"]["job-a"]["status"] == "degraded"
    assert snapshot["jobs"]["job-b"]["status"] == "ok"


def test_manager_success_does_not_clear_job_failure() -> None:
    health = _new_health()
    now = datetime(2026, 2, 22, 10, 10, tzinfo=timezone.utc)

    health.upsert_job("job-a", "Job A")
    health.mark_job_failure("job-a", now=now, error="smtp error")
    health.mark_job_failure("job-a", now=now, error="smtp error")
    health.mark_manager_success(now=now)

    snapshot = health.snapshot()

    assert snapshot["manager"]["status"] == "ok"
    assert snapshot["jobs"]["job-a"]["status"] == "degraded"
    assert snapshot["status"] == "degraded"


def test_removing_degraded_job_recovers_global_status() -> None:
    health = _new_health()
    now = datetime(2026, 2, 22, 10, 15, tzinfo=timezone.utc)

    health.mark_manager_success(now=now)
    health.upsert_job("job-a", "Job A")
    health.mark_job_failure("job-a", now=now, error="x")
    health.mark_job_failure("job-a", now=now, error="x")
    assert health.snapshot()["status"] == "degraded"

    health.remove_job("job-a")
    snapshot = health.snapshot()

    assert snapshot["status"] == "ok"
    assert "job-a" not in snapshot["jobs"]
