"""Plain SMTP sender. Local development delivers to Mailpit (http://localhost:8025)."""

import logging
import smtplib
from email.message import EmailMessage

from jyotish_api.settings import settings

log = logging.getLogger(__name__)
outbox: list[EmailMessage] = []  # filled in tests


def send(to: str, subject: str, text: str, headers: dict[str, str] | None = None) -> None:
    msg = EmailMessage()
    msg["From"] = settings.mail_from
    msg["To"] = to
    msg["Subject"] = subject
    for k, v in (headers or {}).items():
        msg[k] = v
    msg.set_content(text)
    if settings.environment == "test":
        outbox.append(msg)
        return
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as s:
            if settings.smtp_tls:
                s.starttls()
            if settings.smtp_user:
                s.login(settings.smtp_user, settings.smtp_password)
            s.send_message(msg)
    except OSError:
        log.exception("email delivery failed")
        if not settings.is_production:
            # Development fallback: print the message so the sign-in link is usable.
            log.warning("EMAIL to %s: %s\n%s", to, subject, text)
        else:
            raise
