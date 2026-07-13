import smtplib
from email.message import EmailMessage
from collections.abc import Callable

from agent_notice.config import Settings


def send_email(
    settings: Settings,
    subject: str,
    body: str,
    smtp_factory: Callable[[str, int], smtplib.SMTP_SSL] = smtplib.SMTP_SSL,
) -> None:
    message = EmailMessage()
    message["From"] = settings.smtp_user
    message["To"] = settings.email_to
    message["Subject"] = subject
    message.set_content(body)
    with smtp_factory("smtp.qq.com", 465) as smtp:
        smtp.login(settings.smtp_user, settings.smtp_auth_code)
        smtp.send_message(message)
