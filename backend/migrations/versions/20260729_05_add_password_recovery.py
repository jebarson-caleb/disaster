"""Add expiring password-recovery tokens.

Revision ID: 20260729_05
Revises: 20260727_04
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260729_05"
down_revision = "20260727_04"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("password_reset_tokens", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_password_reset_tokens_consumed_at"),
            ["consumed_at"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_password_reset_tokens_expires_at"),
            ["expires_at"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_password_reset_tokens_token_hash"),
            ["token_hash"],
            unique=True,
        )
        batch_op.create_index(
            batch_op.f("ix_password_reset_tokens_user_id"),
            ["user_id"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("password_reset_tokens", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_password_reset_tokens_user_id"))
        batch_op.drop_index(batch_op.f("ix_password_reset_tokens_token_hash"))
        batch_op.drop_index(batch_op.f("ix_password_reset_tokens_expires_at"))
        batch_op.drop_index(batch_op.f("ix_password_reset_tokens_consumed_at"))
    op.drop_table("password_reset_tokens")
