import pytest

from app import create_app
from app.config import Config
from app.extensions import db
from app.seed import seed_demo_data


class TestConfig(Config):
    TESTING = True
    APP_ENV = "testing"
    SECRET_KEY = "test-secret"
    JWT_SECRET_KEY = "test-jwt-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = ["http://localhost:5173"]
    OLLAMA_BASE_URL = ""
    OLLAMA_MODEL = "llama3.1"
    DEMO_MODE = True
    AUTO_MIGRATE = True
    MFA_ENCRYPTION_KEY = "vcj-xKSir33ctWSpSznDQCuve0mHFAtAANrhMecuK-A="
    MFA_REQUIRED_ROLES = {"Admin", "Police", "Fire Service", "Hospital", "Ambulance", "Shelter", "NGO"}
    SESSION_COOKIE_SECURE = False
    SESSION_IDLE_MINUTES = 30
    SESSION_ABSOLUTE_HOURS = 12
    ACCESS_TOKEN_MINUTES = 15
    JWT_ISSUER = "resq-command-test"
    JWT_AUDIENCE = "resq-command-test-client"
    SESSION_COOKIE_NAME = "resq_session"
    CSRF_COOKIE_NAME = "resq_csrf"
    SESSION_COOKIE_SAMESITE = "Lax"
    RATELIMIT_ENABLED = False
    TRUST_PROXY_HEADERS = False


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers(client, app):
    with app.app_context():
        seed_demo_data()
    response = client.post("/api/v1/auth/demo-session", json={"role": "Admin"})
    token = response.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}
