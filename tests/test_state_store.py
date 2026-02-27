from datetime import datetime, timezone

import pytest

from app.state_store import (
    AlertStateStore,
    STATE_CROSSING_ACTIVE,
    STATE_CROSSING_INCOMING,
    STATE_CROSSING_SOON_OVER,
)


class _FakeDb:
    def __init__(self) -> None:
        self.runtime: dict[str, dict[str, object]] = {}
        self.outbox: list[dict[str, object]] = []


class _FakeCursor:
    def __init__(self, db: _FakeDb) -> None:
        self._db = db
        self._last_row: tuple[object, ...] | None = None
        self._rows: list[tuple[object, ...]] = []

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, query: str, params: tuple[object, ...]) -> None:
        if "SELECT pg_advisory_xact_lock" in query:
            return

        if "FROM public.alert_job_runtime_state" in query and "FOR UPDATE" in query:
            job_uuid = str(params[0])
            row = self._db.runtime.get(job_uuid)
            self._last_row = (
                None
                if row is None
                else (
                    row["state"],
                    row["state_since"],
                    row.get("last_notified_state"),
                    row.get("last_notified_predicted_crossing_at"),
                    row.get("last_notified_predicted_end_at"),
                    row.get("last_notified_peak_cm"),
                    row.get("last_notified_peak_at"),
                )
            )
            return

        if "INSERT INTO public.alert_job_runtime_state" in query:
            (
                job_uuid,
                state,
                state_since,
                predicted_crossing_at,
                predicted_end_at,
                predicted_peak_cm,
                predicted_peak_at,
                updated_at,
            ) = params
            self._db.runtime[str(job_uuid)] = {
                "state": state,
                "state_since": state_since,
                "predicted_crossing_at": predicted_crossing_at,
                "predicted_end_at": predicted_end_at,
                "predicted_peak_cm": predicted_peak_cm,
                "predicted_peak_at": predicted_peak_at,
                "updated_at": updated_at,
            }
            return

        if "INSERT INTO public.email_outbox" in query:
            (
                job_uuid,
                target_state,
                trigger_reason,
                state_since,
                predicted_crossing_at,
                predicted_end_at,
                predicted_peak_cm,
                predicted_peak_at,
                recipients,
                subject,
                body_text,
                body_html,
                next_attempt_at,
                created_at,
                updated_at,
            ) = params
            self._db.outbox.append(
                {
                    "job_uuid": job_uuid,
                    "target_state": target_state,
                    "trigger_reason": trigger_reason,
                    "state_since": state_since,
                    "predicted_crossing_at": predicted_crossing_at,
                    "predicted_end_at": predicted_end_at,
                    "predicted_peak_cm": predicted_peak_cm,
                    "predicted_peak_at": predicted_peak_at,
                    "recipients": recipients,
                    "subject": subject,
                    "body_text": body_text,
                    "body_html": body_html,
                    "next_attempt_at": next_attempt_at,
                    "created_at": created_at,
                    "updated_at": updated_at,
                }
            )
            return

        if "DELETE FROM public.alert_job_runtime_state" in query:
            job_uuid = str(params[0])
            removed = self._db.runtime.pop(job_uuid, None)
            self._rows = [] if removed is None else [(job_uuid,)]

    def fetchone(self) -> tuple[object, ...] | None:
        return self._last_row

    def fetchall(self) -> list[tuple[object, ...]]:
        return self._rows


class _FakeTransaction:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *_args: object) -> None:
        return None


class _FakeConnection:
    def __init__(self, db: _FakeDb) -> None:
        self._db = db

    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def transaction(self) -> _FakeTransaction:
        return _FakeTransaction()

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self._db)


def test_apply_job_state_queues_on_transition() -> None:
    fake_db = _FakeDb()
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "app.state_store.psycopg.connect",
        lambda _database_url: _FakeConnection(fake_db),
    )

    store = AlertStateStore("postgresql://user:pass@localhost:5432/db")
    now = datetime(2026, 2, 24, 10, 0, tzinfo=timezone.utc)

    first = store.apply_job_state(
        job_uuid="job-a",
        state=STATE_CROSSING_INCOMING,
        now=now,
        predicted_crossing_at=now,
        predicted_end_at=None,
        predicted_peak_cm=110.0,
        predicted_peak_at=now,
        repeat_active_on_check=False,
        recipients=("a@example.com",),
        subject="subject",
        body_text="body",
        body_html=None,
    )
    second = store.apply_job_state(
        job_uuid="job-a",
        state=STATE_CROSSING_INCOMING,
        now=now,
        predicted_crossing_at=now,
        predicted_end_at=None,
        predicted_peak_cm=110.0,
        predicted_peak_at=now,
        repeat_active_on_check=False,
        recipients=("a@example.com",),
        subject="subject",
        body_text="body",
        body_html=None,
    )

    assert first.transitioned is True
    assert first.notification_queued is True
    assert second.transitioned is False
    assert second.notification_queued is False
    assert len(fake_db.outbox) == 1
    monkeypatch.undo()


def test_apply_job_state_repeat_active_queues_each_cycle() -> None:
    fake_db = _FakeDb()
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "app.state_store.psycopg.connect",
        lambda _database_url: _FakeConnection(fake_db),
    )

    store = AlertStateStore("postgresql://user:pass@localhost:5432/db")
    now = datetime(2026, 2, 24, 10, 0, tzinfo=timezone.utc)

    store.apply_job_state(
        job_uuid="job-a",
        state=STATE_CROSSING_ACTIVE,
        now=now,
        predicted_crossing_at=now,
        predicted_end_at=None,
        predicted_peak_cm=110.0,
        predicted_peak_at=now,
        repeat_active_on_check=True,
        recipients=("a@example.com",),
        subject="subject",
        body_text="body",
        body_html=None,
    )
    result = store.apply_job_state(
        job_uuid="job-a",
        state=STATE_CROSSING_ACTIVE,
        now=now,
        predicted_crossing_at=now,
        predicted_end_at=None,
        predicted_peak_cm=110.0,
        predicted_peak_at=now,
        repeat_active_on_check=True,
        recipients=("a@example.com",),
        subject="subject",
        body_text="body",
        body_html=None,
    )

    assert result.transitioned is False
    assert result.notification_queued is True
    assert result.notification_reason == "repeat"
    assert len(fake_db.outbox) == 2
    monkeypatch.undo()


def test_apply_job_state_incoming_worse_eta_queues_update() -> None:
    fake_db = _FakeDb()
    now = datetime(2026, 2, 24, 10, 0, tzinfo=timezone.utc)
    fake_db.runtime["job-a"] = {
        "state": STATE_CROSSING_INCOMING,
        "state_since": now,
        "last_notified_state": STATE_CROSSING_INCOMING,
        "last_notified_predicted_crossing_at": datetime(
            2026, 2, 24, 15, 0, tzinfo=timezone.utc
        ),
        "last_notified_peak_cm": 120.0,
    }
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "app.state_store.psycopg.connect",
        lambda _database_url: _FakeConnection(fake_db),
    )

    store = AlertStateStore("postgresql://user:pass@localhost:5432/db")
    result = store.apply_job_state(
        job_uuid="job-a",
        state=STATE_CROSSING_INCOMING,
        now=now,
        predicted_crossing_at=datetime(2026, 2, 24, 14, 0, tzinfo=timezone.utc),
        predicted_end_at=None,
        predicted_peak_cm=121.0,
        predicted_peak_at=now,
        repeat_active_on_check=False,
        recipients=("a@example.com",),
        subject="subject",
        body_text="body",
        body_html=None,
    )

    assert result.notification_queued is True
    assert result.notification_reason == "worse_eta"
    monkeypatch.undo()


def test_apply_job_state_active_worse_peak_queues_update() -> None:
    fake_db = _FakeDb()
    now = datetime(2026, 2, 24, 10, 0, tzinfo=timezone.utc)
    fake_db.runtime["job-a"] = {
        "state": STATE_CROSSING_ACTIVE,
        "state_since": now,
        "last_notified_state": STATE_CROSSING_ACTIVE,
        "last_notified_peak_cm": 120.0,
    }
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "app.state_store.psycopg.connect",
        lambda _database_url: _FakeConnection(fake_db),
    )

    store = AlertStateStore("postgresql://user:pass@localhost:5432/db")
    result = store.apply_job_state(
        job_uuid="job-a",
        state=STATE_CROSSING_ACTIVE,
        now=now,
        predicted_crossing_at=now,
        predicted_end_at=None,
        predicted_peak_cm=123.0,
        predicted_peak_at=now,
        repeat_active_on_check=False,
        recipients=("a@example.com",),
        subject="subject",
        body_text="body",
        body_html=None,
    )

    assert result.notification_queued is True
    assert result.notification_reason == "worse_peak"
    monkeypatch.undo()


def test_apply_job_state_soon_over_later_end_queues_update() -> None:
    fake_db = _FakeDb()
    now = datetime(2026, 2, 24, 10, 0, tzinfo=timezone.utc)
    fake_db.runtime["job-a"] = {
        "state": STATE_CROSSING_SOON_OVER,
        "state_since": now,
        "last_notified_state": STATE_CROSSING_SOON_OVER,
        "last_notified_predicted_end_at": datetime(
            2026, 2, 24, 14, 0, tzinfo=timezone.utc
        ),
    }
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "app.state_store.psycopg.connect",
        lambda _database_url: _FakeConnection(fake_db),
    )

    store = AlertStateStore("postgresql://user:pass@localhost:5432/db")
    result = store.apply_job_state(
        job_uuid="job-a",
        state=STATE_CROSSING_SOON_OVER,
        now=now,
        predicted_crossing_at=now,
        predicted_end_at=datetime(2026, 2, 24, 15, 0, tzinfo=timezone.utc),
        predicted_peak_cm=121.0,
        predicted_peak_at=now,
        repeat_active_on_check=False,
        recipients=("a@example.com",),
        subject="subject",
        body_text="body",
        body_html=None,
    )

    assert result.notification_queued is True
    assert result.notification_reason == "worse_end"
    monkeypatch.undo()


def test_invalidate_job_dedupe_keys_removes_runtime_state() -> None:
    fake_db = _FakeDb()
    fake_db.runtime["job-a"] = {
        "state": STATE_CROSSING_ACTIVE,
        "state_since": datetime.now(tz=timezone.utc),
    }
    fake_db.runtime["job-b"] = {
        "state": STATE_CROSSING_INCOMING,
        "state_since": datetime.now(tz=timezone.utc),
    }

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "app.state_store.psycopg.connect",
        lambda _database_url: _FakeConnection(fake_db),
    )

    store = AlertStateStore("postgresql://user:pass@localhost:5432/db")
    removed = store.invalidate_job_dedupe_keys("job-a")

    assert removed == 1
    assert set(fake_db.runtime) == {"job-b"}
    monkeypatch.undo()
