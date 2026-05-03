import smtplib
from email.message import EmailMessage

from app.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, MAIL_FROM, APP_BASE_URL


def send_verification_email(to_email: str, token: str) -> None:
    verify_link = f"{APP_BASE_URL}/api/auth/verify?token={token}"

    msg = EmailMessage()
    msg["Subject"] = "Verify your email"
    msg["From"] = MAIL_FROM
    msg["To"] = to_email
    msg.set_content(f"Please verify your email by clicking the link:\n{verify_link}\n")

    with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT)) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)