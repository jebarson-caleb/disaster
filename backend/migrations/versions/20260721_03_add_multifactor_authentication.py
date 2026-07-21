"""Add multi-factor authentication credentials and challenges.

Revision ID: 20260721_03
Revises: 20260721_02
Create Date: 2026-07-21
"""

from alembic import op
import sqlalchemy as sa


revision = "20260721_03"
down_revision = "20260721_02"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("auth_sessions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("mfa_state", sa.String(length=30), server_default="not_required", nullable=False))
        batch_op.create_index(batch_op.f("ix_auth_sessions_mfa_state"), ["mfa_state"], unique=False)

    op.execute(
        sa.text(
            "UPDATE auth_sessions SET mfa_state = 'setup_required' "
            "WHERE user_id IN (SELECT id FROM users WHERE role IN "
            "('Admin', 'Police', 'Fire Service', 'Hospital', 'Ambulance', 'Shelter', 'NGO'))"
        )
    )

    op.create_table(
        "mfa_credentials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("secret_ciphertext", sa.String(length=500), nullable=False),
        sa.Column("recovery_code_hashes", sa.Text(), nullable=False),
        sa.Column("enabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_step", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("mfa_credentials", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_mfa_credentials_enabled_at"), ["enabled_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_mfa_credentials_user_id"), ["user_id"], unique=True)

    op.create_table(
        "mfa_challenges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_attempts", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("mfa_challenges", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_mfa_challenges_consumed_at"), ["consumed_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_mfa_challenges_expires_at"), ["expires_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_mfa_challenges_token_hash"), ["token_hash"], unique=True)
        batch_op.create_index(batch_op.f("ix_mfa_challenges_user_id"), ["user_id"], unique=False)


def downgrade():
    with op.batch_alter_table("mfa_challenges", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_mfa_challenges_user_id"))
        batch_op.drop_index(batch_op.f("ix_mfa_challenges_token_hash"))
        batch_op.drop_index(batch_op.f("ix_mfa_challenges_expires_at"))
        batch_op.drop_index(batch_op.f("ix_mfa_challenges_consumed_at"))
    op.drop_table("mfa_challenges")

    with op.batch_alter_table("mfa_credentials", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_mfa_credentials_user_id"))
        batch_op.drop_index(batch_op.f("ix_mfa_credentials_enabled_at"))
    op.drop_table("mfa_credentials")

    with op.batch_alter_table("auth_sessions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_auth_sessions_mfa_state"))
        batch_op.drop_column("mfa_state")
