from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

logger = logging.getLogger("hochwasser-alert")


@dataclass
class JobRuntimeHealth:
    name: str
    last_success: datetime | None = None
    last_failure: datetime | None = None
    last_error: str | None = None
    consecutive_failures: int = 0


@dataclass
class RuntimeHealth:
    started_at: datetime
    failure_threshold: int
    manager_last_success: datetime | None = None
    manager_last_failure: datetime | None = None
    manager_last_error: str | None = None
    manager_consecutive_failures: int = 0
    jobs: dict[str, JobRuntimeHealth] = field(default_factory=dict)
    startup_complete: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def mark_startup_complete(self) -> None:
        with self._lock:
            self.startup_complete = True

    def mark_manager_success(self, now: datetime) -> None:
        with self._lock:
            self.manager_last_success = now
            self.manager_last_error = None
            self.manager_consecutive_failures = 0

    def mark_manager_failure(self, now: datetime, error: str) -> None:
        with self._lock:
            self.manager_last_failure = now
            self.manager_last_error = error
            self.manager_consecutive_failures += 1

    def upsert_job(self, job_uuid: str, job_name: str) -> None:
        with self._lock:
            existing = self.jobs.get(job_uuid)
            if existing is None:
                self.jobs[job_uuid] = JobRuntimeHealth(name=job_name)
                return
            existing.name = job_name

    def remove_job(self, job_uuid: str) -> None:
        with self._lock:
            self.jobs.pop(job_uuid, None)

    def mark_job_success(self, job_uuid: str, now: datetime) -> bool:
        with self._lock:
            job = self.jobs.get(job_uuid)
            if job is None:
                return False
            was_degraded = job.consecutive_failures >= self.failure_threshold
            job.last_success = now
            job.last_error = None
            job.consecutive_failures = 0
            return was_degraded

    def mark_job_failure(self, job_uuid: str, now: datetime, error: str) -> bool:
        with self._lock:
            job = self.jobs.get(job_uuid)
            if job is None:
                return False
            was_degraded = job.consecutive_failures >= self.failure_threshold
            job.last_failure = now
            job.last_error = error
            job.consecutive_failures += 1
            is_degraded = job.consecutive_failures >= self.failure_threshold
            return is_degraded and not was_degraded

    def _status_for_failures(self, consecutive_failures: int) -> str:
        return "ok" if consecutive_failures < self.failure_threshold else "degraded"

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            status = "starting"
            manager_status = "starting"
            jobs_snapshot: dict[str, dict[str, object]] = {}
            if self.startup_complete:
                manager_status = self._status_for_failures(
                    self.manager_consecutive_failures
                )
                status = manager_status
                for job_uuid, job in self.jobs.items():
                    job_status = self._status_for_failures(job.consecutive_failures)
                    if job_status == "degraded":
                        status = "degraded"
                    jobs_snapshot[job_uuid] = {
                        "name": job.name,
                        "status": job_status,
                        "consecutive_failures": job.consecutive_failures,
                        "last_success": (
                            job.last_success.isoformat() if job.last_success else None
                        ),
                        "last_failure": (
                            job.last_failure.isoformat() if job.last_failure else None
                        ),
                        "last_error": job.last_error,
                    }
            return {
                "status": status,
                "started_at": self.started_at.isoformat(),
                "startup_complete": self.startup_complete,
                "failure_threshold": self.failure_threshold,
                "manager": {
                    "status": manager_status,
                    "consecutive_failures": self.manager_consecutive_failures,
                    "last_success": (
                        self.manager_last_success.isoformat()
                        if self.manager_last_success
                        else None
                    ),
                    "last_failure": (
                        self.manager_last_failure.isoformat()
                        if self.manager_last_failure
                        else None
                    ),
                    "last_error": self.manager_last_error,
                },
                "jobs": jobs_snapshot,
            }


def start_health_server(host: str, port: int, runtime_health: RuntimeHealth) -> None:
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path != "/health":
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"not found")
                return

            snapshot = runtime_health.snapshot()
            is_healthy = snapshot["status"] == "ok"
            body = json.dumps(snapshot).encode("utf-8")

            self.send_response(200 if is_healthy else 503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer((host, port), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("Health endpoint listening on http://%s:%d/health", host, port)
