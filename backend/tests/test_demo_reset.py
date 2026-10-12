from app.extensions import db
from app.models import Disaster, User
from scripts.reset_demo_database import RESET_CONFIRMATION, reset_demo_database, validate_reset_target


def configure_test_demo(app):
    app.config.update(
        APP_ENV="demo",
        DEMO_MODE=True,
        AUTO_MIGRATE=True,
        SECRET_KEY="c" * 64,
        JWT_SECRET_KEY="d" * 64,
        SESSION_COOKIE_SECURE=True,
        CORS_ORIGINS=[],
        BOOTSTRAP_ADMIN_EMAIL="",
        BOOTSTRAP_ADMIN_PASSWORD="",
        DEMO_DATABASE_NAME="",
        RATELIMIT_STORAGE_URI="rediss://cache.example/0",
        RUNNING_ON_VERCEL=False,
        ALERT_DELIVERY_WEBHOOK_URL="",
        ALERT_DELIVERY_WEBHOOK_SECRET="",
        DONATION_PAYMENT_URL="",
        OLLAMA_BASE_URL="",
        SMTP_HOST="",
        SMTP_USERNAME="",
        SMTP_PASSWORD="",
        SMTP_FROM_EMAIL="",
    )


def test_reset_refuses_production_or_missing_confirmation(app):
    config = dict(app.config)
    config.update(APP_ENV="production", DEMO_MODE=False)

    assert any("APP_ENV must be demo" in issue for issue in validate_reset_target(config, RESET_CONFIRMATION))
    assert any(
        "DEMO_RESET_CONFIRMATION" in issue
        for issue in validate_reset_target({**app.config, "APP_ENV": "demo", "DEMO_MODE": True}, "")
    )


def test_demo_database_reset_rebuilds_migrated_seed_data(app):
    configure_test_demo(app)
    with app.app_context():
        db.create_all()
        db.session.add(
            User(
                name="Temporary record",
                email="temp@example.invalid",
                phone="0",
                role="Citizen",
                password_hash="test-only-hash",
            )
        )
        db.session.commit()

    result = reset_demo_database(app, confirmation=RESET_CONFIRMATION)

    assert result == {"status": "reset", "seeded_users": 9}
    with app.app_context():
        assert User.query.count() == 9
        assert User.query.filter_by(email="temp@example.invalid").first() is None
        assert Disaster.query.count() > 0


def test_hosted_reset_requires_an_explicit_demo_database_name(app):
    configure_test_demo(app)
    config = {
        **app.config,
        "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://demo:secret@db.example/resq_demo?sslmode=require",
        "DEMO_DATABASE_NAME": "resq_demo",
    }

    assert validate_reset_target(config, RESET_CONFIRMATION) == []
    config["DEMO_DATABASE_NAME"] = "resq_production"
    assert any("exactly match DEMO_DATABASE_NAME" in issue for issue in validate_reset_target(config, RESET_CONFIRMATION))
