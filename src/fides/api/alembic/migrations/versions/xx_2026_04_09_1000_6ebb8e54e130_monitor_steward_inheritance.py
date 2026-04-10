"""add monitor steward inheritance support

Adds inherit_system_stewards boolean to monitorconfig.
Adds source and source_system_id columns to monitorsteward.
Updates unique constraint on monitorsteward to include source.

Existing monitors are backfilled with inherit_system_stewards=false so
current behavior is preserved.  New monitors default to true.

Revision ID: 6ebb8e54e130
Revises: 6a42f48c23dd
Create Date: 2026-04-09 10:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "6ebb8e54e130"
down_revision = "6a42f48c23dd"
branch_labels = None
depends_on = None


def upgrade():
    # --- monitorconfig: add inherit_system_stewards ---
    op.add_column(
        "monitorconfig",
        sa.Column(
            "inherit_system_stewards",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    # Backfill existing monitors to false so current behavior is preserved
    op.execute("UPDATE monitorconfig SET inherit_system_stewards = false")

    # --- monitorsteward: add source column ---
    op.add_column(
        "monitorsteward",
        sa.Column(
            "source",
            sa.String(),
            nullable=False,
            server_default="explicit",
        ),
    )

    # --- monitorsteward: add source_system_id FK ---
    op.add_column(
        "monitorsteward",
        sa.Column(
            "source_system_id",
            sa.String(),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_monitorsteward_source_system_id",
        "monitorsteward",
        ["source_system_id"],
    )
    op.create_foreign_key(
        "fk_monitorsteward_source_system_id",
        "monitorsteward",
        "ctl_systems",
        ["source_system_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # --- monitorsteward: replace unique constraint ---
    op.drop_constraint(
        "uq_monitorsteward_user_monitor",
        "monitorsteward",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_monitorsteward_user_monitor_source",
        "monitorsteward",
        ["user_id", "monitor_config_id", "source"],
    )


def downgrade():
    # --- monitorsteward: restore original unique constraint ---
    op.drop_constraint(
        "uq_monitorsteward_user_monitor_source",
        "monitorsteward",
        type_="unique",
    )
    # Remove any inherited rows before restoring the old constraint,
    # since duplicates (same user+monitor, different source) would violate it.
    op.execute("DELETE FROM monitorsteward WHERE source = 'inherited'")
    op.create_unique_constraint(
        "uq_monitorsteward_user_monitor",
        "monitorsteward",
        ["user_id", "monitor_config_id"],
    )

    # --- monitorsteward: drop source_system_id ---
    op.drop_constraint(
        "fk_monitorsteward_source_system_id",
        "monitorsteward",
        type_="foreignkey",
    )
    op.drop_index("ix_monitorsteward_source_system_id", "monitorsteward")
    op.drop_column("monitorsteward", "source_system_id")

    # --- monitorsteward: drop source ---
    op.drop_column("monitorsteward", "source")

    # --- monitorconfig: drop inherit_system_stewards ---
    op.drop_column("monitorconfig", "inherit_system_stewards")
