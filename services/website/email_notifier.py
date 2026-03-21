import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class Notify:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.yandex.ru")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "s4vaki-notification@yandex.com")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.smtp_use_starttls = os.getenv("SMTP_USE_STARTTLS", "false").lower() == "true"
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "s4vaki-notification@yandex.com")
        self.to_email = os.getenv("LEADS_TO_EMAIL", "trip-kzn@mail.ru")

    def is_configured(self) -> bool:
        return all([
            self.smtp_host,
            self.smtp_port,
            self.smtp_username,
            self.smtp_password,
            self.from_email,
            self.to_email,
        ])

    def send_email(self, subject: str, message: str) -> None:
        if not self.is_configured():
            raise RuntimeError("Email notifier is not configured. Check SMTP_* and LEADS_TO_EMAIL env vars.")

        email = EmailMessage()
        email["Subject"] = subject
        email["From"] = self.from_email
        email["To"] = self.to_email
        email.set_content(message)

        if self.smtp_use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context, timeout=20) as server:
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(email)
            return

        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20) as server:
            if self.smtp_use_starttls:
                context = ssl.create_default_context()
                server.starttls(context=context)
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(email)