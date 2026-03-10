from __future__ import annotations

from fastapi import HTTPException, status

from api_app.main import _enforce_rate_limit, _rate_limit_buckets


def _clear_rate_limit_state() -> None:
    _rate_limit_buckets.clear()


def test_enforce_rate_limit_blocks_requests_over_limit() -> None:
    _clear_rate_limit_state()

    for _ in range(3):
        _enforce_rate_limit(
            key="write:test-user",
            max_requests=3,
            window_seconds=60,
            now=100.0,
        )

    try:
        _enforce_rate_limit(
            key="write:test-user",
            max_requests=3,
            window_seconds=60,
            now=100.0,
        )
        raise AssertionError("Expected HTTPException for rate limit")
    except HTTPException as exc:
        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert exc.detail == "Too many requests. Please retry later."
        assert exc.headers == {"Retry-After": "60"}


def test_enforce_rate_limit_prunes_old_entries() -> None:
    _clear_rate_limit_state()

    for _ in range(2):
        _enforce_rate_limit(
            key="write:test-user",
            max_requests=2,
            window_seconds=10,
            now=100.0,
        )

    _enforce_rate_limit(
        key="write:test-user",
        max_requests=2,
        window_seconds=10,
        now=111.0,
    )
