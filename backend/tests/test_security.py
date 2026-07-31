from datetime import timedelta
from types import SimpleNamespace

from flask import request

from app.auth import authenticated_rate_key, utcnow
from app.config import production_configuration_issues
from app.extensions import db
from app.models import AuthSession
from app.seed import seed_demo_data

STRONG_PASSWORD = "Correct-Horse-Battery-47"


def test_authenticated_rate_limits_are_isolated_per_account(app):
    with app.test_request_context("/", environ_base={"REMOTE_ADDR": "203.0.113.17"}):
        assert authenticated_rate_key() == "ip:203.0.113.17"
        request.user = SimpleNamespace(id=42)
        assert authenticated_rate_key() == "user:42"
        request.user = SimpleNamespace(id=84)
        assert authenticated_rate_key() == "user:84"


def test_cookie_session_csrf_logout_and_security_headers(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Beta Citizen",
            "email": "beta@example.com",
            "phone": "9000000123",
            "role": "Citizen",
            "password": STRONG_PASSWORD,
        },
        headers={"X-Request-ID": "beta-security-test-001"},
    )
    assert response.status_code == 201
    cookies = response.headers.getlist("Set-Cookie")
    assert any("resq_session=" in item and "HttpOnly" in item and "SameSite=Lax" in item for item in cookies)
    assert any("resq_csrf=" in item and "HttpOnly" not in item for item in cookies)
    assert response.headers["X-Request-ID"] == "beta-security-test-001"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Cache-Control"] == "no-store"

    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.post("/api/v1/auth/logout", json={}).status_code == 403
    csrf = client.get_cookie("resq_csrf").value
    logout = client.post("/api/v1/auth/logout", json={}, headers={"X-CSRF-Token": csrf})
    assert logout.status_code == 200
    assert '"storage"' in logout.headers["Clear-Site-Data"]
    assert client.get("/api/v1/auth/me").status_code == 401


def test_api_rejects_non_object_json_without_server_error(client):
    response = client.post(
        "/api/v1/auth/login",
        json=["not", "an", "object"],
        headers={"X-Request-ID": "invalid-json-shape-001"},
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "JSON request body must be an object"}
    assert response.headers["X-Request-ID"] == "invalid-json-shape-001"


def test_password_policy_and_account_lockout(client, app):
    weak = client.post(
        "/api/v1/auth/register",
        json={"name": "Weak", "email": "weak@example.com", "phone": "1", "role": "Citizen", "password": "password123"},
    )
    assert weak.status_code == 400

    with app.app_context():
        seed_demo_data()
    for _ in range(5):
        failure = client.post("/api/v1/auth/login", json={"email": "admin@rescue.local", "password": "wrong-password-value"})
        assert failure.status_code == 401
    locked = client.post("/api/v1/auth/login", json={"email": "admin@rescue.local", "password": "DemoPassword123!"})
    assert locked.status_code == 429


def test_readiness_and_production_configuration_gate(client, app):
    with app.app_context():
        db.create_all()
        assert production_configuration_issues(app.config) == []
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.get_json()["checks"] == {"configuration": True, "database": True}

    unsafe_production = dict(app.config)
    unsafe_production.update(
        APP_ENV="production",
        SQLALCHEMY_DATABASE_URI="sqlite:////tmp/disaster.db",
        SECRET_KEY="dev-secret-change-before-production",
        JWT_SECRET_KEY="dev-secret-change-before-production",
        DEMO_MODE=True,
        SESSION_COOKIE_SECURE=False,
        RATELIMIT_STORAGE_URI="memory://",
        BOOTSTRAP_ADMIN_EMAIL="",
        BOOTSTRAP_ADMIN_PASSWORD="",
    )
    issues = production_configuration_issues(unsafe_production)
    assert len(issues) >= 6
    assert any("persistent MySQL or PostgreSQL" in issue for issue in issues)
    assert any("DEMO_MODE" in issue for issue in issues)

    safe_production = dict(app.config)
    safe_production.update(
        APP_ENV="production",
        SQLALCHEMY_DATABASE_URI="postgresql+psycopg://resq:secret@db.example/resq?sslmode=require",
        SECRET_KEY="a" * 64,
        JWT_SECRET_KEY="b" * 64,
        DEMO_MODE=False,
        AUTO_MIGRATE=True,
        SESSION_COOKIE_SECURE=True,
        CORS_ORIGINS=[],
        BOOTSTRAP_ADMIN_EMAIL="admin@example.com",
        BOOTSTRAP_ADMIN_PASSWORD="Production-Admin-Password-77",
    )
    assert production_configuration_issues(safe_production) == []


def test_optional_integration_configuration_is_fail_closed(app):
    base = dict(app.config)
    base.update(
        APP_ENV="production",
        SQLALCHEMY_DATABASE_URI="postgresql+psycopg://resq:secret@db.example/resq?sslmode=require",
        SECRET_KEY="a" * 64,
        JWT_SECRET_KEY="b" * 64,
        DEMO_MODE=False,
        AUTO_MIGRATE=True,
        SESSION_COOKIE_SECURE=True,
        CORS_ORIGINS=[],
        BOOTSTRAP_ADMIN_EMAIL="admin@example.com",
        BOOTSTRAP_ADMIN_PASSWORD="Production-Admin-Password-77",
    )
    invalid = {
        **base,
        "DONATION_PAYMENT_URL": "http://payments.example/checkout",
        "ALERT_DELIVERY_WEBHOOK_URL": "https://alerts.example/provider?token=unsafe",
        "ALERT_DELIVERY_WEBHOOK_SECRET": "short",
        "ALERT_DELIVERY_TIMEOUT_SECONDS": 0,
        "OLLAMA_BASE_URL": "file:///private/model",
        "RATELIMIT_STORAGE_URI": "redis://redis.example/0",
        "SMTP_HOST": "smtp.example",
        "SMTP_FROM_EMAIL": "",
        "SMTP_USERNAME": "mailer",
        "SMTP_PASSWORD": "",
        "SMTP_USE_TLS": True,
        "SMTP_USE_SSL": True,
        "SMTP_PORT": 0,
        "SMTP_TIMEOUT_SECONDS": 0,
        "PUBLIC_BASE_URL": "http://resq.example/?source=unsafe",
        "PASSWORD_RESET_MINUTES": 2,
    }
    issues = production_configuration_issues(invalid)
    assert any("DONATION_PAYMENT_URL" in issue for issue in issues)
    assert any("ALERT_DELIVERY_WEBHOOK_URL" in issue for issue in issues)
    assert any("ALERT_DELIVERY_WEBHOOK_SECRET" in issue for issue in issues)
    assert any("ALERT_DELIVERY_TIMEOUT_SECONDS" in issue for issue in issues)
    assert any("OLLAMA_BASE_URL" in issue for issue in issues)
    assert any("RATELIMIT_STORAGE_URI" in issue for issue in issues)
    assert any("SMTP_HOST and SMTP_FROM_EMAIL" in issue for issue in issues)
    assert any("SMTP_USERNAME and SMTP_PASSWORD" in issue for issue in issues)
    assert any("cannot both" in issue for issue in issues)
    assert any("SMTP_PORT" in issue for issue in issues)
    assert any("SMTP_TIMEOUT_SECONDS" in issue for issue in issues)
    assert any("PUBLIC_BASE_URL" in issue for issue in issues)
    assert any("PASSWORD_RESET_MINUTES" in issue for issue in issues)

    configured = {
        **base,
        "DONATION_PAYMENT_URL": "https://payments.example/checkout",
        "ALERT_DELIVERY_WEBHOOK_URL": "https://alerts.example/provider",
        "ALERT_DELIVERY_WEBHOOK_SECRET": "approved-provider-webhook-secret-32-bytes",
        "ALERT_DELIVERY_TIMEOUT_SECONDS": 5,
        "OLLAMA_BASE_URL": "https://private-ai.example",
        "RATELIMIT_STORAGE_URI": "rediss://redis.example/0",
        "SMTP_HOST": "smtp.example",
        "SMTP_FROM_EMAIL": "security@resq.example",
        "SMTP_USERNAME": "mailer",
        "SMTP_PASSWORD": "private-mail-password",
        "SMTP_USE_TLS": True,
        "SMTP_USE_SSL": False,
        "SMTP_PORT": 587,
        "SMTP_TIMEOUT_SECONDS": 8,
        "PUBLIC_BASE_URL": "https://resq.example",
        "PASSWORD_RESET_MINUTES": 30,
    }
    assert production_configuration_issues(configured) == []

    invalid_sender = {**configured, "SMTP_FROM_EMAIL": "ResQ Security <security@resq.example>"}
    assert any("SMTP_FROM_EMAIL" in issue for issue in production_configuration_issues(invalid_sender))

    incomplete_webhook = {**configured, "ALERT_DELIVERY_WEBHOOK_SECRET": ""}
    assert any(
        "must be supplied together" in issue
        for issue in production_configuration_issues(incomplete_webhook)
    )


def test_password_change_revokes_previous_session(client):
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Credential Owner",
            "email": "credentials@example.com",
            "phone": "9000000444",
            "role": "Citizen",
            "password": STRONG_PASSWORD,
        },
    )
    old_token = registered.get_json()["token"]
    csrf = client.get_cookie("resq_csrf").value
    changed = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": STRONG_PASSWORD, "new_password": "New-Correct-Horse-Battery-48"},
        headers={"X-CSRF-Token": csrf},
    )
    assert changed.status_code == 200
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {old_token}"}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": "credentials@example.com", "password": STRONG_PASSWORD}).status_code == 401
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "credentials@example.com", "password": "New-Correct-Horse-Battery-48"},
    ).status_code == 200


def test_user_can_review_and_revoke_other_active_sessions(client, app):
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Session Owner",
            "email": "sessions@example.com",
            "phone": "9000000777",
            "role": "Citizen",
            "password": STRONG_PASSWORD,
        },
        headers={"User-Agent": "Primary acceptance browser"},
    )
    assert registered.status_code == 201

    other_client = app.test_client()
    other_login = other_client.post(
        "/api/v1/auth/login",
        json={"email": "sessions@example.com", "password": STRONG_PASSWORD},
        headers={"User-Agent": "Secondary acceptance browser"},
    )
    assert other_login.status_code == 200
    other_token = other_login.get_json()["token"]

    sessions = client.get("/api/v1/auth/sessions").get_json()["sessions"]
    assert len(sessions) == 2
    assert sum(item["current"] for item in sessions) == 1
    secondary = next(item for item in sessions if not item["current"])
    revoked = client.delete(
        f"/api/v1/auth/sessions/{secondary['id']}",
        headers={"X-CSRF-Token": client.get_cookie("resq_csrf").value},
    )
    assert revoked.status_code == 200
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {other_token}"}).status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 200


def test_revoking_current_session_clears_browser_state(client):
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Current Session Owner",
            "email": "current-session@example.com",
            "phone": "9000000778",
            "role": "Citizen",
            "password": STRONG_PASSWORD,
        },
    )
    assert registered.status_code == 201
    current = next(item for item in client.get("/api/v1/auth/sessions").get_json()["sessions"] if item["current"])

    revoked = client.delete(
        f"/api/v1/auth/sessions/{current['id']}",
        headers={"X-CSRF-Token": client.get_cookie("resq_csrf").value},
    )

    assert revoked.status_code == 200
    assert revoked.headers["Clear-Site-Data"] == '"cache", "cookies", "storage"'
    assert client.get("/api/v1/auth/me").status_code == 401


def test_idle_and_absolute_session_expiry_are_enforced(client, app):
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Expiring Session Owner",
            "email": "expiring-session@example.com",
            "phone": "9000000779",
            "role": "Citizen",
            "password": STRONG_PASSWORD,
        },
    )
    assert registered.status_code == 201
    with app.app_context():
        auth_session = AuthSession.query.filter_by(user_id=registered.get_json()["user"]["id"]).one()
        auth_session.idle_expires_at = utcnow() - timedelta(seconds=1)
        db.session.commit()
    assert client.get("/api/v1/auth/me").status_code == 401

    relogged = client.post(
        "/api/v1/auth/login",
        json={"email": "expiring-session@example.com", "password": STRONG_PASSWORD},
    )
    assert relogged.status_code == 200
    with app.app_context():
        auth_session = AuthSession.query.filter_by(
            user_id=relogged.get_json()["user"]["id"],
            revoked_at=None,
        ).order_by(AuthSession.id.desc()).first()
        auth_session.absolute_expires_at = utcnow() - timedelta(seconds=1)
        db.session.commit()
    assert client.get("/api/v1/auth/me").status_code == 401


def test_volunteer_requires_admin_verification(client, app):
    with app.app_context():
        seed_demo_data()
    pending = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Pending Volunteer",
            "email": "pending-volunteer@example.com",
            "phone": "9000000555",
            "role": "Volunteer",
            "password": STRONG_PASSWORD,
        },
    )
    assert pending.status_code == 202
    assert pending.get_json()["pending_verification"] is True
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "pending-volunteer@example.com", "password": STRONG_PASSWORD},
    ).status_code == 401
    admin_session = client.post("/api/v1/auth/demo-session", json={"role": "Admin"}).get_json()
    admin_headers = {"Authorization": f"Bearer {admin_session['token']}"}
    users = client.get("/api/v1/admin/users", headers=admin_headers).get_json()["users"]
    volunteer = next(user for user in users if user["email"] == "pending-volunteer@example.com")
    assert volunteer["verification_status"] == "pending"
    verified = client.patch(
        f"/api/v1/admin/users/{volunteer['id']}",
        headers=admin_headers,
        json={"verification_status": "verified"},
    )
    assert verified.status_code == 200
    assert verified.get_json()["user"]["is_active"] is True
    volunteer_login = client.post(
        "/api/v1/auth/login",
        json={"email": "pending-volunteer@example.com", "password": STRONG_PASSWORD},
    )
    assert volunteer_login.status_code == 200
    volunteer_token = volunteer_login.get_json()["token"]

    deactivated = client.patch(
        f"/api/v1/admin/users/{volunteer['id']}",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert deactivated.status_code == 200
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {volunteer_token}"}).status_code == 401
    assert client.patch(
        f"/api/v1/admin/users/{volunteer['id']}",
        headers=admin_headers,
        json={"is_active": True},
    ).status_code == 200

    reset = client.post(
        f"/api/v1/admin/users/{volunteer['id']}/reset-password",
        headers=admin_headers,
        json={"admin_password": "DemoPassword123!", "new_password": "Reset-Volunteer-Password-49"},
    )
    assert reset.status_code == 200
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "pending-volunteer@example.com", "password": STRONG_PASSWORD},
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/login",
        json={"email": "pending-volunteer@example.com", "password": "Reset-Volunteer-Password-49"},
    ).status_code == 200
