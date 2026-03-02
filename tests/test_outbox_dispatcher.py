from datetime import datetime, timedelta, timezone

import pytest

from app.config import Settings
from app.outbox_dispatcher import run_outbox_dispatch_cycle


class _FakeDb:
    def __init__(self) -> None:
        self.outbox: list[dict[str, object]] = []


def _is_due(
    row: dict[str, object],
    now: datetime,
    stale_sending_before: datetime,
) -> bool:
    status = row["status"]
    if status in {"queued", "failed"}:
        next_attempt_at = row["next_attempt_at"]
        return isinstance(next_attempt_at, datetime) and next_attempt_at <= now
    if status == "sending":
        sending_started_at = row.get("sending_started_at")
        return (
            isinstance(sending_started_at, datetime)
            and sending_started_at <= stale_sending_before
        )
    return False


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
        if "SELECT count(*)" in query and "FROM public.email_outbox" in query:
            now, stale_sending_before = params
            due = sum(
                1
                for row in self._db.outbox
                if _is_due(row, now, stale_sending_before)  # type: ignore[arg-type]
            )
            self._last_row = (due,)
            return

        if "WITH candidates AS" in query and "UPDATE public.email_outbox AS o" in query:
            now, stale_sending_before, batch_size, sending_started_at, updated_at = (
                params
            )
            candidates = [
                row
                for row in sorted(self._db.outbox, key=lambda item: item["created_at"])
                if _is_due(row, now, stale_sending_before)  # type: ignore[arg-type]
            ][: int(batch_size)]
            for row in candidates:
                row["status"] = "sending"
                row["sending_started_at"] = sending_started_at
                row["updated_at"] = updated_at
            self._rows = [
                (
                    row["id"],
                    row["job_uuid"],
                    row["target_state"],
                    row["trigger_reason"],
                    row["state_since"],
                    row["predicted_crossing_at"],
                    row["predicted_end_at"],
                    row["predicted_peak_cm"],
                    row["predicted_peak_at"],
                    row["recipients"],
                    row["subject"],
                    row["body_text"],
                    row["body_html"],
                    row["attempt_count"],
                )
                for row in candidates
            ]
            return

        if "UPDATE public.email_outbox" in query and "SET status = 'sent'" in query:
            sent_at, updated_at, message_id = params
            row = next(item for item in self._db.outbox if item["id"] == message_id)
            row["status"] = "sent"
            row["sent_at"] = sent_at
            row["sending_started_at"] = None
            row["updated_at"] = updated_at
            return

        if "UPDATE public.alert_job_runtime_state" in query:
            return

        if "UPDATE public.email_outbox" in query and "attempt_count" in query:
            status, attempts, next_attempt_at, error, updated_at, message_id = params
            row = next(item for item in self._db.outbox if item["id"] == message_id)
            row["status"] = status
            row["attempt_count"] = attempts
            row["next_attempt_at"] = next_attempt_at
            row["sending_started_at"] = None
            row["last_error"] = error
            row["updated_at"] = updated_at
            return

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


def _make_settings() -> Settings:
    return Settings(
        provider="pegelonline",
        database_url="postgresql://user:pass@localhost:5432/db",
        forecast_series_shortname="WV",
        dedupe_hours=24,
        timezone="UTC",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="",
        smtp_password="",
        smtp_sender="alerts@example.com",
        smtp_use_starttls=True,
        smtp_use_ssl=False,
        admin_recipients=("ops@example.com",),
        health_host="0.0.0.0",
        health_port=8090,
        health_failure_threshold=3,
        jobs=(),
    )


def _base_outbox_row(now: datetime) -> dict[str, object]:
    return {
        "id": 1,
        "job_uuid": "job-a",
        "target_state": "crossing_incoming",
        "trigger_reason": "transition",
        "state_since": now,
        "predicted_crossing_at": now,
        "predicted_end_at": None,
        "predicted_peak_cm": 123.0,
        "predicted_peak_at": now,
        "recipients": ["a@example.com"],
        "subject": "subject",
        "body_text": "body",
        "body_html": None,
        "status": "queued",
        "attempt_count": 0,
        "next_attempt_at": now,
        "sent_at": None,
        "sending_started_at": None,
        "last_error": None,
        "created_at": now,
        "updated_at": now,
    }


def test_dispatch_reclaims_stale_sending_and_sends() -> None:
    now = datetime(2026, 3, 2, 12, 0, tzinfo=timezone.utc)
    fake_db = _FakeDb()
    row = _base_outbox_row(now)
    row["status"] = "sending"
    row["next_attempt_at"] = now + timedelta(hours=3)
    row["sending_started_at"] = now - timedelta(minutes=20)
    fake_db.outbox.append(row)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "app.outbox_dispatcher.psycopg.connect",
        lambda _database_url: _FakeConnection(fake_db),
    )
    monkeypatch.setattr(
        "app.outbox_dispatcher.probe_smtp", lambda _settings: (True, None)
    )
    monkeypatch.setattr(
        "app.outbox_dispatcher.send_alert_email", lambda **_kwargs: None
    )

    result = run_outbox_dispatch_cycle(
        database_url="postgresql://user:pass@localhost:5432/db",
        settings=_make_settings(),
        now=now,
        stale_sending_timeout=timedelta(minutes=15),
    )

    assert result.smtp_available is True
    assert result.queued_due == 1
    assert result.sent == 1
    assert result.failed == 0
    assert fake_db.outbox[0]["status"] == "sent"
    assert fake_db.outbox[0]["sending_started_at"] is None
    assert fake_db.outbox[0]["sent_at"] == now
    monkeypatch.undo()


def test_dispatch_does_not_reclaim_fresh_sending() -> None:
    now = datetime(2026, 3, 2, 12, 0, tzinfo=timezone.utc)
    fake_db = _FakeDb()
    row = _base_outbox_row(now)
    row["status"] = "sending"
    row["next_attempt_at"] = now + timedelta(hours=3)
    row["sending_started_at"] = now - timedelta(minutes=5)
    fake_db.outbox.append(row)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "app.outbox_dispatcher.psycopg.connect",
        lambda _database_url: _FakeConnection(fake_db),
    )
    monkeypatch.setattr(
        "app.outbox_dispatcher.probe_smtp", lambda _settings: (True, None)
    )
    monkeypatch.setattr(
        "app.outbox_dispatcher.send_alert_email", lambda **_kwargs: None
    )

    result = run_outbox_dispatch_cycle(
        database_url="postgresql://user:pass@localhost:5432/db",
        settings=_make_settings(),
        now=now,
        stale_sending_timeout=timedelta(minutes=15),
    )

    assert result.smtp_available is True
    assert result.queued_due == 0
    assert result.sent == 0
    assert result.failed == 0
    assert fake_db.outbox[0]["status"] == "sending"
    assert fake_db.outbox[0]["sending_started_at"] == now - timedelta(minutes=5)
    monkeypatch.undo()


def test_dispatch_failure_clears_sending_started_at() -> None:
    now = datetime(2026, 3, 2, 12, 0, tzinfo=timezone.utc)
    fake_db = _FakeDb()
    row = _base_outbox_row(now)
    row["status"] = "sending"
    row["next_attempt_at"] = now + timedelta(hours=3)
    row["sending_started_at"] = now - timedelta(minutes=20)
    fake_db.outbox.append(row)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "app.outbox_dispatcher.psycopg.connect",
        lambda _database_url: _FakeConnection(fake_db),
    )
    monkeypatch.setattr(
        "app.outbox_dispatcher.probe_smtp", lambda _settings: (True, None)
    )

    def _raise_send(**_kwargs: object) -> None:
        raise RuntimeError("smtp temporary failure")

    monkeypatch.setattr("app.outbox_dispatcher.send_alert_email", _raise_send)

    result = run_outbox_dispatch_cycle(
        database_url="postgresql://user:pass@localhost:5432/db",
        settings=_make_settings(),
        now=now,
        max_attempts=2,
        stale_sending_timeout=timedelta(minutes=15),
    )

    assert result.smtp_available is True
    assert result.queued_due == 1
    assert result.sent == 0
    assert result.failed == 1
    assert fake_db.outbox[0]["status"] == "failed"
    assert fake_db.outbox[0]["attempt_count"] == 1
    assert fake_db.outbox[0]["sending_started_at"] is None
    assert fake_db.outbox[0]["next_attempt_at"] > now
    monkeypatch.undo()
