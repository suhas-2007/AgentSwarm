import os
import smtplib
import ssl

from email.message import EmailMessage

from dotenv import load_dotenv


load_dotenv()


def send_password_reset_email(
    recipient_email: str,
    reset_link: str
) -> None:

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(
        os.getenv(
            "SMTP_PORT",
            "587"
        )
    )

    smtp_username = os.getenv(
        "SMTP_USERNAME"
    )

    smtp_password = os.getenv(
        "SMTP_PASSWORD"
    )

    email_from = os.getenv(
        "EMAIL_FROM",
        smtp_username
    )

    if not smtp_host:
        raise ValueError(
            "SMTP_HOST is not configured."
        )

    if not smtp_username:
        raise ValueError(
            "SMTP_USERNAME is not configured."
        )

    if not smtp_password:
        raise ValueError(
            "SMTP_PASSWORD is not configured."
        )

    if not email_from:
        raise ValueError(
            "EMAIL_FROM is not configured."
        )


    message = EmailMessage()

    message["Subject"] = (
        "Reset your AgentSwarm password"
    )

    message["From"] = email_from

    message["To"] = recipient_email


    message.set_content(
        f"""
Hello,

We received a request to reset your AgentSwarm password.

Use the link below to create a new password:

{reset_link}

This password reset link will expire in 15 minutes.

If you did not request a password reset, you can safely ignore this email.

Regards,
AgentSwarm
"""
    )


    context = ssl.create_default_context()


    if smtp_port == 465:

        with smtplib.SMTP_SSL(
            smtp_host,
            smtp_port,
            context=context,
            timeout=20
        ) as server:

            server.login(
                smtp_username,
                smtp_password
            )

            server.send_message(
                message
            )

    else:

        with smtplib.SMTP(
            smtp_host,
            smtp_port,
            timeout=20
        ) as server:

            server.starttls(
                context=context
            )

            server.login(
                smtp_username,
                smtp_password
            )

            server.send_message(
                message
            )