"""Add authentication security tables and backfill existing accounts.

Revision ID: 20260721_02
Revises: 20260721_01
Create Date: 2026-07-21
"""

from alembic import op
import sqlalchemy as sa


revision = "20260721_02"
down_revision = "20260721_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "account_security",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("account_security", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_account_security_locked_until"), ["locked_until"], unique=False)
        batch_op.create_index(batch_op.f("ix_account_security_user_id"), ["user_id"], unique=True)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("outcome", sa.String(length=30), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("details", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("audit_events", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_audit_events_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_audit_events_event_type"), ["event_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_audit_events_outcome"), ["outcome"], unique=False)
        batch_op.create_index(batch_op.f("ix_audit_events_request_id"), ["request_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_audit_events_user_id"), ["user_id"], unique=False)

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("csrf_hash", sa.String(length=64), nullable=False),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idle_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("auth_sessions", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_auth_sessions_absolute_expires_at"), ["absolute_expires_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_auth_sessions_idle_expires_at"), ["idle_expires_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_auth_sessions_last_seen_at"), ["last_seen_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_auth_sessions_revoked_at"), ["revoked_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_auth_sessions_token_hash"), ["token_hash"], unique=True)
        batch_op.create_index(batch_op.f("ix_auth_sessions_user_id"), ["user_id"], unique=False)

    account_security = sa.table(
        "account_security",
        sa.column("user_id", sa.Integer()),
        sa.column("failed_login_attempts", sa.Integer()),
        sa.column("locked_until", sa.DateTime(timezone=True)),
        sa.column("last_login_at", sa.DateTime(timezone=True)),
        sa.column("password_changed_at", sa.DateTime(timezone=True)),
    )
    users = sa.table("users", sa.column("id", sa.Integer()))
    existing_security = sa.table("account_security", sa.column("user_id", sa.Integer()))
    select_accounts = sa.select(
        users.c.id,
        sa.literal(0),
        sa.null(),
        sa.null(),
        sa.func.now(),
    ).where(~sa.exists(sa.select(existing_security.c.user_id).where(existing_security.c.user_id == users.c.id)))
    op.execute(
        sa.insert(account_security).from_select(
            ["user_id", "failed_login_attempts", "locked_until", "last_login_at", "password_changed_at"],
            select_accounts,
        )
    )


def downgrade():
    with op.batch_alter_table("auth_sessions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_auth_sessions_user_id"))
        batch_op.drop_index(batch_op.f("ix_auth_sessions_token_hash"))
        batch_op.drop_index(batch_op.f("ix_auth_sessions_revoked_at"))
        batch_op.drop_index(batch_op.f("ix_auth_sessions_last_seen_at"))
        batch_op.drop_index(batch_op.f("ix_auth_sessions_idle_expires_at"))
        batch_op.drop_index(batch_op.f("ix_auth_sessions_absolute_expires_at"))
    op.drop_table("auth_sessions")

    with op.batch_alter_table("audit_events", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_audit_events_user_id"))
        batch_op.drop_index(batch_op.f("ix_audit_events_request_id"))
        batch_op.drop_index(batch_op.f("ix_audit_events_outcome"))
        batch_op.drop_index(batch_op.f("ix_audit_events_event_type"))
        batch_op.drop_index(batch_op.f("ix_audit_events_created_at"))
    op.drop_table("audit_events")

    with op.batch_alter_table("account_security", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_account_security_user_id"))
        batch_op.drop_index(batch_op.f("ix_account_security_locked_until"))
    op.drop_table("account_security")
