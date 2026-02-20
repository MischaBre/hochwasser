from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import replace
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import AlertJob, Settings, load_settings
from app.email_content import build_email
from app.forecasting import (
    Crossing,
    _forecast_horizon_hours_from_station,
    filter_future_forecast_points,
    find_crossing_from_forecast,
    find_threshold_breach,
)
from app.notifier import send_alert_email
from app.pegelonline import Measurement, PegelonlineClient, StationInfo


_log_level_name = os.getenv("LOG_LEVEL", "DEBUG").upper()
_log_level = getattr(logging, _log_level_name, logging.DEBUG)

logging.basicConfig(level=_log_level, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("hochwasser-alert")


@dataclass
class RuntimeHealth:
    started_at: datetime
    failure_threshold: int
    last_success: datetime | None = None
    last_failure: datetime | None = None
    last_error: str | None = None
    consecutive_failures: int = 0
    startup_complete: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def mark_startup_complete(self) -> None:
        with self._lock:
            self.startup_complete = True

    def mark_success(self, now: datetime) -> None:
        with self._lock:
            self.last_success = now
            self.last_error = None
            self.consecutive_failures = 0

    def mark_failure(self, now: datetime, error: str) -> None:
        with self._lock:
            self.last_failure = now
            self.last_error = error
            self.consecutive_failures += 1

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            status = "starting"
            if self.startup_complete:
                status = (
                    "ok"
                    if self.consecutive_failures < self.failure_threshold
                    else "degraded"
                )
            return {
                "status": status,
                "started_at": self.started_at.isoformat(),
                "startup_complete": self.startup_complete,
                "failure_threshold": self.failure_threshold,
                "consecutive_failures": self.consecutive_failures,
                "last_success": (
                    self.last_success.isoformat() if self.last_success else None
                ),
                "last_failure": (
                    self.last_failure.isoformat() if self.last_failure else None
                ),
                "last_error": self.last_error,
            }


@dataclass(frozen=True)
class StationCycleData:
    station: StationInfo
    current: Measurement
    historical_points: list[Measurement]
    future_forecast: list[Measurement]
    horizon_hours: int


def _start_health_server(host: str, port: int, runtime_health: RuntimeHealth) -> None:
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


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"sent_keys": {}}
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
            if "sent_keys" not in data or not isinstance(data["sent_keys"], dict):
                data["sent_keys"] = {}
            return data
    except (json.JSONDecodeError, OSError):
        return {"sent_keys": {}}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(state, file, indent=2)


def should_send_alert(
    settings: Settings,
    state: dict,
    crossing: Crossing,
    now: datetime,
) -> bool:
    key = (
        f"{settings.station_uuid}|{settings.limit_cm}|"
        f"{crossing.timestamp.isoformat()}|{crossing.source}|"
        f"{','.join(sorted(settings.alert_recipients))}"
    )
    sent_at_raw = state["sent_keys"].get(key)
    if not sent_at_raw:
        state["_pending_key"] = key
        return True

    try:
        sent_at = datetime.fromisoformat(sent_at_raw)
    except ValueError:
        state["_pending_key"] = key
        return True

    if now - sent_at >= timedelta(hours=settings.dedupe_hours):
        state["_pending_key"] = key
        return True

    return False


def remember_sent(state: dict, now: datetime) -> None:
    pending = state.pop("_pending_key", None)
    if not pending:
        return
    state["sent_keys"][pending] = now.isoformat()

    if len(state["sent_keys"]) > 500:
        items = sorted(state["sent_keys"].items(), key=lambda kv: kv[1], reverse=True)
        state["sent_keys"] = dict(items[:500])


def run_once(
    settings: Settings,
    clients: dict[str, PegelonlineClient],
    state: dict,
    zone: ZoneInfo,
) -> None:
    now = datetime.now(tz=zone)
    logger.info("Starting monitoring cycle at %s", now.isoformat())

    station_cache: dict[str, StationCycleData] = {}
    failures: list[str] = []
    for job in settings.jobs:
        try:
            _run_job_once(now, settings, job, clients, station_cache, state, zone)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{job.name}: {exc}")
            logger.exception("Job '%s' failed: %s", job.name, exc)

    if failures:
        raise RuntimeError("; ".join(failures))


def _run_job_once(
    now: datetime,
    settings: Settings,
    job: AlertJob,
    clients: dict[str, PegelonlineClient],
    station_cache: dict[str, StationCycleData],
    state: dict,
    zone: ZoneInfo,
) -> None:
    client = clients.get(job.station_uuid)
    if client is None:
        client = PegelonlineClient(
            job.station_uuid,
            forecast_series_shortname=settings.forecast_series_shortname,
        )
        clients[job.station_uuid] = client

    job_settings = replace(
        settings,
        station_uuid=job.station_uuid,
        limit_cm=job.limit_cm,
        alert_recipients=job.recipients,
        locale=job.locale,
    )

    station_data = station_cache.get(job.station_uuid)
    if station_data is None:
        station_data = _load_station_cycle_data(now, client, job_settings)
        station_cache[job.station_uuid] = station_data
        logger.info(
            "Station '%s' data fetched once for this cycle",
            job.station_uuid,
        )
    else:
        logger.info(
            "Job '%s' reusing cached data for station '%s'",
            job.name,
            job.station_uuid,
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
        limit_cm=job_settings.limit_cm,
        horizon_hours=horizon_hours,
    )

    if crossing:
        logger.info(
            "Crossing prediction found: source=%s timestamp=%s value=%.1f",
            crossing.source,
            crossing.timestamp.isoformat(),
            crossing.value,
        )
    else:
        logger.info("No crossing prediction found in this cycle")

    logger.info(
        "Current %.1f %s, limit %.1f %s, crossing=%s",
        current.value,
        station.unit,
        job_settings.limit_cm,
        station.unit,
        crossing.timestamp.isoformat() if crossing else "none",
    )

    if crossing and should_send_alert(job_settings, state, crossing, now):
        subject, body, html_body = build_email(
            now,
            station,
            current,
            historical_points,
            future_forecast,
            crossing,
            job_settings,
            zone,
        )
        send_alert_email(job_settings, subject, body, html_body)
        remember_sent(state, now)
        save_state(job_settings.state_file, state)
        logger.info(
            "Job '%s' alert email sent to %s",
            job.name,
            ", ".join(job_settings.alert_recipients),
        )


def _load_station_cycle_data(
    now: datetime,
    client: PegelonlineClient,
    settings: Settings,
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
            "No active forecast timeseries '%s' in station metadata; evaluating current value only",
            settings.forecast_series_shortname,
        )

    future_forecast = filter_future_forecast_points(official_forecast, now)

    logger.info(
        "Fetched station data: station=%s current=%s %.1f history_count=%d forecast_count=%d future_forecast_count=%d horizon_hours=%d",
        settings.station_uuid,
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
    _start_health_server(settings.health_host, settings.health_port, runtime_health)

    unique_stations = sorted({job.station_uuid for job in settings.jobs})
    clients = {
        station_uuid: PegelonlineClient(
            station_uuid,
            forecast_series_shortname=settings.forecast_series_shortname,
        )
        for station_uuid in unique_stations
    }
    state = load_state(settings.state_file)

    logger.info(
        "Starting monitor for %d jobs on %d station(s), run hours %s, run_every_minute=%s",
        len(settings.jobs),
        len(unique_stations),
        ",".join(str(hour) for hour in settings.forecast_run_hours),
        settings.run_every_minute,
    )
    if settings.run_every_minute:
        logger.warning(
            "DEBUG mode active: DEBUG_RUN_EVERY_MINUTE=true (checks every minute)"
        )
    runtime_health.mark_startup_complete()

    while True:
        now = datetime.now(tz=zone)
        if settings.run_every_minute:
            next_run = _next_minute_run_at(now)
        else:
            next_run = _next_run_at(now, settings.forecast_run_hours)

        sleep_seconds = max(0.0, (next_run - now).total_seconds())
        if sleep_seconds > 0:
            logger.info("Next forecast check at %s", next_run.isoformat())
            time.sleep(sleep_seconds)

        try:
            run_once(settings, clients, state, zone)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Monitoring cycle failed: %s", exc)
            runtime_health.mark_failure(now=datetime.now(tz=zone), error=str(exc))
        else:
            runtime_health.mark_success(now=datetime.now(tz=zone))
        time.sleep(1)


def _next_run_at(now: datetime, run_hours: tuple[int, ...]) -> datetime:
    for hour in run_hours:
        candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if candidate >= now:
            return candidate

    first_hour = run_hours[0]
    tomorrow = now + timedelta(days=1)
    return tomorrow.replace(hour=first_hour, minute=0, second=0, microsecond=0)


def _next_minute_run_at(now: datetime) -> datetime:
    return (now + timedelta(minutes=1)).replace(second=0, microsecond=0)


if __name__ == "__main__":
    main()
