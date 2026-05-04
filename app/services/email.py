"""
Email service utilities (SMTP).

This module sends transactional emails through SMTP (Mailtrap in development):
- email verification message
- password reset message

Configuration is read from environment variables (.env) via app.config:
- SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
- MAIL_FROM
- APP_BASE_URL

Notes:
- In development you can use Mailtrap SMTP credentials.
- In production you'd use a real SMTP provider.
"""

import smtplib
from email.message import EmailMessage

from app.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, MAIL_FROM, APP_BASE_URL


def send_verification_email(to_email: str, token: str) -> None:
    """
    Send email verification message.

    The email contains a verification link of the form:
        {APP_BASE_URL}/api/auth/verify?token=...

    Args:
        to_email: Recipient email address.
        token: Verification JWT token (type="verify").

    Raises:
        smtplib.SMTPException: On SMTP connection/auth/send failures.
    """
    verify_link = f"{APP_BASE_URL}/api/auth/verify?token={token}"

    msg = EmailMessage()
    msg["Subject"] = "Verify your email"
    msg["From"] = MAIL_FROM
    msg["To"] = to_email
    msg.set_content(
        "Please verify your email by clicking the link:\n"
        f"{verify_link}\n"
    )

    with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT)) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)


def send_password_reset_email(to_email: str, token: str) -> None:
    """
    Send password reset message.

    The message includes:
    - the reset token itself (JWT type="reset")
    - confirm endpoint URL
    - example curl command for quick testing

    Args:
        to_email: Recipient email address.
        token: Password reset JWT token (type="reset").

    Raises:
        smtplib.SMTPException: On SMTP connection/auth/send failures.
    """
    confirm_endpoint = f"{APP_BASE_URL}/api/auth/password-reset/confirm"

    msg = EmailMessage()
    msg["Subject"] = "Password reset request"
    msg["From"] = MAIL_FROM
    msg["To"] = to_email
    msg.set_content(
        "You requested a password reset.\n\n"
        f"Token:\n{token}\n\n"
        "Use this endpoint to confirm reset:\n"
        f"{confirm_endpoint}\n\n"
        "Example curl:\n"
        f"curl -X POST \"{confirm_endpoint}\" -H \"Content-Type: application/json\" "
        f"-d '{{\"token\":\"{token}\",\"new_password\":\"NEW_PASSWORD\"}}'\n"
    )

    with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT)) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)