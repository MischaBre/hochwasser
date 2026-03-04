from __future__ import annotations

from urllib.error import HTTPError, URLError

import pytest

from app.http_json_client import HttpJsonClient


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


def test_get_json_reads_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    client = HttpJsonClient(base_url="https://example.invalid")

    def fake_urlopen(url: str, timeout: int):
        assert url == "https://example.invalid/health"
        assert timeout == 20
        return _FakeResponse(b'{"ok": true}')

    monkeypatch.setattr("app.http_json_client.urlopen", fake_urlopen)

    assert client._get_json("/health") == {"ok": True}


def test_get_json_raises_runtime_error_on_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = HttpJsonClient(base_url="https://example.invalid")

    def fake_urlopen(url: str, timeout: int):
        raise HTTPError(url, 404, "not found", hdrs=None, fp=None)

    monkeypatch.setattr("app.http_json_client.urlopen", fake_urlopen)

    with pytest.raises(RuntimeError, match="HTTP 404"):
        client._get_json("/missing")


def test_get_json_raises_runtime_error_on_url_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = HttpJsonClient(base_url="https://example.invalid")

    def fake_urlopen(url: str, timeout: int):
        raise URLError("dns failed")

    monkeypatch.setattr("app.http_json_client.urlopen", fake_urlopen)

    with pytest.raises(RuntimeError, match="Could not reach"):
        client._get_json("/any")
