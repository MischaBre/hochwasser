from __future__ import annotations

import json
import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from html import escape
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import Settings, load_settings
from app.notifier import send_alert_email
from app.pegelonline import Measurement, PegelonlineClient, StationInfo


_log_level_name = os.getenv("LOG_LEVEL", "DEBUG").upper()
_log_level = getattr(logging, _log_level_name, logging.DEBUG)

logging.basicConfig(level=_log_level, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("hochwasser-alert")


@dataclass(frozen=True)
class Crossing:
    timestamp: datetime
    value: float
    source: str


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


def find_crossing_from_forecast(
    points: list[Measurement], limit_cm: float, horizon_hours: int
) -> Crossing | None:
    if not points:
        return None

    now = datetime.now(tz=points[0].timestamp.tzinfo)
    horizon = now + timedelta(hours=horizon_hours)

    for point in points:
        if point.timestamp < now:
            continue
        if point.timestamp > horizon:
            break
        if point.value >= limit_cm:
            return Crossing(
                timestamp=point.timestamp, value=point.value, source="official"
            )

    return None


def find_threshold_breach(
    now: datetime,
    current: Measurement,
    forecast_points: list[Measurement],
    limit_cm: float,
    horizon_hours: int,
) -> Crossing | None:
    if current.value >= limit_cm:
        return Crossing(timestamp=now, value=current.value, source="current")

    horizon = now + timedelta(hours=horizon_hours)
    for point in forecast_points:
        if point.timestamp < now:
            continue
        if point.timestamp > horizon:
            break
        if point.value >= limit_cm:
            return Crossing(
                timestamp=point.timestamp, value=point.value, source="official"
            )

    return None


def should_send_alert(
    settings: Settings, state: dict, crossing: Crossing, now: datetime
) -> bool:
    key = f"{settings.station_uuid}|{settings.limit_cm}|{crossing.timestamp.isoformat()}|{crossing.source}"
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


def build_email(
    station: StationInfo,
    current: Measurement,
    forecast_points: list[Measurement],
    crossing: Crossing,
    settings: Settings,
    zone: ZoneInfo,
) -> tuple[str, str, str]:
    current_local = current.timestamp.astimezone(zone)
    crossing_local = crossing.timestamp.astimezone(zone)
    max_forecast = _get_max_forecast_point(forecast_points)

    max_forecast_line = "Max forecast value: -"
    if max_forecast:
        max_ts_local = max_forecast.timestamp.astimezone(zone)
        max_forecast_line = (
            f"Max forecast value: {max_forecast.value:.1f} {station.unit} "
            f"(at {max_ts_local:%Y-%m-%d %H:%M %Z})"
        )

    subject = (
        f"[Hochwasser Alert] {station.shortname}: {settings.limit_cm:.1f} {station.unit} "
        f"wird erreicht"
    )

    body = (
        "Station information\n"
        "-------------------\n"
        f"Station UUID: {station.uuid}\n"
        f"Station number: {station.number or '-'}\n"
        f"Short name: {station.shortname}\n"
        f"Long name: {station.longname}\n"
        f"Agency: {station.agency or '-'}\n"
        f"Water body: {station.water_longname or station.water_shortname or '-'}\n"
        f"Water shortname: {station.water_shortname or '-'}\n"
        f"KM: {station.km if station.km is not None else '-'}\n"
        f"Longitude: {station.longitude if station.longitude is not None else '-'}\n"
        f"Latitude: {station.latitude if station.latitude is not None else '-'}\n"
        f"Timeseries: {', '.join(ts.get('shortname', '?') for ts in station.timeseries if isinstance(ts, dict)) or '-'}\n\n"
        "Alert context\n"
        "-------------\n"
        f"Threshold: {settings.limit_cm:.1f} {station.unit}\n"
        f"Current value: {current.value:.1f} {station.unit} "
        f"(at {current_local:%Y-%m-%d %H:%M %Z})\n"
        f"Trigger source: {crossing.source}\n"
        f"Trigger value: {crossing.value:.1f} {station.unit}\n"
        f"Trigger time: {crossing_local:%Y-%m-%d %H:%M %Z}\n\n"
        f"{max_forecast_line}\n\n"
        "Forecast data (fetched)\n"
        "-----------------------\n"
        f"{_format_forecast_table(forecast_points, settings.limit_cm, station.unit, zone)}\n"
    )

    html_body = _build_email_html(
        station,
        current,
        crossing,
        forecast_points,
        settings,
        zone,
        max_forecast_line,
    )
    return subject, body, html_body


def _get_max_forecast_point(forecast_points: list[Measurement]) -> Measurement | None:
    if not forecast_points:
        return None
    return max(forecast_points, key=lambda p: p.value)


def _build_email_html(
    station: StationInfo,
    current: Measurement,
    crossing: Crossing,
    forecast_points: list[Measurement],
    settings: Settings,
    zone: ZoneInfo,
    max_forecast_line: str,
) -> str:
    current_local = current.timestamp.astimezone(zone)
    crossing_local = crossing.timestamp.astimezone(zone)

    station_timeseries = (
        ", ".join(
            ts.get("shortname", "?")
            for ts in station.timeseries
            if isinstance(ts, dict)
        )
        or "-"
    )

    table_html = _format_forecast_table_html(
        forecast_points,
        settings.limit_cm,
        station.unit,
        zone,
    )

    return (
        "<html><body style='font-family:Arial,sans-serif;font-size:14px;color:#111'>"
        "<h3>Station information</h3>"
        f"<p>Station UUID: {escape(station.uuid)}<br>"
        f"Station number: {escape(station.number or '-')}<br>"
        f"Short name: {escape(station.shortname)}<br>"
        f"Long name: {escape(station.longname)}<br>"
        f"Agency: {escape(station.agency or '-')}<br>"
        f"Water body: {escape(station.water_longname or station.water_shortname or '-')}<br>"
        f"Water shortname: {escape(station.water_shortname or '-')}<br>"
        f"KM: {station.km if station.km is not None else '-'}<br>"
        f"Longitude: {station.longitude if station.longitude is not None else '-'}<br>"
        f"Latitude: {station.latitude if station.latitude is not None else '-'}<br>"
        f"Timeseries: {escape(station_timeseries)}</p>"
        "<h3>Alert context</h3>"
        f"<p>Threshold: {settings.limit_cm:.1f} {escape(station.unit)}<br>"
        f"Current value: {current.value:.1f} {escape(station.unit)} "
        f"(at {current_local:%Y-%m-%d %H:%M %Z})<br>"
        f"Trigger source: {escape(crossing.source)}<br>"
        f"Trigger value: {crossing.value:.1f} {escape(station.unit)}<br>"
        f"Trigger time: {crossing_local:%Y-%m-%d %H:%M %Z}<br>"
        f"{escape(max_forecast_line)}</p>"
        "<h3>Forecast data (fetched)</h3>"
        f"{table_html}"
        "</body></html>"
    )


def _format_forecast_table(
    forecast_points: list[Measurement],
    limit_cm: float,
    unit: str,
    zone: ZoneInfo,
) -> str:
    if not forecast_points:
        return "No forecast points returned by API."

    header = f"{'Timestamp':<20} | {'Value':>10} | {'Above limit':<11}"
    separator = "-" * len(header)
    rows = [header, separator]

    for point in forecast_points:
        local_ts = point.timestamp.astimezone(zone)
        is_above = "YES" if point.value >= limit_cm else "no"
        rows.append(
            f"{local_ts:%Y-%m-%d %H:%M} | {point.value:>7.1f} {unit:<2} | {is_above:<11}"
        )

    return "\n".join(rows)


def _format_forecast_table_html(
    forecast_points: list[Measurement],
    limit_cm: float,
    unit: str,
    zone: ZoneInfo,
) -> str:
    if not forecast_points:
        return "<p>No forecast points returned by API.</p>"

    rows = []
    for point in forecast_points:
        local_ts = point.timestamp.astimezone(zone)
        above = point.value >= limit_cm
        value_html = f"{point.value:.1f} {escape(unit)}"
        if above:
            value_html = f"<strong style='color:#b00020'>{value_html}</strong>"
        rows.append(
            "<tr>"
            f"<td style='padding:6px;border:1px solid #ddd'>{local_ts:%Y-%m-%d %H:%M}</td>"
            f"<td style='padding:6px;border:1px solid #ddd;text-align:right'>{value_html}</td>"
            f"<td style='padding:6px;border:1px solid #ddd'>{'YES' if above else 'no'}</td>"
            "</tr>"
        )

    return (
        "<table style='border-collapse:collapse'>"
        "<thead><tr>"
        "<th style='padding:6px;border:1px solid #ddd;text-align:left'>Timestamp</th>"
        "<th style='padding:6px;border:1px solid #ddd;text-align:left'>Value</th>"
        "<th style='padding:6px;border:1px solid #ddd;text-align:left'>Above limit</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )


def run_once(
    settings: Settings,
    client: PegelonlineClient,
    station: StationInfo,
    state: dict,
    zone: ZoneInfo,
) -> None:
    now = datetime.now(tz=zone)
    logger.info("Starting monitoring cycle at %s", now.isoformat())

    current = client.get_current_measurement()
    official_forecast = client.get_official_forecast()

    logger.info(
        "Fetched data: current=%s %.1f, forecast_count=%d",
        current.timestamp.isoformat(),
        current.value,
        len(official_forecast),
    )

    crossing = find_threshold_breach(
        now=now,
        current=current,
        forecast_points=official_forecast,
        limit_cm=settings.limit_cm,
        horizon_hours=settings.forecast_horizon_hours,
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
        settings.limit_cm,
        station.unit,
        crossing.timestamp.isoformat() if crossing else "none",
    )

    if crossing and should_send_alert(settings, state, crossing, now):
        subject, body, html_body = build_email(
            station,
            current,
            official_forecast,
            crossing,
            settings,
            zone,
        )
        send_alert_email(settings, subject, body, html_body)
        remember_sent(state, now)
        save_state(settings.state_file, state)
        logger.info("Alert email sent to %s", ", ".join(settings.alert_recipients))


def main() -> None:
    settings = load_settings()
    zone = ZoneInfo(settings.timezone)
    runtime_health = RuntimeHealth(
        started_at=datetime.now(tz=zone),
        failure_threshold=max(1, settings.health_failure_threshold),
    )
    _start_health_server(settings.health_host, settings.health_port, runtime_health)

    client = PegelonlineClient(
        settings.station_uuid,
        forecast_series_shortname=settings.forecast_series_shortname,
    )
    station = client.get_station_info()
    state = load_state(settings.state_file)

    logger.info(
        "Starting monitor for station %s (%s), limit %.1f %s, run hours %s, run_every_minute=%s",
        station.longname,
        settings.station_uuid,
        settings.limit_cm,
        station.unit,
        ",".join(str(h) for h in settings.forecast_run_hours),
        settings.run_every_minute,
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
            run_once(settings, client, station, state, zone)
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
