from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable


class AlertStateStore:
    def __init__(self, state_file: Path) -> None:
        self.state_file = state_file
        self._lock = threading.Lock()
        self._state = self._load_state(state_file)

    def run_if_due(
        self,
        key: str,
        now: datetime,
        dedupe_hours: int,
        action: Callable[[], None],
    ) -> bool:
        with self._lock:
            if not self._should_send_alert_unlocked(key, now, dedupe_hours):
                return False
            action()
            self._remember_sent_unlocked(key, now)
            self._save_state_unlocked()
            return True

    def invalidate_job_dedupe_keys(self, job_uuid: str) -> int:
        prefix = f"{job_uuid}|"
        with self._lock:
            sent_keys = self._state.get("sent_keys")
            if not isinstance(sent_keys, dict):
                return 0
            keys_to_remove = [key for key in sent_keys if key.startswith(prefix)]
            for key in keys_to_remove:
                sent_keys.pop(key, None)
            removed = len(keys_to_remove)
            if removed:
                self._save_state_unlocked()
            return removed

    @staticmethod
    def _load_state(path: Path) -> dict:
        if not path.exists():
            return {"sent_keys": {}}
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
                if "sent_keys" not in data or not isinstance(data["sent_keys"], dict):
                    data["sent_keys"] = {}
                return data
        except (json.JSONDecodeError, OSError):
            return {"sent_keys": {}}

    def _save_state_unlocked(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with self.state_file.open("w", encoding="utf-8") as file:
            json.dump(self._state, file, indent=2)

    def _should_send_alert_unlocked(
        self, key: str, now: datetime, dedupe_hours: int
    ) -> bool:
        sent_at_raw = self._state["sent_keys"].get(key)
        if not sent_at_raw:
            return True

        try:
            sent_at = datetime.fromisoformat(sent_at_raw)
        except ValueError:
            return True

        return now - sent_at >= timedelta(hours=dedupe_hours)

    def _remember_sent_unlocked(self, key: str, now: datetime) -> None:
        self._state["sent_keys"][key] = now.isoformat()

        if len(self._state["sent_keys"]) > 500:
            items = sorted(
                self._state["sent_keys"].items(), key=lambda kv: kv[1], reverse=True
            )
            self._state["sent_keys"] = dict(items[:500])


def _hash_key_parts(*args: object) -> str:
    digest = hashlib.sha256()
    for arg in args:
        digest.update(str(arg).encode("utf-8"))
        digest.update(b"\x1f")
    return digest.hexdigest()


def build_dedupe_key(
    job_uuid: str, crossing_timestamp: datetime, alert_recipients: tuple[str, ...]
) -> str:
    hashed = _hash_key_parts(
        crossing_timestamp.isoformat(),
        ",".join(sorted(alert_recipients)),
    )
    return f"{job_uuid}|{hashed}"
