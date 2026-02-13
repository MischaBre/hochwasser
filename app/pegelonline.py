from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


BASE_URL = "https://www.pegelonline.wsv.de/webservices/rest-api/v2"


@dataclass(frozen=True)
class Measurement:
    timestamp: datetime
    value: float


@dataclass(frozen=True)
class StationInfo:
    uuid: str
    shortname: str
    longname: str
    water_shortname: str
    water_longname: str
    unit: str


class PegelonlineClient:
    def __init__(self, station_uuid: str, timeout_seconds: int = 20) -> None:
        self.station_uuid = station_uuid
        self.timeout_seconds = timeout_seconds

    def _get_json(self, endpoint: str) -> Any:
        url = f"{BASE_URL}{endpoint}"
        try:
            with urlopen(url, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
        except URLError as exc:
            raise RuntimeError(f"Could not reach {url}: {exc}") from exc

    def get_station_info(self) -> StationInfo:
        payload = self._get_json(
            f"/stations/{self.station_uuid}.json?includeTimeseries=true"
        )
        unit = "cm"
        for series in payload.get("timeseries", []):
            if series.get("shortname") == "W":
                unit = series.get("unit", "cm")
                break

        water = payload.get("water", {})
        return StationInfo(
            uuid=payload["uuid"],
            shortname=payload.get("shortname", payload["uuid"]),
            longname=payload.get("longname", payload.get("shortname", payload["uuid"])),
            water_shortname=water.get("shortname", ""),
            water_longname=water.get("longname", ""),
            unit=unit,
        )

    def get_current_measurement(self) -> Measurement:
        payload = self._get_json(
            f"/stations/{self.station_uuid}/W/currentmeasurement.json"
        )
        return Measurement(
            timestamp=datetime.fromisoformat(payload["timestamp"]),
            value=float(payload["value"]),
        )

    def get_recent_measurements(self, start: str = "P2D") -> list[Measurement]:
        payload = self._get_json(
            f"/stations/{self.station_uuid}/W/measurements.json?start={start}"
        )
        measurements: list[Measurement] = []
        for item in payload:
            if item.get("value") is None or item.get("timestamp") is None:
                continue
            measurements.append(
                Measurement(
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                    value=float(item["value"]),
                )
            )
        return measurements

    def get_official_forecast(self) -> list[Measurement]:
        endpoints = (
            f"/stations/{self.station_uuid}/W/forecast.json",
            f"/stations/{self.station_uuid}/W/shorttermforecast.json",
            f"/stations/{self.station_uuid}/W/longtermforecast.json",
            f"/stations/{self.station_uuid}/W/predictions.json",
        )

        for endpoint in endpoints:
            try:
                payload = self._get_json(endpoint)
            except RuntimeError as exc:
                if "HTTP 404" in str(exc):
                    continue
                raise

            points = self._extract_measurements(payload)
            if points:
                return points

        return []

    def _extract_measurements(self, payload: Any) -> list[Measurement]:
        if isinstance(payload, list):
            return self._to_measurements(payload)

        if isinstance(payload, dict):
            for key in ("forecast", "predictions", "measurements", "values", "data"):
                if key in payload and isinstance(payload[key], list):
                    return self._to_measurements(payload[key])

        return []

    def _to_measurements(self, entries: list[dict[str, Any]]) -> list[Measurement]:
        out: list[Measurement] = []
        for item in entries:
            if not isinstance(item, dict):
                continue
            timestamp = item.get("timestamp")
            value = item.get("value")
            if timestamp is None or value is None:
                continue
            try:
                out.append(
                    Measurement(
                        timestamp=datetime.fromisoformat(str(timestamp)),
                        value=float(value),
                    )
                )
            except (TypeError, ValueError):
                continue
        return sorted(out, key=lambda m: m.timestamp)
