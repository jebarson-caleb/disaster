"""Add department road-access and readiness-checklist records.

Revision ID: 20261022_08
Revises: 20260905_07
Create Date: 2026-10-22
"""

from alembic import op
import sqlalchemy as sa


revision = "20261022_08"
down_revision = "20260905_07"
branch_labels = None
depends_on = None


def upgrade():
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "road_closures" not in existing_tables:
        _create_road_closures()
    if "readiness_checks" not in existing_tables:
        _create_readiness_checks()


def _create_road_closures():
    op.create_table(
        "road_closures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("disaster_id", sa.Integer(), nullable=True),
        sa.Column("road_name", sa.String(length=160), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("diversion", sa.String(length=255), nullable=True),
        sa.Column("reported_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["disaster_id"], ["disasters.id"]),
        sa.ForeignKeyConstraint(["reported_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("road_closures", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_road_closures_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_road_closures_disaster_id"), ["disaster_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_road_closures_status"), ["status"], unique=False)


def _create_readiness_checks():
    op.create_table(
        "readiness_checks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("subject", sa.String(length=160), nullable=False),
        sa.Column("items", sa.Text(), nullable=False),
        sa.Column("ready_count", sa.Integer(), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("readiness_checks", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_readiness_checks_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_readiness_checks_role"), ["role"], unique=False)
        batch_op.create_index(batch_op.f("ix_readiness_checks_user_id"), ["user_id"], unique=False)


def downgrade():
    with op.batch_alter_table("readiness_checks", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_readiness_checks_user_id"))
        batch_op.drop_index(batch_op.f("ix_readiness_checks_role"))
        batch_op.drop_index(batch_op.f("ix_readiness_checks_created_at"))
    op.drop_table("readiness_checks")

    with op.batch_alter_table("road_closures", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_road_closures_status"))
        batch_op.drop_index(batch_op.f("ix_road_closures_disaster_id"))
        batch_op.drop_index(batch_op.f("ix_road_closures_created_at"))
    op.drop_table("road_closures")
