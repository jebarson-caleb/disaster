from app.config import production_configuration_issues
from app.extensions import db
from app.seed import seed_demo_data


STRONG_PASSWORD = "Correct-Horse-Battery-47"


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
        MFA_ENCRYPTION_KEY="",
        MFA_REQUIRED_ROLES=set(),
    )
    issues = production_configuration_issues(unsafe_production)
    assert len(issues) >= 6
    assert any("persistent MySQL or PostgreSQL" in issue for issue in issues)
    assert any("DEMO_MODE" in issue for issue in issues)
    assert any("MFA_ENCRYPTION_KEY" in issue for issue in issues)
    assert any("MFA_REQUIRED_ROLES" in issue for issue in issues)

    safe_production = dict(app.config)
    safe_production.update(
        APP_ENV="production",
        SQLALCHEMY_DATABASE_URI="postgresql+psycopg://resq:secret@db.example/resq?sslmode=require",
        SECRET_KEY="a" * 64,
        JWT_SECRET_KEY="b" * 64,
        MFA_ENCRYPTION_KEY="vcj-xKSir33ctWSpSznDQCuve0mHFAtAANrhMecuK-A=",
        MFA_REQUIRED_ROLES={"Admin", "Police"},
        DEMO_MODE=False,
        AUTO_MIGRATE=True,
        SESSION_COOKIE_SECURE=True,
        CORS_ORIGINS=[],
        BOOTSTRAP_ADMIN_EMAIL="admin@example.com",
        BOOTSTRAP_ADMIN_PASSWORD="Production-Admin-Password-77",
    )
    assert production_configuration_issues(safe_production) == []


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
