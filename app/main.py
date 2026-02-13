from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import Settings, load_settings
from app.notifier import send_alert_email
from app.pegelonline import Measurement, PegelonlineClient, StationInfo


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("hochwasser-alert")


@dataclass(frozen=True)
class Crossing:
    timestamp: datetime
    value: float
    source: str


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


def extrapolate_crossing(
    recent_points: list[Measurement],
    current: Measurement,
    limit_cm: float,
    horizon_hours: int,
    rising_points: int,
    min_slope_cm_per_hour: float,
) -> Crossing | None:
    if current.value >= limit_cm:
        return Crossing(
            timestamp=current.timestamp, value=current.value, source="current"
        )

    points = recent_points[-rising_points:]
    if len(points) < 2:
        return None

    start = points[0]
    end = points[-1]
    delta_hours = (end.timestamp - start.timestamp).total_seconds() / 3600
    if delta_hours <= 0:
        return None

    slope = (end.value - start.value) / delta_hours
    if slope < min_slope_cm_per_hour:
        return None

    hours_until_limit = (limit_cm - current.value) / slope
    if hours_until_limit < 0 or hours_until_limit > horizon_hours:
        return None

    predicted_at = current.timestamp + timedelta(hours=hours_until_limit)
    return Crossing(timestamp=predicted_at, value=limit_cm, source="trend")


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
    crossing: Crossing,
    settings: Settings,
    zone: ZoneInfo,
) -> tuple[str, str]:
    current_local = current.timestamp.astimezone(zone)
    crossing_local = crossing.timestamp.astimezone(zone)

    subject = (
        f"[Hochwasser Alert] {station.shortname}: {settings.limit_cm:.1f} {station.unit} "
        f"wird erreicht"
    )

    body = (
        f"Station: {station.longname} ({station.shortname})\n"
        f"Gewaesser: {station.water_longname or station.water_shortname}\n"
        f"Station UUID: {station.uuid}\n\n"
        f"Grenzwert: {settings.limit_cm:.1f} {station.unit}\n"
        f"Aktueller Wert: {current.value:.1f} {station.unit} "
        f"(Stand {current_local:%Y-%m-%d %H:%M %Z})\n"
        f"Prognose (Quelle: {crossing.source}): "
        f"{crossing.value:.1f} {station.unit} am {crossing_local:%Y-%m-%d %H:%M %Z}\n\n"
        "Hinweis: Die Trend-Prognose ist eine lineare Naeherung aus den letzten Messpunkten, "
        "falls keine offizielle Vorhersage verfuegbar ist.\n"
    )
    return subject, body


def run_once(
    settings: Settings,
    client: PegelonlineClient,
    station: StationInfo,
    state: dict,
    zone: ZoneInfo,
) -> None:
    now = datetime.now(tz=zone)
    current = client.get_current_measurement()
    recent = client.get_recent_measurements(start="P2D")
    official_forecast = client.get_official_forecast()

    crossing = find_crossing_from_forecast(
        official_forecast,
        settings.limit_cm,
        settings.forecast_horizon_hours,
    )

    if crossing is None:
        crossing = extrapolate_crossing(
            recent_points=recent,
            current=current,
            limit_cm=settings.limit_cm,
            horizon_hours=settings.forecast_horizon_hours,
            rising_points=settings.rising_points,
            min_slope_cm_per_hour=settings.min_slope_cm_per_hour,
        )

    logger.info(
        "Current %.1f %s, limit %.1f %s, crossing=%s",
        current.value,
        station.unit,
        settings.limit_cm,
        station.unit,
        crossing.timestamp.isoformat() if crossing else "none",
    )

    if crossing and should_send_alert(settings, state, crossing, now):
        subject, body = build_email(station, current, crossing, settings, zone)
        send_alert_email(settings, subject, body)
        remember_sent(state, now)
        save_state(settings.state_file, state)
        logger.info("Alert email sent to %s", ", ".join(settings.alert_recipients))


def main() -> None:
    settings = load_settings()
    zone = ZoneInfo(settings.timezone)
    client = PegelonlineClient(settings.station_uuid)
    station = client.get_station_info()
    state = load_state(settings.state_file)

    logger.info(
        "Starting monitor for station %s (%s), limit %.1f %s, run hours %s",
        station.longname,
        settings.station_uuid,
        settings.limit_cm,
        station.unit,
        ",".join(str(h) for h in settings.forecast_run_hours),
    )

    while True:
        now = datetime.now(tz=zone)
        next_run = _next_run_at(now, settings.forecast_run_hours)
        sleep_seconds = max(0.0, (next_run - now).total_seconds())
        if sleep_seconds > 0:
            logger.info("Next forecast check at %s", next_run.isoformat())
            time.sleep(sleep_seconds)

        try:
            run_once(settings, client, station, state, zone)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Monitoring cycle failed: %s", exc)
        time.sleep(1)


def _next_run_at(now: datetime, run_hours: tuple[int, ...]) -> datetime:
    for hour in run_hours:
        candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if candidate >= now:
            return candidate

    first_hour = run_hours[0]
    tomorrow = now + timedelta(days=1)
    return tomorrow.replace(hour=first_hour, minute=0, second=0, microsecond=0)


if __name__ == "__main__":
    main()
