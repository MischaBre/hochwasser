from __future__ import annotations

import pytest

from app.pegelonline import PegelonlineClient
from app.provider_client import create_provider_client


def test_create_provider_client_returns_pegelonline_client() -> None:
    client = create_provider_client(
        provider="pegelonline",
        station_uuid="station-1",
        forecast_series_shortname="WV",
    )

    assert isinstance(client, PegelonlineClient)


def test_create_provider_client_rejects_unsupported_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported provider"):
        create_provider_client(provider="elwis", station_uuid="station-1")
