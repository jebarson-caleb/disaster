from contextlib import contextmanager
from pathlib import Path

from flask import current_app
from flask_migrate import stamp, upgrade
from sqlalchemy import inspect, text

from .auth import hash_password, validate_password
from .extensions import db
from .models import AccountSecurity, RoleProfile, User
from .seed import seed_demo_data

MIGRATIONS_DIRECTORY = Path(__file__).resolve().parents[1] / "migrations"
BASELINE_REVISION = "20260721_01"
SECURITY_REVISION = "20260721_02"
MFA_REVISION = "20260721_03"
ONBOARDING_REVISION = "20260727_04"
HEAD_REVISION = "20260729_05"
SECURITY_TABLES = {"account_security", "audit_events", "auth_sessions"}
MFA_TABLES = {"mfa_credentials", "mfa_challenges"}
RECOVERY_TABLES = {"password_reset_tokens"}
POST_BASELINE_TABLES = SECURITY_TABLES | MFA_TABLES | RECOVERY_TABLES
POSTGRESQL_MIGRATION_LOCK_ID = int.from_bytes(b"RSQC", byteorder="big")
MYSQL_MIGRATION_LOCK_NAME = "resq_command_schema_migration"


@contextmanager
def migration_lock():
    """Serialize startup migrations on supported production databases."""
    dialect = db.engine.dialect.name
    if dialect not in {"postgresql", "mysql"}:
        yield
        return

    with db.engine.connect() as connection:
        if dialect == "postgresql":
            connection.execute(
                text("SELECT pg_advisory_lock(:lock_id)"),
                {"lock_id": POSTGRESQL_MIGRATION_LOCK_ID},
            )
        else:
            acquired = connection.execute(
                text("SELECT GET_LOCK(:lock_name, 60)"),
                {"lock_name": MYSQL_MIGRATION_LOCK_NAME},
            ).scalar()
            if acquired != 1:
                raise RuntimeError("Timed out waiting for the database migration lock")

        try:
            yield
        finally:
            if dialect == "postgresql":
                connection.execute(
                    text("SELECT pg_advisory_unlock(:lock_id)"),
                    {"lock_id": POSTGRESQL_MIGRATION_LOCK_ID},
                )
            else:
                connection.execute(
                    text("SELECT RELEASE_LOCK(:lock_name)"),
                    {"lock_name": MYSQL_MIGRATION_LOCK_NAME},
                )


def apply_schema_migrations():
    """Upgrade a fresh or legacy database to the checked-in migration head."""
    migration_directory = str(MIGRATIONS_DIRECTORY)
    with migration_lock():
        table_names = set(inspect(db.engine).get_table_names())
        if "alembic_version" not in table_names:
            model_tables = set(db.metadata.tables)
            baseline_tables = model_tables - POST_BASELINE_TABLES
            existing_model_tables = table_names & model_tables

            if existing_model_tables:
                missing_baseline = baseline_tables - table_names
                existing_security = SECURITY_TABLES & table_names
                existing_mfa = MFA_TABLES & table_names
                existing_recovery = RECOVERY_TABLES & table_names
                if missing_baseline:
                    missing = ", ".join(sorted(missing_baseline))
                    raise RuntimeError(
                        "The existing unversioned database does not match the supported legacy schema; "
                        f"missing tables: {missing}"
                    )
                if existing_security and existing_security != SECURITY_TABLES:
                    partial = ", ".join(sorted(existing_security))
                    raise RuntimeError(
                        "The existing unversioned database has a partial security schema; "
                        f"found: {partial}"
                    )
                if existing_mfa and existing_mfa != MFA_TABLES:
                    partial = ", ".join(sorted(existing_mfa))
                    raise RuntimeError(
                        "The existing unversioned database has a partial MFA schema; "
                        f"found: {partial}"
                    )
                if existing_mfa and existing_security != SECURITY_TABLES:
                    raise RuntimeError("The existing unversioned database has MFA tables without the security schema")
                if existing_recovery and existing_mfa != MFA_TABLES:
                    raise RuntimeError("The existing unversioned database has recovery tables without the MFA schema")

                if existing_mfa == MFA_TABLES:
                    auth_session_columns = {
                        column["name"] for column in inspect(db.engine).get_columns("auth_sessions")
                    }
                    if "mfa_state" not in auth_session_columns:
                        raise RuntimeError("The existing unversioned database has MFA tables but no session MFA state")
                    account_security_columns = {
                        column["name"] for column in inspect(db.engine).get_columns("account_security")
                    }
                    role_profile_columns = {
                        column["name"] for column in inspect(db.engine).get_columns("role_profiles")
                    }
                    onboarding_columns_present = (
                        "must_change_password" in account_security_columns
                        and {"hospital_id", "shelter_id", "ambulance_id"} <= role_profile_columns
                    )
                    if onboarding_columns_present:
                        legacy_revision = HEAD_REVISION if existing_recovery else ONBOARDING_REVISION
                    else:
                        legacy_revision = MFA_REVISION
                elif existing_security == SECURITY_TABLES:
                    legacy_revision = SECURITY_REVISION
                else:
                    legacy_revision = BASELINE_REVISION
                current_app.logger.info("Stamping legacy database at schema revision %s", legacy_revision)
                stamp(directory=migration_directory, revision=legacy_revision)

        upgrade(directory=migration_directory, revision="head")
        current_app.logger.info("Database schema is current at revision %s", HEAD_REVISION)


def initialize_database():
    """Apply schema migrations and provision only explicitly requested data."""
    if current_app.config.get("AUTO_MIGRATE", True):
        apply_schema_migrations()
    else:
        current_app.logger.info("Automatic schema migration is disabled")
    if current_app.config.get("DEMO_MODE"):
        seed_demo_data()
        return
    bootstrap_admin()


def bootstrap_admin():
    email = current_app.config.get("BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
    password = current_app.config.get("BOOTSTRAP_ADMIN_PASSWORD", "")
    if not email or not password or User.query.filter_by(email=email).first():
        return
    password_error = validate_password(password)
    if password_error:
        current_app.logger.error("Bootstrap administrator was not created: %s", password_error)
        return
    user = User(
        name=current_app.config.get("BOOTSTRAP_ADMIN_NAME", "Incident Commander")[:120],
        email=email,
        phone=current_app.config.get("BOOTSTRAP_ADMIN_PHONE", "")[:30] or "Not provided",
        role="Admin",
        password_hash=hash_password(password),
    )
    db.session.add(user)
    db.session.flush()
    db.session.add_all(
        [
            RoleProfile(user_id=user.id, organization_name="Emergency Operations", verification_status="verified"),
            AccountSecurity(user_id=user.id, must_change_password=True),
        ]
    )
    db.session.commit()
    current_app.logger.info("Bootstrap administrator created for %s", email)
