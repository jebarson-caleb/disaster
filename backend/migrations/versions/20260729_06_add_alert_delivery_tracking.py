"""Add outbound public-warning delivery tracking.

Revision ID: 20260729_06
Revises: 20260729_05
Create Date: 2026-07-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260729_06"
down_revision = "20260729_05"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("emergency_alerts", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "delivery_status",
                sa.String(length=30),
                server_default="not_configured",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "delivery_attempts",
                sa.Integer(),
                server_default=sa.text("0"),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("delivery_status_code", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("delivery_attempted_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_emergency_alerts_delivery_status"),
            ["delivery_status"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("emergency_alerts", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_emergency_alerts_delivery_status"))
        batch_op.drop_column("delivery_attempted_at")
        batch_op.drop_column("delivery_status_code")
        batch_op.drop_column("delivery_attempts")
        batch_op.drop_column("delivery_status")
