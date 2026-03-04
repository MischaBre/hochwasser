from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


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
