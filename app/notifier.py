from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.config import Settings


logger = logging.getLogger("hochwasser-alert.notifier")


def send_alert_email(
    settings: Settings,
    recipients: tuple[str, ...],
    subject: str,
    body: str,
    html_body: str | None = None,
) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_sender
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    logger.info(
        "Sending alert email via %s:%d to %s with subject '%s'",
        settings.smtp_host,
        settings.smtp_port,
        ", ".join(recipients),
        subject,
    )

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(
            settings.smtp_host, settings.smtp_port, timeout=20
        ) as server:
            _login_if_needed(server, settings)
            server.send_message(msg)
        logger.info("Alert email successfully sent (SMTP SSL)")
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        server.ehlo()
        if settings.smtp_use_starttls:
            server.starttls()
            server.ehlo()
        _login_if_needed(server, settings)
        server.send_message(msg)
    logger.info("Alert email successfully sent")


def _login_if_needed(server: smtplib.SMTP, settings: Settings) -> None:
    if settings.smtp_username:
        server.login(settings.smtp_username, settings.smtp_password)
