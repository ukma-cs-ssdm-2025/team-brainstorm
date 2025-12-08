# src/services/send_email.py

from aiosmtplib import send
from email.mime.text import MIMEText
import os

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")       # email
SMTP_PASS = os.getenv("SMTP_PASSWORD")   # <-- FIX: правильне ім'я змінної

EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)


async def send_email(to_email: str, subject: str, message: str):
    msg = MIMEText(message, "plain", "utf-8")
    msg["From"] = EMAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = subject

    await send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=SMTP_PASS,
        start_tls=True,
    )
