"""Secure temporary passwords and link operational accounts to managed assets.

Revision ID: 20260727_04
Revises: 20260721_03
Create Date: 2026-07-27
"""

from alembic import op
import sqlalchemy as sa


revision = "20260727_04"
down_revision = "20260721_03"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("account_security", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("must_change_password", sa.Boolean(), server_default=sa.false(), nullable=False)
        )

    # Existing administrator credentials pre-date the temporary-password gate.
    # Requiring one deliberate rotation is safer than assuming they were delivered
    # and changed through a secure channel.
    op.execute(
        sa.text(
            "UPDATE account_security SET must_change_password = true "
            "WHERE user_id IN (SELECT id FROM users WHERE role = 'Admin')"
        )
    )

    with op.batch_alter_table("role_profiles", schema=None) as batch_op:
        batch_op.add_column(sa.Column("hospital_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("shelter_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("ambulance_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_role_profiles_hospital_id_hospitals",
            "hospitals",
            ["hospital_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_role_profiles_shelter_id_shelters",
            "shelters",
            ["shelter_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_role_profiles_ambulance_id_ambulances",
            "ambulances",
            ["ambulance_id"],
            ["id"],
        )
        batch_op.create_index(batch_op.f("ix_role_profiles_hospital_id"), ["hospital_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_role_profiles_shelter_id"), ["shelter_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_role_profiles_ambulance_id"), ["ambulance_id"], unique=False)
        batch_op.create_unique_constraint("uq_role_profiles_user_id", ["user_id"])


def downgrade():
    with op.batch_alter_table("role_profiles", schema=None) as batch_op:
        batch_op.drop_constraint("uq_role_profiles_user_id", type_="unique")
        batch_op.drop_index(batch_op.f("ix_role_profiles_ambulance_id"))
        batch_op.drop_index(batch_op.f("ix_role_profiles_shelter_id"))
        batch_op.drop_index(batch_op.f("ix_role_profiles_hospital_id"))
        batch_op.drop_constraint("fk_role_profiles_ambulance_id_ambulances", type_="foreignkey")
        batch_op.drop_constraint("fk_role_profiles_shelter_id_shelters", type_="foreignkey")
        batch_op.drop_constraint("fk_role_profiles_hospital_id_hospitals", type_="foreignkey")
        batch_op.drop_column("ambulance_id")
        batch_op.drop_column("shelter_id")
        batch_op.drop_column("hospital_id")

    with op.batch_alter_table("account_security", schema=None) as batch_op:
        batch_op.drop_column("must_change_password")
