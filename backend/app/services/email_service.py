import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode

from flask import current_app


def password_recovery_available():
    """Return whether the standard SMTP recovery channel is fully configured."""
    config = current_app.config
    return bool(
        config.get("SMTP_HOST")
        and config.get("SMTP_FROM_EMAIL")
        and config.get("PUBLIC_BASE_URL")
        and bool(config.get("SMTP_USERNAME")) == bool(config.get("SMTP_PASSWORD"))
        and not (config.get("SMTP_USE_TLS") and config.get("SMTP_USE_SSL"))
    )


def send_password_reset_email(user, raw_token):
    """Deliver one reset link without logging or persisting its raw token."""
    if not password_recovery_available():
        raise RuntimeError("Transactional email recovery is not configured")

    config = current_app.config
    reset_url = (
        f"{config['PUBLIC_BASE_URL']}/?"
        f"{urlencode({'reset_token': raw_token})}"
    )
    message = EmailMessage()
    message["Subject"] = "Reset your ResQ Command password"
    message["From"] = config["SMTP_FROM_EMAIL"]
    message["To"] = user.email
    message.set_content(
        "\n".join(
            [
                f"Hello {user.name},",
                "",
                "A password reset was requested for your ResQ Command account.",
                f"Use this single-use link within {config['PASSWORD_RESET_MINUTES']} minutes:",
                reset_url,
                "",
                "If you did not request this, ignore this email. Existing sessions remain valid unless the reset is completed.",
                "ResQ Command will never ask you to send a password, authenticator code, or recovery code by email.",
            ]
        )
    )

    smtp_class = smtplib.SMTP_SSL if config.get("SMTP_USE_SSL") else smtplib.SMTP
    smtp_kwargs = {
        "host": config["SMTP_HOST"],
        "port": config["SMTP_PORT"],
        "timeout": config["SMTP_TIMEOUT_SECONDS"],
    }
    if config.get("SMTP_USE_SSL"):
        smtp_kwargs["context"] = ssl.create_default_context()

    with smtp_class(**smtp_kwargs) as connection:
        if config.get("SMTP_USE_TLS"):
            connection.starttls(context=ssl.create_default_context())
        if config.get("SMTP_USERNAME"):
            connection.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
        connection.send_message(message)
