import pytest

from app import create_app
from app.extensions import db


class TestConfig:
    SECRET_KEY = "test-secret"
    JWT_SECRET_KEY = "test-jwt-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = "*"
    OLLAMA_BASE_URL = ""
    OLLAMA_MODEL = "llama3.1"


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
def auth_headers(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Admin",
            "email": "admin@test.local",
            "phone": "9000000000",
            "role": "Admin",
            "password": "password123",
        },
    )
    token = response.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}
