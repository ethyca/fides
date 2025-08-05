"""add generic taxonomy models

Revision ID: 26964fd16126
Revises: a7065df4dcf1
Create Date: 2025-08-04 23:48:15.260781

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "26964fd16126"
down_revision = "a7065df4dcf1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "taxonomy",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("organization_fides_key", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id", "fides_key"),
    )
    op.create_index(
        op.f("ix_taxonomy_fides_key"), "taxonomy", ["fides_key"], unique=True
    )
    op.create_index(op.f("ix_taxonomy_id"), "taxonomy", ["id"], unique=False)
    op.create_table(
        "taxonomy_allowed_usage",
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
        sa.Column("source_taxonomy_key", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_taxonomy_key", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_taxonomy_key"], ["taxonomy.fides_key"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", "source_taxonomy_key", "target_type"),
        sa.UniqueConstraint(
            "source_taxonomy_key",
            "target_type",
            "target_taxonomy_key",
            name="uq_allowed_usage_combination",
        ),
    )
    op.create_index(
        "ix_allowed_usage_lookup",
        "taxonomy_allowed_usage",
        ["source_taxonomy_key", "target_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_taxonomy_allowed_usage_id"),
        "taxonomy_allowed_usage",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_taxonomy_allowed_usage_source_taxonomy_key"),
        "taxonomy_allowed_usage",
        ["source_taxonomy_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_taxonomy_allowed_usage_target_taxonomy_key"),
        "taxonomy_allowed_usage",
        ["target_taxonomy_key"],
        unique=False,
    )
    op.create_table(
        "taxonomy_element",
        sa.Column("organization_fides_key", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
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
        sa.Column("id", sa.String(length=255), nullable=True),
        sa.Column("fides_key", sa.String(), nullable=False),
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
        op.f("ix_taxonomy_element_active"), "taxonomy_element", ["active"], unique=False
    )
    op.create_index(
        op.f("ix_taxonomy_element_fides_key"),
        "taxonomy_element",
        ["fides_key"],
        unique=True,
    )
    op.create_index(
        op.f("ix_taxonomy_element_id"), "taxonomy_element", ["id"], unique=False
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
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_identifier", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_element_key"],
            ["taxonomy_element.fides_key"],
            name="fk_taxonomy_usage_source_element",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_element_key"], ["taxonomy_element.fides_key"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint(
            "id", "source_element_key", "target_type", "target_identifier"
        ),
    )
    op.create_index(
        "ix_taxonomy_usage_by_source",
        "taxonomy_usage",
        ["source_element_key", "target_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_taxonomy_usage_id"), "taxonomy_usage", ["id"], unique=False
    )
    op.create_index(
        "ix_taxonomy_usage_lookup",
        "taxonomy_usage",
        ["target_type", "target_identifier"],
        unique=False,
    )
    op.create_index(
        op.f("ix_taxonomy_usage_source_element_key"),
        "taxonomy_usage",
        ["source_element_key"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_taxonomy_usage_source_element_key"), table_name="taxonomy_usage"
    )
    op.drop_index("ix_taxonomy_usage_lookup", table_name="taxonomy_usage")
    op.drop_index(op.f("ix_taxonomy_usage_id"), table_name="taxonomy_usage")
    op.drop_index("ix_taxonomy_usage_by_source", table_name="taxonomy_usage")
    op.drop_table("taxonomy_usage")
    op.drop_index(
        op.f("ix_taxonomy_element_taxonomy_type"), table_name="taxonomy_element"
    )
    op.drop_index(op.f("ix_taxonomy_element_parent_key"), table_name="taxonomy_element")
    op.drop_index(op.f("ix_taxonomy_element_id"), table_name="taxonomy_element")
    op.drop_index(op.f("ix_taxonomy_element_fides_key"), table_name="taxonomy_element")
    op.drop_index(op.f("ix_taxonomy_element_active"), table_name="taxonomy_element")
    op.drop_table("taxonomy_element")
    op.drop_index(
        op.f("ix_taxonomy_allowed_usage_target_taxonomy_key"),
        table_name="taxonomy_allowed_usage",
    )
    op.drop_index(
        op.f("ix_taxonomy_allowed_usage_source_taxonomy_key"),
        table_name="taxonomy_allowed_usage",
    )
    op.drop_index(
        op.f("ix_taxonomy_allowed_usage_id"), table_name="taxonomy_allowed_usage"
    )
    op.drop_index("ix_allowed_usage_lookup", table_name="taxonomy_allowed_usage")
    op.drop_table("taxonomy_allowed_usage")
    op.drop_index(op.f("ix_taxonomy_id"), table_name="taxonomy")
    op.drop_index(op.f("ix_taxonomy_fides_key"), table_name="taxonomy")
    op.drop_table("taxonomy")
