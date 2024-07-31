"""add consent automation tables

Revision ID: d69cf8f82a58
Revises: fc82ab64bd5e
Create Date: 2024-07-24 23:09:46.681097

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d69cf8f82a58"
down_revision = "fc82ab64bd5e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "plus_consent_automation",
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
        sa.Column("connection_config_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["connection_config_id"], ["connectionconfig.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("connection_config_id"),
    )
    op.create_index(
        op.f("ix_plus_consent_automation_id"),
        "plus_consent_automation",
        ["id"],
        unique=False,
    )
    op.create_table(
        "plus_consentable_item",
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
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("consent_automation_id", sa.String(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("parent_id", sa.String(), nullable=True),
        sa.Column("notice_id", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["consent_automation_id"],
            ["plus_consent_automation.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["notice_id"],
            ["privacynotice.id"],
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["plus_consentable_item.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("consent_automation_id", "type", "external_id"),
    )
    op.create_index(
        op.f("ix_plus_consentable_item_id"),
        "plus_consentable_item",
        ["id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_plus_consentable_item_id"), table_name="plus_consentable_item"
    )
    op.drop_table("plus_consentable_item")
    op.drop_index(
        op.f("ix_plus_consent_automation_id"), table_name="plus_consent_automation"
    )
    op.drop_table("plus_consent_automation")
