from datetime import datetime, timezone
from pathlib import Path
import threading
import time

from app.state_store import AlertStateStore


def test_run_if_due_does_not_block_other_keys(tmp_path: Path) -> None:
    store = AlertStateStore(tmp_path / "state.json")
    now = datetime(2026, 2, 24, 10, 0, tzinfo=timezone.utc)

    entered_action = threading.Event()
    release_action = threading.Event()
    first_result: list[bool] = []

    def first_action() -> None:
        entered_action.set()
        release_action.wait(timeout=2)

    def run_first() -> None:
        first_result.append(
            store.run_if_due(
                key="job-a|k1",
                now=now,
                dedupe_hours=24,
                action=first_action,
            )
        )

    thread = threading.Thread(target=run_first)
    thread.start()
    assert entered_action.wait(timeout=1)

    start = time.perf_counter()
    second_result = store.run_if_due(
        key="job-b|k2",
        now=now,
        dedupe_hours=24,
        action=lambda: None,
    )
    elapsed = time.perf_counter() - start

    release_action.set()
    thread.join(timeout=1)

    assert first_result == [True]
    assert second_result is True
    assert elapsed < 0.2


def test_run_if_due_executes_action_once_per_key_race(tmp_path: Path) -> None:
    store = AlertStateStore(tmp_path / "state.json")
    now = datetime(2026, 2, 24, 10, 0, tzinfo=timezone.utc)

    action_runs = 0
    action_lock = threading.Lock()
    start_gate = threading.Barrier(2)
    results: list[bool] = []
    results_lock = threading.Lock()

    def action() -> None:
        nonlocal action_runs
        with action_lock:
            action_runs += 1
        time.sleep(0.05)

    def worker() -> None:
        start_gate.wait(timeout=1)
        result = store.run_if_due(
            key="job-a|shared",
            now=now,
            dedupe_hours=24,
            action=action,
        )
        with results_lock:
            results.append(result)

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    t2.start()
    t1.join(timeout=2)
    t2.join(timeout=2)

    assert action_runs == 1
    assert sorted(results) == [False, True]
