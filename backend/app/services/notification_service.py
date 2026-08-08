"""
Notification dispatch: always records an in-app notification row, and
additionally sends a real email via SMTP when SMTP_HOST/SMTP_USER/
SMTP_PASSWORD are configured. SMS is architected the same way
(send_sms is the integration point for a provider such as Twilio) but
left unimplemented until an SMS provider key is supplied, since
sending a real text message requires a paid account.
"""
from __future__ import annotations

import smtplib
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app.config import settings
from app.models.notification import Notification, NotificationChannel


def notify_in_app(db: Session, user_id: str, title: str, message: str, related_report_id: str | None = None) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        channel=NotificationChannel.IN_APP,
        related_report_id=related_report_id,
        delivered=True,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def send_email(to_address: str, subject: str, body: str) -> bool:
    if not (settings.smtp_host and settings.smtp_user and settings.smtp_password):
        return False

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = settings.smtp_from_address
    message["To"] = to_address

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_from_address, [to_address], message.as_string())
    return True


def send_sms(to_phone: str, message: str) -> bool:
    """Integration point for an SMS provider (e.g. Twilio). Returns False
    until SMS provider credentials are added to app/config.py and this
    function is wired up to that provider's SDK/API."""
    return False
