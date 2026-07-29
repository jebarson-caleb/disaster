import smtplib
from datetime import timedelta
from types import SimpleNamespace

from app.auth import digest, utcnow
from app.extensions import db
from app.models import AuthSession, MfaChallenge, PasswordResetToken, User
from app.services.email_service import send_password_reset_email

CURRENT_PASSWORD = "Existing-Citizen-Password-91"
NEW_PASSWORD = "Recovered-Citizen-Password-92"


def _register_citizen(client):
    return client.post(
        "/api/v1/auth/register",
        json={
            "name": "Recovery Citizen",
            "email": "recovery-citizen@example.com",
            "phone": "9000000991",
            "role": "Citizen",
            "password": CURRENT_PASSWORD,
        },
    )


def _configure_email_recovery(app):
    app.config.update(
        PUBLIC_BASE_URL="https://resq.example",
        SMTP_HOST="smtp.example",
        SMTP_PORT=587,
        SMTP_USERNAME="",
        SMTP_PASSWORD="",
        SMTP_FROM_EMAIL="security@resq.example",
        SMTP_USE_TLS=True,
        SMTP_USE_SSL=False,
        SMTP_TIMEOUT_SECONDS=3,
        PASSWORD_RESET_MINUTES=30,
    )


def test_password_reset_is_single_use_and_revokes_authentication_state(client, app, monkeypatch):
    registered = _register_citizen(client)
    assert registered.status_code == 201
    old_access_token = registered.get_json()["token"]
    _configure_email_recovery(app)

    delivered = {}

    def capture_delivery(user, raw_token):
        delivered.update(user_id=user.id, token=raw_token)

    monkeypatch.setattr("app.routes.auth.send_password_reset_email", capture_delivery)
    with app.app_context():
        user = User.query.filter_by(email="recovery-citizen@example.com").one()
        db.session.add(
            MfaChallenge(
                user_id=user.id,
                token_hash=digest("pending-password-derived-challenge"),
                expires_at=utcnow() + timedelta(minutes=5),
            )
        )
        db.session.commit()
        user_id = user.id

    requested = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "RECOVERY-CITIZEN@example.com"},
    )
    assert requested.status_code == 202
    assert requested.get_json()["recovery_available"] is True
    assert delivered["user_id"] == user_id

    with app.app_context():
        reset_token = PasswordResetToken.query.filter_by(user_id=user_id).one()
        assert reset_token.token_hash == digest(delivered["token"])
        assert reset_token.token_hash != delivered["token"]
        assert reset_token.consumed_at is None

    weak = client.post(
        "/api/v1/auth/password-reset/complete",
        json={"token": delivered["token"], "new_password": "too-short"},
    )
    assert weak.status_code == 400

    completed = client.post(
        "/api/v1/auth/password-reset/complete",
        json={"token": delivered["token"], "new_password": NEW_PASSWORD},
    )
    assert completed.status_code == 200
    assert client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {old_access_token}"},
    ).status_code == 401

    with app.app_context():
        assert MfaChallenge.query.filter_by(user_id=user_id).count() == 0
        assert AuthSession.query.filter_by(user_id=user_id, revoked_at=None).count() == 0
        assert PasswordResetToken.query.filter_by(user_id=user_id, consumed_at=None).count() == 0

    reused = client.post(
        "/api/v1/auth/password-reset/complete",
        json={"token": delivered["token"], "new_password": "Another-Recovered-Password-93"},
    )
    assert reused.status_code == 400
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "recovery-citizen@example.com", "password": CURRENT_PASSWORD},
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "recovery-citizen@example.com", "password": NEW_PASSWORD},
    ).status_code == 200


def test_password_reset_request_does_not_enumerate_accounts(client, app, monkeypatch):
    _configure_email_recovery(app)
    delivered = []
    monkeypatch.setattr(
        "app.routes.auth.send_password_reset_email",
        lambda user, token: delivered.append((user.id, token)),
    )

    unknown = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "unknown@example.com"},
    )
    assert unknown.status_code == 202
    assert unknown.get_json()["recovery_available"] is True
    assert delivered == []
    with app.app_context():
        assert PasswordResetToken.query.count() == 0

    unavailable_app = app
    unavailable_app.config.update(SMTP_HOST="", SMTP_FROM_EMAIL="")
    unavailable = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "unknown@example.com"},
    )
    assert unavailable.status_code == 202
    assert unavailable.get_json()["recovery_available"] is False


def test_failed_email_delivery_invalidates_reset_token(client, app, monkeypatch):
    registered = _register_citizen(client)
    assert registered.status_code == 201
    _configure_email_recovery(app)

    def fail_delivery(_user, _raw_token):
        raise smtplib.SMTPException("test delivery failure")

    monkeypatch.setattr("app.routes.auth.send_password_reset_email", fail_delivery)
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "recovery-citizen@example.com"},
    )
    assert response.status_code == 202
    with app.app_context():
        reset_token = PasswordResetToken.query.one()
        assert reset_token.consumed_at is not None


def test_smtp_delivery_uses_tls_login_and_single_use_link(app, monkeypatch):
    _configure_email_recovery(app)
    app.config.update(SMTP_USERNAME="mailer", SMTP_PASSWORD="private-mail-password")
    recorded = {}

    class FakeSmtp:
        def __init__(self, **kwargs):
            recorded["connection"] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def starttls(self, context):
            recorded["tls"] = context is not None

        def login(self, username, password):
            recorded["login"] = (username, password)

        def send_message(self, message):
            recorded["message"] = message

    monkeypatch.setattr("app.services.email_service.smtplib.SMTP", FakeSmtp)
    with app.app_context():
        send_password_reset_email(
            SimpleNamespace(name="Recovery Citizen", email="recovery-citizen@example.com"),
            "private-single-use-token",
        )

    assert recorded["connection"] == {
        "host": "smtp.example",
        "port": 587,
        "timeout": 3,
    }
    assert recorded["tls"] is True
    assert recorded["login"] == ("mailer", "private-mail-password")
    assert recorded["message"]["To"] == "recovery-citizen@example.com"
    assert "https://resq.example/?reset_token=private-single-use-token" in recorded["message"].get_content()
