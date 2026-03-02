from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import psycopg

from app.config import Settings
from app.notifier import probe_smtp, send_alert_email


STALE_SENDING_TIMEOUT = timedelta(minutes=15)


@dataclass(frozen=True)
class DispatchCycleResult:
    smtp_available: bool
    smtp_error: str | None
    queued_due: int
    sent: int
    failed: int


@dataclass(frozen=True)
class _OutboxMessage:
    id: int
    job_uuid: str
    target_state: str
    trigger_reason: str
    state_since: datetime
    predicted_crossing_at: datetime | None
    predicted_end_at: datetime | None
    predicted_peak_cm: float | None
    predicted_peak_at: datetime | None
    recipients: list[str]
    subject: str
    body_text: str
    body_html: str | None
    attempt_count: int


def run_outbox_dispatch_cycle(
    database_url: str,
    settings: Settings,
    now: datetime,
    batch_size: int = 50,
    max_attempts: int = 10,
    stale_sending_timeout: timedelta = STALE_SENDING_TIMEOUT,
) -> DispatchCycleResult:
    stale_sending_before = now - stale_sending_timeout
    queued_due = _count_due_outbox(database_url, now, stale_sending_before)
    smtp_available, smtp_error = probe_smtp(settings)
    if not smtp_available:
        return DispatchCycleResult(
            smtp_available=False,
            smtp_error=smtp_error,
            queued_due=queued_due,
            sent=0,
            failed=0,
        )

    messages = _claim_outbox_messages(
        database_url,
        now,
        batch_size,
        stale_sending_before,
    )
    sent = 0
    failed = 0
    for message in messages:
        try:
            send_alert_email(
                settings=settings,
                recipients=tuple(message.recipients),
                subject=message.subject,
                body=message.body_text,
                html_body=message.body_html,
            )
        except Exception as exc:  # noqa: BLE001
            failed += 1
            _mark_outbox_failed(database_url, message, now, str(exc), max_attempts)
            continue

        sent += 1
        _mark_outbox_sent(database_url, message, now)

    return DispatchCycleResult(
        smtp_available=True,
        smtp_error=None,
        queued_due=queued_due,
        sent=sent,
        failed=failed,
    )


def _count_due_outbox(
    database_url: str,
    now: datetime,
    stale_sending_before: datetime,
) -> int:
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT count(*)
                FROM public.email_outbox
                WHERE (
                    status IN ('queued', 'failed')
                    AND next_attempt_at <= %s
                )
                OR (
                    status = 'sending'
                    AND sending_started_at <= %s
                )
                """,
                (now, stale_sending_before),
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0


def _claim_outbox_messages(
    database_url: str,
    now: datetime,
    batch_size: int,
    stale_sending_before: datetime,
) -> list[_OutboxMessage]:
    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    WITH candidates AS (
                        SELECT id
                        FROM public.email_outbox
                        WHERE (
                            status IN ('queued', 'failed')
                            AND next_attempt_at <= %s
                        )
                        OR (
                            status = 'sending'
                            AND sending_started_at <= %s
                        )
                        ORDER BY created_at ASC
                        FOR UPDATE SKIP LOCKED
                        LIMIT %s
                    )
                    UPDATE public.email_outbox AS o
                    SET status = 'sending', sending_started_at = %s, updated_at = %s
                    FROM candidates
                    WHERE o.id = candidates.id
                    RETURNING
                        o.id,
                        o.job_uuid,
                        o.target_state,
                        o.trigger_reason,
                        o.state_since,
                        o.predicted_crossing_at,
                        o.predicted_end_at,
                        o.predicted_peak_cm,
                        o.predicted_peak_at,
                        o.recipients,
                        o.subject,
                        o.body_text,
                        o.body_html,
                        o.attempt_count
                    """,
                    (now, stale_sending_before, batch_size, now, now),
                )
                rows = cur.fetchall()

    return [
        _OutboxMessage(
            id=row[0],
            job_uuid=row[1],
            target_state=row[2],
            trigger_reason=row[3],
            state_since=row[4],
            predicted_crossing_at=row[5],
            predicted_end_at=row[6],
            predicted_peak_cm=row[7],
            predicted_peak_at=row[8],
            recipients=row[9],
            subject=row[10],
            body_text=row[11],
            body_html=row[12],
            attempt_count=int(row[13]),
        )
        for row in rows
    ]


def _mark_outbox_sent(
    database_url: str, message: _OutboxMessage, now: datetime
) -> None:
    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE public.email_outbox
                    SET status = 'sent', sent_at = %s, sending_started_at = NULL, updated_at = %s
                    WHERE id = %s
                    """,
                    (now, now, message.id),
                )
                cur.execute(
                    """
                    UPDATE public.alert_job_runtime_state
                    SET last_notified_state = %s,
                        last_notified_at = %s,
                        last_notified_predicted_crossing_at = %s,
                        last_notified_predicted_end_at = %s,
                        last_notified_peak_cm = %s,
                        last_notified_peak_at = %s,
                        updated_at = %s
                    WHERE job_uuid = %s AND state_since = %s
                    """,
                    (
                        message.target_state,
                        now,
                        message.predicted_crossing_at,
                        message.predicted_end_at,
                        message.predicted_peak_cm,
                        message.predicted_peak_at,
                        now,
                        message.job_uuid,
                        message.state_since,
                    ),
                )


def _mark_outbox_failed(
    database_url: str,
    message: _OutboxMessage,
    now: datetime,
    error: str,
    max_attempts: int,
) -> None:
    attempts = message.attempt_count + 1
    delay_minutes = min(60, 2 ** min(attempts, 6))
    next_attempt = now + timedelta(minutes=delay_minutes)
    new_status = "dead" if attempts >= max_attempts else "failed"
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE public.email_outbox
                SET status = %s,
                    attempt_count = %s,
                    next_attempt_at = %s,
                    sending_started_at = NULL,
                    last_error = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (new_status, attempts, next_attempt, error, now, message.id),
            )
