import time

import pyotp

from app.models import MfaCredential
from app.seed import seed_demo_data


def csrf_headers(client):
    return {"X-CSRF-Token": client.get_cookie("resq_csrf").value}


def test_privileged_account_enrollment_totp_login_and_recovery(client, app):
    with app.app_context():
        seed_demo_data()

    password_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@rescue.local", "password": "DemoPassword123!"},
    )
    assert password_login.status_code == 200
    assert password_login.get_json()["mfa_setup_required"] is True

    blocked = client.get("/api/v1/admin/users")
    assert blocked.status_code == 403
    assert blocked.get_json()["code"] == "mfa_setup_required"

    setup = client.post(
        "/api/v1/auth/mfa/setup",
        json={"current_password": "DemoPassword123!"},
        headers=csrf_headers(client),
    )
    assert setup.status_code == 200
    secret = setup.get_json()["secret"]
    assert setup.get_json()["provisioning_uri"].startswith("otpauth://totp/")
    with app.app_context():
        stored = MfaCredential.query.one()
        assert secret not in stored.secret_ciphertext
        assert stored.enabled_at is None

    confirmation_code = pyotp.TOTP(secret).now()
    confirmed = client.post(
        "/api/v1/auth/mfa/confirm",
        json={"code": confirmation_code},
        headers=csrf_headers(client),
    )
    assert confirmed.status_code == 200
    recovery_codes = confirmed.get_json()["recovery_codes"]
    assert len(recovery_codes) == 10
    assert client.get("/api/v1/admin/users").status_code == 200

    assert client.post("/api/v1/auth/logout", json={}, headers=csrf_headers(client)).status_code == 200
    challenged = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@rescue.local", "password": "DemoPassword123!"},
    )
    assert challenged.status_code == 202
    challenge_token = challenged.get_json()["challenge_token"]
    next_totp = pyotp.TOTP(secret).at(time.time() + 30)
    completed = client.post(
        "/api/v1/auth/mfa/challenge",
        json={"challenge_token": challenge_token, "code": next_totp},
    )
    assert completed.status_code == 200
    assert completed.get_json()["mfa_verified"] is True

    replay = client.post(
        "/api/v1/auth/mfa/challenge",
        json={"challenge_token": challenge_token, "code": recovery_codes[0]},
    )
    assert replay.status_code == 401

    assert client.post("/api/v1/auth/logout", json={}, headers=csrf_headers(client)).status_code == 200
    recovery_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@rescue.local", "password": "DemoPassword123!"},
    ).get_json()
    recovered = client.post(
        "/api/v1/auth/mfa/challenge",
        json={"challenge_token": recovery_login["challenge_token"], "code": recovery_codes[0]},
    )
    assert recovered.status_code == 200
    status = client.get("/api/v1/auth/mfa/status").get_json()
    assert status["enabled"] is True
    assert status["recovery_codes_remaining"] == 9


def test_citizen_account_does_not_require_mfa_enrollment(client):
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "name": "MFA Optional Citizen",
            "email": "mfa-citizen@example.com",
            "phone": "9000000999",
            "role": "Citizen",
            "password": "Correct-Horse-Battery-99",
        },
    )
    assert registered.status_code == 201
    assert registered.get_json()["mfa_setup_required"] is False
    assert client.get("/api/v1/auth/mfa/status").get_json()["required"] is False
