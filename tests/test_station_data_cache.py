from datetime import datetime, timezone
import threading
import time

from app.station_data_cache import StationDataCache


def test_same_key_fetches_once_for_concurrent_callers() -> None:
    cache: StationDataCache[str] = StationDataCache()
    now = datetime(2026, 2, 24, 10, 1, tzinfo=timezone.utc)
    runs = 0
    runs_lock = threading.Lock()

    def fetcher() -> str:
        nonlocal runs
        with runs_lock:
            runs += 1
        time.sleep(0.05)
        return "payload"

    results: list[str] = []
    results_lock = threading.Lock()
    start_gate = threading.Barrier(2)

    def worker() -> None:
        start_gate.wait(timeout=1)
        result = cache.get_or_fetch(
            now=now,
            station_uuid="station-a",
            forecast_series_shortname="WV",
            requester="[job=t]",
            fetcher=fetcher,
        )
        with results_lock:
            results.append(result)

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    t1.join(timeout=2)
    t2.join(timeout=2)

    assert runs == 1
    assert results == ["payload", "payload"]


def test_different_keys_fetch_independently() -> None:
    cache: StationDataCache[str] = StationDataCache()
    now = datetime(2026, 2, 24, 10, 2, tzinfo=timezone.utc)

    started_a = threading.Event()
    started_b = threading.Event()
    release = threading.Event()

    def fetch_a() -> str:
        started_a.set()
        release.wait(timeout=2)
        return "a"

    def fetch_b() -> str:
        started_b.set()
        release.wait(timeout=2)
        return "b"

    out: list[str] = []
    out_lock = threading.Lock()

    def worker(station_uuid: str, fetcher) -> None:  # type: ignore[no-untyped-def]
        result = cache.get_or_fetch(
            now=now,
            station_uuid=station_uuid,
            forecast_series_shortname="WV",
            requester=f"[job={station_uuid}]",
            fetcher=fetcher,
        )
        with out_lock:
            out.append(result)

    t1 = threading.Thread(target=worker, args=("station-a", fetch_a))
    t2 = threading.Thread(target=worker, args=("station-b", fetch_b))
    t1.start()
    t2.start()

    assert started_a.wait(timeout=1)
    assert started_b.wait(timeout=1)

    release.set()
    t1.join(timeout=2)
    t2.join(timeout=2)

    assert sorted(out) == ["a", "b"]
