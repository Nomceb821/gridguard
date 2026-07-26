"""
Sends alert notifications by email (SMTP) and SMS (Twilio).

Both are optional: if the relevant settings aren't configured, the function
logs a message instead of failing, so the app still runs end-to-end in a
demo environment without real credentials.
"""

import logging
import smtplib
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger("gridguard.alerts")


def send_email_alert(subject: str, body: str) -> bool:
    if not (settings.smtp_host and settings.smtp_username and settings.alert_email_to):
        logger.info("[demo mode] Email alert not sent (SMTP not configured): %s", subject)
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.alert_email_from or settings.smtp_username
    msg["To"] = settings.alert_email_to

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
        return True
    except Exception:
        logger.exception("Failed to send email alert")
        return False


def send_sms_alert(body: str) -> bool:
    if not (settings.twilio_account_sid and settings.twilio_auth_token and settings.alert_sms_to):
        logger.info("[demo mode] SMS alert not sent (Twilio not configured): %s", body)
        return False

    try:
        from twilio.rest import Client

        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        client.messages.create(
            body=body,
            from_=settings.twilio_from_number,
            to=settings.alert_sms_to,
        )
        return True
    except Exception:
        logger.exception("Failed to send SMS alert")
        return False


def dispatch_alert(subject: str, body: str) -> None:
    send_email_alert(subject, body)
    send_sms_alert(body)