from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Generic, TypeVar


T = TypeVar("T")

logger = logging.getLogger("hochwasser-alert")


@dataclass
class _InFlight(Generic[T]):
    event: threading.Event = field(default_factory=threading.Event)
    result: T | None = None
    error: Exception | None = None


class StationDataCache(Generic[T]):
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cache: dict[tuple[str, str, int], T] = {}
        self._inflight: dict[tuple[str, str, int], _InFlight[T]] = {}

    @staticmethod
    def _minute_bucket(now: datetime) -> int:
        return int(now.timestamp() // 60)

    def get_or_fetch(
        self,
        *,
        now: datetime,
        station_uuid: str,
        forecast_series_shortname: str,
        requester: str,
        fetcher: Callable[[], T],
    ) -> T:
        bucket = self._minute_bucket(now)
        key = (station_uuid, forecast_series_shortname, bucket)

        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                logger.debug(
                    "%s [cache=hit] station=%s series=%s bucket=%d",
                    requester,
                    station_uuid,
                    forecast_series_shortname,
                    bucket,
                )
                return cached

            inflight = self._inflight.get(key)
            if inflight is not None:
                logger.debug(
                    "%s [cache=wait] station=%s series=%s bucket=%d",
                    requester,
                    station_uuid,
                    forecast_series_shortname,
                    bucket,
                )
                should_wait = True
            else:
                inflight = _InFlight[T]()
                self._inflight[key] = inflight
                logger.debug(
                    "%s [cache=miss] station=%s series=%s bucket=%d",
                    requester,
                    station_uuid,
                    forecast_series_shortname,
                    bucket,
                )
                should_wait = False

        if should_wait:
            inflight.event.wait()
            if inflight.error is not None:
                raise inflight.error
            return inflight.result  # type: ignore[return-value]

        try:
            result = fetcher()
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                inflight.error = exc
                inflight.event.set()
                self._inflight.pop(key, None)
            raise

        with self._lock:
            inflight.result = result
            self._cache[key] = result
            self._prune_cache_unlocked(current_bucket=bucket)
            inflight.event.set()
            self._inflight.pop(key, None)
        return result

    def _prune_cache_unlocked(self, current_bucket: int) -> None:
        keep_from = current_bucket - 1
        stale_keys = [key for key in self._cache if key[2] < keep_from]
        for key in stale_keys:
            self._cache.pop(key, None)
