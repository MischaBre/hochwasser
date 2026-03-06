from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from time import monotonic
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from fastapi import HTTPException, status

PEGELONLINE_BASE_URL = "https://pegelonline.wsv.de/webservices/rest-api/v2"
STATION_CACHE_TTL_SECONDS = 900
STATION_FETCH_TIMEOUT_SECONDS = 20


@dataclass(frozen=True)
class StationSummary:
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


@dataclass
class _StationCache:
    fetched_at_monotonic: float
    stations: tuple[StationSummary, ...]


_cache_lock = threading.Lock()
_station_cache: _StationCache | None = None


def list_stations(
    *,
    search: str,
    limit: int,
    offset: int,
    uuids: tuple[str, ...],
) -> tuple[StationSummary, ...]:
    stations = _get_cached_stations()

    if uuids:
        wanted = {candidate.strip() for candidate in uuids if candidate.strip()}
        if not wanted:
            return ()
        return tuple(station for station in stations if station.uuid in wanted)

    filtered = stations
    normalized_search = search.strip().lower()
    if normalized_search:
        filtered = tuple(
            station
            for station in stations
            if _station_matches_search(station, normalized_search)
        )

    return filtered[offset : offset + limit]


def _station_matches_search(station: StationSummary, query: str) -> bool:
    normalized_query = _normalize_search_text(query)
    if not normalized_query:
        return True

    query_tokens = normalized_query.split(" ")

    haystack = " ".join(
        (
            station.uuid,
            station.number,
            station.shortname,
            station.longname,
            station.agency,
            station.water_shortname,
            station.water_longname,
        )
    )
    normalized_haystack = _normalize_search_text(haystack)
    return all(token in normalized_haystack for token in query_tokens)


def _normalize_search_text(value: str) -> str:
    normalized_chars = [char if char.isalnum() else " " for char in value.casefold()]
    return " ".join("".join(normalized_chars).split())


def _get_cached_stations() -> tuple[StationSummary, ...]:
    global _station_cache

    now = monotonic()
    with _cache_lock:
        cache = _station_cache
        if (
            cache is not None
            and (now - cache.fetched_at_monotonic) < STATION_CACHE_TTL_SECONDS
        ):
            return cache.stations

        stations = _fetch_stations_from_pegelonline()
        _station_cache = _StationCache(fetched_at_monotonic=now, stations=stations)
        return stations


def _fetch_stations_from_pegelonline() -> tuple[StationSummary, ...]:
    query = urllib_parse.urlencode({"includeTimeseries": "false"})
    url = f"{PEGELONLINE_BASE_URL}/stations.json?{query}"

    try:
        with urllib_request.urlopen(
            url, timeout=STATION_FETCH_TIMEOUT_SECONDS
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib_error.URLError, TimeoutError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not load stations from Pegelonline: {exc}",
        ) from exc

    if not isinstance(payload, list):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Pegelonline returned an unexpected stations payload",
        )

    stations: list[StationSummary] = []
    for item in payload:
        if not isinstance(item, dict):
            continue

        station_uuid = str(item.get("uuid", "")).strip()
        if not station_uuid:
            continue

        water_data = item.get("water")
        water_shortname = ""
        water_longname = ""
        if isinstance(water_data, dict):
            shortname = water_data.get("shortname")
            longname = water_data.get("longname")
            water_shortname = str(shortname) if shortname is not None else ""
            water_longname = str(longname) if longname is not None else ""
        km = item.get("km")
        longitude = item.get("longitude")
        latitude = item.get("latitude")

        stations.append(
            StationSummary(
                uuid=station_uuid,
                number=str(item.get("number", "")),
                shortname=str(item.get("shortname", station_uuid)),
                longname=str(item.get("longname", item.get("shortname", station_uuid))),
                km=float(km) if isinstance(km, (int, float)) else None,
                agency=str(item.get("agency", "")),
                longitude=float(longitude)
                if isinstance(longitude, (int, float))
                else None,
                latitude=float(latitude)
                if isinstance(latitude, (int, float))
                else None,
                water_shortname=water_shortname,
                water_longname=water_longname,
            )
        )

    stations.sort(
        key=lambda station: (
            station.shortname.lower(),
            station.longname.lower(),
            station.uuid,
        )
    )
    return tuple(stations)
