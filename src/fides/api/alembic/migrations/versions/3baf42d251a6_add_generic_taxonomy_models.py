"""add generic taxonomy models

Revision ID: f11e77bc2333
Revises: a7065df4dcf1
Create Date: 2025-08-05 21:49:39.619569

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f11e77bc2333"
down_revision = "a7065df4dcf1"
branch_labels = None
depends_on = None


def upgrade():
    # Create taxonomy table
    op.create_table(
        "taxonomy",
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
        sa.Column("fides_key", sa.String(), nullable=False),
        sa.Column("organization_fides_key", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("applies_to", sa.JSON(), server_default="[]", nullable=False),
        sa.PrimaryKeyConstraint("fides_key"),
    )
    op.create_index(op.f("ix_taxonomy_id"), "taxonomy", ["id"], unique=False)
    op.create_index(
        op.f("ix_taxonomy_fides_key"), "taxonomy", ["fides_key"], unique=True
    )

    # Create taxonomy_element table
    op.create_table(
        "taxonomy_element",
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
        sa.Column("fides_key", sa.String(), nullable=False),
        sa.Column("organization_fides_key", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("taxonomy_type", sa.String(), nullable=False),
        sa.Column("parent_key", sa.Text(), nullable=True),
        sa.Column("active", sa.BOOLEAN(), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_key"], ["taxonomy_element.fides_key"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["taxonomy_type"], ["taxonomy.fides_key"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("fides_key"),
    )
    op.create_index(
        op.f("ix_taxonomy_element_id"), "taxonomy_element", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_taxonomy_element_fides_key"),
        "taxonomy_element",
        ["fides_key"],
        unique=True,
    )
    op.create_index(
        op.f("ix_taxonomy_element_active"), "taxonomy_element", ["active"], unique=False
    )
    op.create_index(
        op.f("ix_taxonomy_element_parent_key"),
        "taxonomy_element",
        ["parent_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_taxonomy_element_taxonomy_type"),
        "taxonomy_element",
        ["taxonomy_type"],
        unique=False,
    )

    # Create taxonomy_usage table
    op.create_table(
        "taxonomy_usage",
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
        sa.Column("source_element_key", sa.String(), nullable=False),
        sa.Column("taxonomy_type", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_identifier", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_element_key"],
            ["taxonomy_element.fides_key"],
            name="fk_taxonomy_usage_source_element",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_element_key",
            "target_type",
            "target_identifier",
            name="uq_taxonomy_usage_application",
        ),
    )
    op.create_index(
        op.f("ix_taxonomy_usage_id"), "taxonomy_usage", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_taxonomy_usage_source_element_key"),
        "taxonomy_usage",
        ["source_element_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_taxonomy_usage_taxonomy_type"),
        "taxonomy_usage",
        ["taxonomy_type"],
        unique=False,
    )
    op.create_index(
        "ix_taxonomy_usage_lookup",
        "taxonomy_usage",
        ["target_type", "target_identifier"],
        unique=False,
    )
    op.create_index(
        "ix_taxonomy_usage_by_taxonomy",
        "taxonomy_usage",
        ["taxonomy_type", "target_type"],
        unique=False,
    )


def downgrade():
    # Drop taxonomy_usage
    op.drop_index("ix_taxonomy_usage_by_taxonomy", table_name="taxonomy_usage")
    op.drop_index("ix_taxonomy_usage_lookup", table_name="taxonomy_usage")
    op.drop_index(op.f("ix_taxonomy_usage_taxonomy_type"), table_name="taxonomy_usage")
    op.drop_index(
        op.f("ix_taxonomy_usage_source_element_key"), table_name="taxonomy_usage"
    )
    op.drop_index(op.f("ix_taxonomy_usage_id"), table_name="taxonomy_usage")
    op.drop_table("taxonomy_usage")

    # Drop taxonomy_element
    op.drop_index(
        op.f("ix_taxonomy_element_taxonomy_type"), table_name="taxonomy_element"
    )
    op.drop_index(op.f("ix_taxonomy_element_parent_key"), table_name="taxonomy_element")
    op.drop_index(op.f("ix_taxonomy_element_active"), table_name="taxonomy_element")
    op.drop_index(op.f("ix_taxonomy_element_fides_key"), table_name="taxonomy_element")
    op.drop_index(op.f("ix_taxonomy_element_id"), table_name="taxonomy_element")
    op.drop_table("taxonomy_element")

    # Drop taxonomy
    op.drop_index(op.f("ix_taxonomy_fides_key"), table_name="taxonomy")
    op.drop_index(op.f("ix_taxonomy_id"), table_name="taxonomy")
    op.drop_table("taxonomy")
