from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

import psycopg

STATE_NO_CROSSING = "no_crossing"
STATE_CROSSING_INCOMING = "crossing_incoming"
STATE_CROSSING_ACTIVE = "crossing_active"
STATE_CROSSING_SOON_OVER = "crossing_soon_over"

WORSE_TIME_THRESHOLD = timedelta(hours=1)
WORSE_PEAK_CM_THRESHOLD = 3.0


@dataclass(frozen=True)
class JobStateCycleResult:
    previous_state: str | None
    current_state: str
    transitioned: bool
    notification_required: bool
    notification_queued: bool
    notification_reason: str | None


class AlertStateStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def apply_job_state(
        self,
        job_uuid: str,
        state: str,
        now: datetime,
        predicted_crossing_at: datetime | None,
        predicted_end_at: datetime | None,
        predicted_peak_cm: float | None,
        predicted_peak_at: datetime | None,
        repeat_active_on_check: bool,
        recipients: tuple[str, ...],
        subject: str,
        body_text: str,
        body_html: str | None,
    ) -> JobStateCycleResult:
        self._validate_state(state)

        with psycopg.connect(self.database_url) as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT pg_advisory_xact_lock(hashtext(%s))",
                        (f"job-state:{job_uuid}",),
                    )
                    cur.execute(
                        """
                        SELECT
                            state,
                            state_since,
                            last_notified_state,
                            last_notified_predicted_crossing_at,
                            last_notified_predicted_end_at,
                            last_notified_peak_cm,
                            last_notified_peak_at
                        FROM public.alert_job_runtime_state
                        WHERE job_uuid = %s
                        FOR UPDATE
                        """,
                        (job_uuid,),
                    )
                    row = cur.fetchone()

                    previous_state: str | None = None
                    previous_state_since: datetime | None = None
                    last_notified_state: str | None = None
                    last_notified_crossing_at: datetime | None = None
                    last_notified_end_at: datetime | None = None
                    last_notified_peak_cm: float | None = None
                    if row is not None:
                        (
                            previous_state,
                            previous_state_since,
                            last_notified_state,
                            last_notified_crossing_at,
                            last_notified_end_at,
                            last_notified_peak_cm,
                            _last_notified_peak_at,
                        ) = row

                    transitioned = previous_state != state
                    notification_reason = _notification_reason(
                        state=state,
                        transitioned=transitioned,
                        repeat_active_on_check=repeat_active_on_check,
                        last_notified_state=last_notified_state,
                        last_notified_crossing_at=last_notified_crossing_at,
                        last_notified_end_at=last_notified_end_at,
                        last_notified_peak_cm=last_notified_peak_cm,
                        predicted_crossing_at=predicted_crossing_at,
                        predicted_end_at=predicted_end_at,
                        predicted_peak_cm=predicted_peak_cm,
                    )
                    notification_required = notification_reason is not None
                    state_since = (
                        now
                        if transitioned or previous_state_since is None
                        else previous_state_since
                    )

                    cur.execute(
                        """
                        INSERT INTO public.alert_job_runtime_state (
                            job_uuid,
                            state,
                            state_since,
                            predicted_crossing_at,
                            predicted_end_at,
                            predicted_peak_cm,
                            predicted_peak_at,
                            updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (job_uuid)
                        DO UPDATE SET
                            state = EXCLUDED.state,
                            state_since = EXCLUDED.state_since,
                            predicted_crossing_at = EXCLUDED.predicted_crossing_at,
                            predicted_end_at = EXCLUDED.predicted_end_at,
                            predicted_peak_cm = EXCLUDED.predicted_peak_cm,
                            predicted_peak_at = EXCLUDED.predicted_peak_at,
                            updated_at = EXCLUDED.updated_at
                        """,
                        (
                            job_uuid,
                            state,
                            state_since,
                            predicted_crossing_at,
                            predicted_end_at,
                            predicted_peak_cm,
                            predicted_peak_at,
                            now,
                        ),
                    )

                    notification_queued = False
                    if notification_required:
                        cur.execute(
                            """
                            INSERT INTO public.email_outbox (
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
                                status,
                                attempt_count,
                                next_attempt_at,
                                created_at,
                                updated_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'queued', 0, %s, %s, %s)
                            """,
                            (
                                job_uuid,
                                state,
                                notification_reason,
                                state_since,
                                predicted_crossing_at,
                                predicted_end_at,
                                predicted_peak_cm,
                                predicted_peak_at,
                                list(recipients),
                                subject,
                                body_text,
                                body_html,
                                now,
                                now,
                                now,
                            ),
                        )
                        notification_queued = True

        return JobStateCycleResult(
            previous_state=previous_state,
            current_state=state,
            transitioned=transitioned,
            notification_required=notification_required,
            notification_queued=notification_queued,
            notification_reason=notification_reason,
        )

    def invalidate_job_dedupe_keys(self, job_uuid: str) -> int:
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM public.alert_job_runtime_state WHERE job_uuid = %s RETURNING job_uuid",
                    (job_uuid,),
                )
                return len(cur.fetchall())

    @staticmethod
    def _validate_state(state: str) -> None:
        if state not in {
            STATE_NO_CROSSING,
            STATE_CROSSING_INCOMING,
            STATE_CROSSING_ACTIVE,
            STATE_CROSSING_SOON_OVER,
        }:
            raise ValueError(f"invalid job state: {state}")


def _notification_reason(
    state: str,
    transitioned: bool,
    repeat_active_on_check: bool,
    last_notified_state: str | None,
    last_notified_crossing_at: datetime | None,
    last_notified_end_at: datetime | None,
    last_notified_peak_cm: float | None,
    predicted_crossing_at: datetime | None,
    predicted_end_at: datetime | None,
    predicted_peak_cm: float | None,
) -> str | None:
    if transitioned:
        return "transition"

    if repeat_active_on_check and state == STATE_CROSSING_ACTIVE:
        return "repeat"

    if last_notified_state != state:
        return None

    if state == STATE_CROSSING_INCOMING:
        if (
            predicted_crossing_at is not None
            and last_notified_crossing_at is not None
            and predicted_crossing_at
            <= last_notified_crossing_at - WORSE_TIME_THRESHOLD
        ):
            return "worse_eta"
        if (
            predicted_peak_cm is not None
            and last_notified_peak_cm is not None
            and predicted_peak_cm >= last_notified_peak_cm + WORSE_PEAK_CM_THRESHOLD
        ):
            return "worse_peak"
        return None

    if state == STATE_CROSSING_ACTIVE:
        if (
            predicted_peak_cm is not None
            and last_notified_peak_cm is not None
            and predicted_peak_cm >= last_notified_peak_cm + WORSE_PEAK_CM_THRESHOLD
        ):
            return "worse_peak"
        return None

    if state == STATE_CROSSING_SOON_OVER:
        if (
            predicted_end_at is not None
            and last_notified_end_at is not None
            and predicted_end_at >= last_notified_end_at + WORSE_TIME_THRESHOLD
        ):
            return "worse_end"
        return None

    return None
