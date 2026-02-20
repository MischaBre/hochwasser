from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


BASE_URL = "https://pegelonline.wsv.de/webservices/rest-api/v2"

logger = logging.getLogger("hochwasser-alert.pegelonline")


@dataclass(frozen=True)
class Measurement:
    timestamp: datetime
    value: float


@dataclass(frozen=True)
class StationInfo:
    uuid: str
    number: str
    shortname: str
    longname: str
    km: float | None
    agency: str
    longitude: float | None
    latitude: float | None
    water_shortname: str
    water_longname: str
    unit: str
    timeseries: tuple[dict[str, Any], ...]


class PegelonlineClient:
    def __init__(
        self,
        station_uuid: str,
        timeout_seconds: int = 20,
        forecast_series_shortname: str = "WV",
    ) -> None:
        self.station_uuid = station_uuid
        self.timeout_seconds = timeout_seconds
        self.forecast_series_shortname = forecast_series_shortname

    def _get_json(self, endpoint: str) -> Any:
        url = f"{BASE_URL}{endpoint}"
        logger.info("Fetching Pegelonline data: %s", url)
        try:
            with urlopen(url, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
                logger.info("Fetched Pegelonline response successfully: %s", url)
                return data
        except HTTPError as exc:
            raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
        except URLError as exc:
            raise RuntimeError(f"Could not reach {url}: {exc}") from exc

    def get_station_info(self) -> StationInfo:
        payload = self._get_json(
            f"/stations/{self.station_uuid}.json?includeTimeseries=true&includeForecastTimeseries=true"
        )
        unit = "cm"
        for series in payload.get("timeseries", []):
            if series.get("shortname") == "W":
                unit = series.get("unit", "cm")
                break
        else:
            for series in payload.get("timeseries", []):
                if series.get("shortname") == self.forecast_series_shortname:
                    unit = series.get("unit", "cm")
                    break

        water = payload.get("water", {})
        return StationInfo(
            uuid=payload["uuid"],
            number=str(payload.get("number", "")),
            shortname=payload.get("shortname", payload["uuid"]),
            longname=payload.get("longname", payload.get("shortname", payload["uuid"])),
            km=payload.get("km"),
            agency=payload.get("agency", ""),
            longitude=payload.get("longitude"),
            latitude=payload.get("latitude"),
            water_shortname=water.get("shortname", ""),
            water_longname=water.get("longname", ""),
            unit=unit,
            timeseries=tuple(payload.get("timeseries", [])),
        )

    def get_current_measurement(self) -> Measurement:
        payload = self._get_json(
            f"/stations/{self.station_uuid}/W/currentmeasurement.json"
        )
        measurement = Measurement(
            timestamp=datetime.fromisoformat(payload["timestamp"]),
            value=float(payload["value"]),
        )
        logger.info(
            "Current measurement returned: %s %.1f",
            measurement.timestamp.isoformat(),
            measurement.value,
        )
        return measurement

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
        logger.info("Recent measurements returned (%d points)", len(measurements))
        logger.debug(
            "Recent measurements detail: %s",
            [
                {"timestamp": m.timestamp.isoformat(), "value": m.value}
                for m in measurements
            ],
        )
        return measurements

    def get_official_forecast(self) -> list[Measurement]:
        primary_endpoint = f"/stations/{self.station_uuid}/{self.forecast_series_shortname}/measurements.json"
        try:
            payload = self._get_json(primary_endpoint)
            points = self._extract_measurements(payload)
            if points:
                logger.info(
                    "Official forecast returned from %s (%d points)",
                    primary_endpoint,
                    len(points),
                )
                logger.debug(
                    "Official forecast detail: %s",
                    [
                        {"timestamp": p.timestamp.isoformat(), "value": p.value}
                        for p in points
                    ],
                )
                return points
        except RuntimeError as exc:
            if "HTTP 404" in str(exc):
                logger.info(
                    "No official forecast available at %s (404). Using current value only.",
                    primary_endpoint,
                )
                return []
            raise

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
                logger.info(
                    "Official forecast returned from %s (%d points)",
                    endpoint,
                    len(points),
                )
                logger.debug(
                    "Official forecast detail: %s",
                    [
                        {"timestamp": p.timestamp.isoformat(), "value": p.value}
                        for p in points
                    ],
                )
                return points

        logger.info("No official forecast endpoint returned data")
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
