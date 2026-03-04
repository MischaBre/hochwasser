from __future__ import annotations

from typing import Protocol

from app.waterlevel_models import Measurement, StationInfo


class WaterLevelProviderClient(Protocol):
    def get_station_info(self) -> StationInfo: ...

    def get_current_measurement(self) -> Measurement: ...

    def get_recent_measurements(self, start: str = "P2D") -> list[Measurement]: ...

    def get_official_forecast(self) -> list[Measurement]: ...


def create_provider_client(
    provider: str,
    station_uuid: str,
    timeout_seconds: int = 20,
    forecast_series_shortname: str = "WV",
) -> WaterLevelProviderClient:
    normalized = provider.strip().lower()
    if normalized == "pegelonline":
        from app.pegelonline import PegelonlineClient

        return PegelonlineClient(
            station_uuid=station_uuid,
            timeout_seconds=timeout_seconds,
            forecast_series_shortname=forecast_series_shortname,
        )

    raise ValueError(f"Unsupported provider: {provider}")
