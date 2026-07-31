import json
from pathlib import Path

from app.config import production_configuration_issues
from app.release import APPLICATION_VERSION


def test_health_exposes_public_release_provenance(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.get_json()
    frontend_package = json.loads(
        (Path(__file__).parents[2] / "frontend" / "package.json").read_text(encoding="utf-8")
    )
    assert payload == {
        "status": "ok",
        "service": "disaster-response-api",
        "version": APPLICATION_VERSION,
        "commit": None,
    }
    assert payload["version"] == frontend_package["version"]


def test_vercel_production_requires_git_release_provenance(app):
    production = dict(app.config)
    production.update(
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
        RUNNING_ON_VERCEL=True,
        RELEASE_COMMIT="",
    )

    issues = production_configuration_issues(production)
    assert any("release provenance" in issue for issue in issues)

    production["RELEASE_COMMIT"] = "a" * 40
    assert production_configuration_issues(production) == []
