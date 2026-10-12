"""Rebuild the isolated public demo database from migrations and synthetic seed data."""

import json
import os
import sys
from urllib.parse import unquote, urlsplit

from sqlalchemy import MetaData

from app import create_app
from app.bootstrap import apply_schema_migrations
from app.config import Config, production_configuration_issues
from app.extensions import db
from app.models import User
from app.seed import seed_demo_data

RESET_CONFIRMATION = "RESET_DEMO_DATABASE"


def validate_reset_target(config, confirmation, allow_sqlite=False):
    issues = []
    if config.get("APP_ENV") != "demo":
        issues.append("APP_ENV must be demo")
    if not config.get("DEMO_MODE"):
        issues.append("DEMO_MODE must be enabled")
    if confirmation != RESET_CONFIRMATION:
        issues.append("DEMO_RESET_CONFIRMATION must match RESET_DEMO_DATABASE")

    database_uri = str(config.get("SQLALCHEMY_DATABASE_URI") or "")
    if allow_sqlite and database_uri.startswith("sqlite:"):
        deployment_issues = production_configuration_issues(config)
        issues.extend(
            issue
            for issue in deployment_issues
            if "persistent MySQL or PostgreSQL storage" not in issue
        )
    else:
        issues.extend(production_configuration_issues(config))
        if not database_uri.startswith(("postgresql+psycopg://", "mysql+pymysql://")):
            issues.append("Demo reset requires a dedicated persistent MySQL or PostgreSQL database")
        else:
            configured_database_name = str(config.get("DEMO_DATABASE_NAME") or "").strip()
            database_name = unquote(urlsplit(database_uri).path.lstrip("/"))
            if not configured_database_name:
                issues.append("DEMO_DATABASE_NAME must be configured for the destructive reset")
            elif "demo" not in configured_database_name.lower() or database_name != configured_database_name:
                issues.append("DATABASE_URL name must exactly match DEMO_DATABASE_NAME and include demo")
    return list(dict.fromkeys(issues))


def reset_demo_database(app=None, confirmation=None):
    app = app or create_app(Config)
    issues = validate_reset_target(
        app.config,
        confirmation if confirmation is not None else os.getenv("DEMO_RESET_CONFIRMATION", ""),
        allow_sqlite=bool(app.testing),
    )
    if issues:
        raise RuntimeError("Demo database reset refused: " + "; ".join(issues))

    with app.app_context():
        db.session.remove()
        reflected_metadata = MetaData()
        reflected_metadata.reflect(bind=db.engine)
        reflected_metadata.drop_all(bind=db.engine)
        apply_schema_migrations()
        seed_demo_data()
        return {"status": "reset", "seeded_users": User.query.count()}


def main():
    try:
        result = reset_demo_database()
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
