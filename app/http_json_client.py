from __future__ import annotations

import json
import logging
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


class HttpJsonClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: int = 20,
        logger_name: str = "hochwasser-alert.provider",
        provider_name: str = "provider",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.provider_name = provider_name
        self.logger = logging.getLogger(logger_name)

    def _resolve_url(self, endpoint: str) -> str:
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        return f"{self.base_url}{endpoint}"

    def _get_json(self, endpoint: str) -> Any:
        url = self._resolve_url(endpoint)
        self.logger.info("Fetching %s data: %s", self.provider_name, url)
        try:
            with urlopen(url, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
                self.logger.info(
                    "Fetched %s response successfully: %s",
                    self.provider_name,
                    url,
                )
                return data
        except HTTPError as exc:
            raise RuntimeError(f"HTTP {exc.code} for {url}") from exc
        except URLError as exc:
            raise RuntimeError(f"Could not reach {url}: {exc}") from exc
