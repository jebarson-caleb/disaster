import pytest

from app import create_app
from app.extensions import db
from app.seed import seed_demo_data


class TestConfig:
    SECRET_KEY = "test-secret"
    JWT_SECRET_KEY = "test-jwt-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = "*"
    OLLAMA_BASE_URL = ""
    OLLAMA_MODEL = "llama3.1"
    DEMO_MODE = True


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
