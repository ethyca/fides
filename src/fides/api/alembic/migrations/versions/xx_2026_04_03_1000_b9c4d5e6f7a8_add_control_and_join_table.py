"""add control and access_policy_control tables

Revision ID: b9c4d5e6f7a8
Revises: d4e6f8a0b2c3
Create Date: 2026-04-03 10:00:00.000000

"""

from uuid import uuid4

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b9c4d5e6f7a8"
down_revision = "d4e6f8a0b2c3"
branch_labels = None
depends_on = None

SEED_CONTROLS = [
    ("eea_uk_gdpr", "EEA/UK: GDPR Articles 6 & 9"),
    ("us_glba_ccpa", "US: GLBA, CCPA / CPRA"),
    ("apac_pdpa_app", "APAC: PDPA, APP"),
    ("global", "Global: GDPR + GLBA + PDPA composite"),
]


def upgrade() -> None:
    op.create_table(
        "plus_control",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_plus_control_id", "plus_control", ["id"])
    op.create_index(
        "ix_plus_control_key", "plus_control", ["key"], unique=True
    )

    op.create_table(
        "plus_access_policy_control",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("access_policy_id", sa.String(length=255), nullable=False),
        sa.Column("control_id", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["access_policy_id"],
            ["plus_access_policy.id"],
            name="plus_access_policy_control_policy_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["control_id"],
            ["plus_control.id"],
            name="plus_access_policy_control_control_id_fkey",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "access_policy_id",
            name="uq_plus_access_policy_control_one_per_policy",
        ),
    )
    op.create_index(
        "ix_plus_access_policy_control_id",
        "plus_access_policy_control",
        ["id"],
    )
    # Seed initial controls
    for key, label in SEED_CONTROLS:
        control_id = str(uuid4())
        op.execute(
            sa.text(
                "INSERT INTO plus_control (id, key, label) VALUES (:id, :key, :label)"
            ).bindparams(id=control_id, key=key, label=label)
        )


def downgrade() -> None:
    op.drop_index(
        "ix_plus_access_policy_control_id",
        table_name="plus_access_policy_control",
    )
    op.drop_table("plus_access_policy_control")
    op.drop_index("ix_plus_control_key", table_name="plus_control")
    op.drop_index("ix_plus_control_id", table_name="plus_control")
    op.drop_table("plus_control")
