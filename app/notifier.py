from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.config import Settings


def send_alert_email(settings: Settings, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_sender
    msg["To"] = ", ".join(settings.alert_recipients)
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


def _login_if_needed(server: smtplib.SMTP, settings: Settings) -> None:
    if settings.smtp_username:
        server.login(settings.smtp_username, settings.smtp_password)
