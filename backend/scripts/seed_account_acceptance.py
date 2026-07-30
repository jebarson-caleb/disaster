"""Seed role accounts only in an isolated SQLite acceptance environment."""

from app import create_app
from app.bootstrap import initialize_database
from app.extensions import db
from app.seed import seed_demo_data


def main():
    app = create_app()
    database_uri = str(app.config.get("SQLALCHEMY_DATABASE_URI") or "")
    if app.config.get("APP_ENV") != "testing":
        raise RuntimeError("account acceptance fixtures require APP_ENV=testing")
    if app.config.get("DEMO_MODE"):
        raise RuntimeError("account acceptance must exercise the backend with DEMO_MODE=false")
    if not database_uri.startswith("sqlite:///") or "account-acceptance" not in database_uri:
        raise RuntimeError("account acceptance fixtures require a dedicated SQLite database")

    with app.app_context():
        if db.engine.dialect.name != "sqlite":
            raise RuntimeError("account acceptance fixtures refuse non-SQLite databases")
        initialize_database()
        seed_demo_data()
        print("Seeded isolated account acceptance fixtures.")


if __name__ == "__main__":
    main()
