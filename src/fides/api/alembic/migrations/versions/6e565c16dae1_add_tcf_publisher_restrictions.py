"""Add TCF Publisher Restrictions

Revision ID: 6e565c16dae1
Revises: 67d01c4e124e
Create Date: 2025-04-02 12:35:34.105607

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "6e565c16dae1"
down_revision = "67d01c4e124e"
branch_labels = None
depends_on = None


def upgrade():
    # Create tcf_configuration table
    op.create_table(
        "tcf_configuration",
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
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    # Create tcf_publisher_restriction table
    op.create_table(
        "tcf_publisher_restriction",
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
        sa.Column("tcf_configuration_id", sa.String(255), nullable=False),
        sa.Column("purpose_id", sa.Integer(), nullable=False),
        sa.Column(
            "restriction_type",
            sa.Enum(
                "purpose_restriction",
                "require_consent",
                "require_legitimate_interest",
                name="tcfrestrictiontype",
            ),
            nullable=False,
        ),
        sa.Column(
            "vendor_restriction",
            sa.Enum(
                "restrict_all_vendors",
                "allow_specific_vendors",
                "restrict_specific_vendors",
                name="tcfvendorrestriction",
            ),
            nullable=False,
        ),
        sa.Column(
            "range_entries",
            postgresql.ARRAY(postgresql.JSONB(astext_type=sa.Text())),
            server_default="{}",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tcf_configuration_id"],
            ["tcf_configuration.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tcf_publisher_restriction_config_purpose"),
        "tcf_publisher_restriction",
        ["tcf_configuration_id", "purpose_id"],
        unique=False,
    )


def downgrade():
    # Drop tables
    op.drop_table("tcf_publisher_restriction")
    op.drop_table("tcf_configuration")

    # Drop enums
    op.execute("DROP TYPE tcfrestrictiontype")
    op.execute("DROP TYPE tcfvendorrestriction")
