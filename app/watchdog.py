from __future__ import annotations

import logging
import os
import smtplib
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage

import docker
from docker.errors import APIError, NotFound


logger = logging.getLogger("hochwasser-watchdog")


def _bool_env(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _required_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


@dataclass(frozen=True)
class WatchdogSettings:
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_sender: str
    smtp_use_starttls: bool
    smtp_use_ssl: bool
    recipients: tuple[str, ...]
    watch_containers: tuple[str, ...]
    cooldown_seconds: int
    auto_restart_unhealthy: bool


def load_settings() -> WatchdogSettings:
    recipients_raw = _required_env("WATCHDOG_ALERT_RECIPIENTS")
    recipients = tuple(
        addr.strip() for addr in recipients_raw.split(",") if addr.strip()
    )
    if not recipients:
        raise ValueError("WATCHDOG_ALERT_RECIPIENTS must not be empty")

    watch_raw = os.getenv("WATCHDOG_WATCH_CONTAINERS", "")
    watch_containers = tuple(
        name.strip() for name in watch_raw.split(",") if name.strip()
    )

    return WatchdogSettings(
        smtp_host=_required_env("SMTP_HOST"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_sender=_required_env("SMTP_SENDER"),
        smtp_use_starttls=_bool_env("SMTP_USE_STARTTLS", True),
        smtp_use_ssl=_bool_env("SMTP_USE_SSL", False),
        recipients=recipients,
        watch_containers=watch_containers,
        cooldown_seconds=max(0, int(os.getenv("WATCHDOG_COOLDOWN_SECONDS", "900"))),
        auto_restart_unhealthy=_bool_env("WATCHDOG_AUTO_RESTART_UNHEALTHY", True),
    )


def _send_email(settings: WatchdogSettings, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_sender
    msg["To"] = ", ".join(settings.recipients)
    msg.set_content(body)

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(
            settings.smtp_host, settings.smtp_port, timeout=20
        ) as server:
            _login_if_needed(server, settings)
            server.send_message(msg)
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        server.ehlo()
        if settings.smtp_use_starttls:
            server.starttls()
            server.ehlo()
        _login_if_needed(server, settings)
        server.send_message(msg)


def _login_if_needed(server: smtplib.SMTP, settings: WatchdogSettings) -> None:
    if settings.smtp_username:
        server.login(settings.smtp_username, settings.smtp_password)


def _matches_watchlist(container_name: str, watch_containers: tuple[str, ...]) -> bool:
    if not watch_containers:
        return True
    return container_name in watch_containers


def _restart_container(client: docker.DockerClient, container_name: str) -> str:
    try:
        container = client.containers.get(container_name)
        container.restart(timeout=10)
        return "restart requested"
    except NotFound:
        return "container not found"
    except APIError as exc:
        return f"restart failed: {exc}"


def main() -> None:
    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s %(message)s")

    settings = load_settings()
    logger.info(
        "Watchdog started, watch_containers=%s, auto_restart_unhealthy=%s, cooldown=%ds",
        ",".join(settings.watch_containers) if settings.watch_containers else "all",
        settings.auto_restart_unhealthy,
        settings.cooldown_seconds,
    )

    client = docker.from_env()
    last_alert_sent: dict[str, float] = {}

    while True:
        try:
            for event in client.events(decode=True):
                if event.get("Type") != "container":
                    continue

                action = str(event.get("Action", ""))
                actor = event.get("Actor") or {}
                attrs = actor.get("Attributes") or {}
                container_name = str(attrs.get("name", "")).strip()
                if not container_name or not _matches_watchlist(
                    container_name, settings.watch_containers
                ):
                    continue

                notify_type: str | None = None
                restart_note = ""
                if action == "die":
                    notify_type = "die"
                elif action == "health_status: unhealthy":
                    notify_type = "unhealthy"
                    if settings.auto_restart_unhealthy:
                        restart_result = _restart_container(client, container_name)
                        restart_note = f"\nAuto-restart: {restart_result}"

                if not notify_type:
                    continue

                alert_key = f"{container_name}|{notify_type}"
                now_ts = time.time()
                previous = last_alert_sent.get(alert_key)
                if (
                    previous is not None
                    and settings.cooldown_seconds > 0
                    and now_ts - previous < settings.cooldown_seconds
                ):
                    logger.info(
                        "Suppressed alert for %s (%s), within cooldown",
                        container_name,
                        notify_type,
                    )
                    continue

                timestamp = datetime.now(timezone.utc).isoformat()
                subject = f"[Hochwasser Watchdog] {container_name} {notify_type} at {timestamp}"
                body = (
                    f"Container: {container_name}\n"
                    f"Event: {notify_type}\n"
                    f"Original Docker action: {action}\n"
                    f"Time (UTC): {timestamp}\n"
                    f"Actor ID: {actor.get('ID', '-')}{restart_note}\n"
                )
                _send_email(settings, subject, body)
                last_alert_sent[alert_key] = now_ts
                logger.warning("Alert sent for %s (%s)", container_name, notify_type)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Docker event stream error: %s", exc)
            time.sleep(5)


if __name__ == "__main__":
    main()
