from conftest import TestConfig
from flask_migrate import upgrade
from sqlalchemy import inspect, text

from app import create_app
from app.bootstrap import (
    BASELINE_REVISION,
    HEAD_REVISION,
    MFA_REVISION,
    MIGRATIONS_DIRECTORY,
    SECURITY_REVISION,
    initialize_database,
)
from app.extensions import db
from app.models import AccountSecurity, User


def build_migration_app(database_path):
    class MigrationTestConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{database_path.as_posix()}"
        DEMO_MODE = False
        AUTO_MIGRATE = True
        BOOTSTRAP_ADMIN_EMAIL = ""
        BOOTSTRAP_ADMIN_PASSWORD = ""

    return create_app(MigrationTestConfig)


def current_revision():
    return db.session.execute(text("SELECT version_num FROM alembic_version")).scalar_one()


def test_fresh_database_migrates_to_head_and_is_idempotent(tmp_path):
    application = build_migration_app(tmp_path / "fresh.db")
    with application.app_context():
        initialize_database()
        initialize_database()

        tables = set(inspect(db.engine).get_table_names())
        assert {"users", "account_security", "auth_sessions", "audit_events", "alembic_version"} <= tables
        assert "must_change_password" in {
            column["name"] for column in inspect(db.engine).get_columns("account_security")
        }
        assert {"hospital_id", "shelter_id", "ambulance_id"} <= {
            column["name"] for column in inspect(db.engine).get_columns("role_profiles")
        }
        assert current_revision() == HEAD_REVISION
        db.session.remove()
        db.engine.dispose()


def test_unversioned_legacy_database_is_stamped_upgraded_and_preserved(tmp_path):
    application = build_migration_app(tmp_path / "legacy.db")
    with application.app_context():
        upgrade(directory=str(MIGRATIONS_DIRECTORY), revision=BASELINE_REVISION)
        legacy_user = User(
            name="Existing Operator",
            email="existing@example.com",
            phone="9000000000",
            role="Citizen",
            password_hash="legacy-password-hash",
        )
        db.session.add(legacy_user)
        db.session.commit()
        legacy_user_id = legacy_user.id
        db.session.execute(text("DROP TABLE alembic_version"))
        db.session.commit()

        initialize_database()

        assert current_revision() == HEAD_REVISION
        assert db.session.get(User, legacy_user_id).email == "existing@example.com"
        assert AccountSecurity.query.filter_by(user_id=legacy_user_id).one().failed_login_attempts == 0
        db.session.remove()
        db.engine.dispose()


def test_unversioned_current_schema_is_adopted_without_recreating_tables(tmp_path):
    application = build_migration_app(tmp_path / "current.db")
    with application.app_context():
        db.create_all()
        user = User(
            name="Current Operator",
            email="current@example.com",
            phone="9000000001",
            role="Admin",
            password_hash="current-password-hash",
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        initialize_database()

        assert current_revision() == HEAD_REVISION
        assert db.session.get(User, user_id).email == "current@example.com"
        db.session.remove()
        db.engine.dispose()


def test_unversioned_security_release_upgrades_to_mfa_schema(tmp_path):
    application = build_migration_app(tmp_path / "security-release.db")
    with application.app_context():
        upgrade(directory=str(MIGRATIONS_DIRECTORY), revision=SECURITY_REVISION)
        existing_user = User(
            name="Existing Administrator",
            email="security-release@example.com",
            phone="9000000002",
            role="Admin",
            password_hash="existing-password-hash",
        )
        db.session.add(existing_user)
        db.session.commit()
        existing_user_id = existing_user.id
        db.session.execute(text("DROP TABLE alembic_version"))
        db.session.commit()

        initialize_database()

        tables = set(inspect(db.engine).get_table_names())
        assert {"mfa_credentials", "mfa_challenges"} <= tables
        assert "mfa_state" in {column["name"] for column in inspect(db.engine).get_columns("auth_sessions")}
        assert "must_change_password" in {
            column["name"] for column in inspect(db.engine).get_columns("account_security")
        }
        assert current_revision() == HEAD_REVISION
        assert db.session.get(User, existing_user_id).email == "security-release@example.com"
        db.session.remove()
        db.engine.dispose()


def test_unversioned_mfa_release_upgrades_to_secure_onboarding_schema(tmp_path):
    application = build_migration_app(tmp_path / "mfa-release.db")
    with application.app_context():
        upgrade(directory=str(MIGRATIONS_DIRECTORY), revision=MFA_REVISION)
        db.session.execute(text("DROP TABLE alembic_version"))
        db.session.commit()

        initialize_database()

        assert "must_change_password" in {
            column["name"] for column in inspect(db.engine).get_columns("account_security")
        }
        assert {"hospital_id", "shelter_id", "ambulance_id"} <= {
            column["name"] for column in inspect(db.engine).get_columns("role_profiles")
        }
        assert current_revision() == HEAD_REVISION
        db.session.remove()
        db.engine.dispose()
