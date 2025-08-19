"""add generic taxonomy models

Revision ID: 3baf42d251a6
Revises: 2f3c1a2d6b10
Create Date: 2025-08-05 21:49:39.619569

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "3baf42d251a6"
down_revision = "2f3c1a2d6b10"
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
        sa.PrimaryKeyConstraint("fides_key"),
        sa.UniqueConstraint("id", name="uq_taxonomy_id"),
    )
    op.create_index(
        op.f("ix_taxonomy_fides_key"), "taxonomy", ["fides_key"], unique=True
    )

    # Create taxonomy_allowed_usage table
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
        sa.Column(
            "target_type", sa.String(), nullable=False
        ),  # Can be "system" OR "data_categories"
        sa.ForeignKeyConstraint(
            ["source_taxonomy_key"], ["taxonomy.fides_key"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("source_taxonomy_key", "target_type"),
        sa.UniqueConstraint("id", name="uq_taxonomy_allowed_usage_id"),
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
        sa.UniqueConstraint("id", name="uq_taxonomy_element_id"),
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
        sa.Column("target_element_key", sa.String(), nullable=False),
        sa.Column("source_taxonomy", sa.String(), nullable=False),
        sa.Column("target_taxonomy", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_taxonomy", "target_taxonomy"],
            [
                "taxonomy_allowed_usage.source_taxonomy_key",
                "taxonomy_allowed_usage.target_type",
            ],
            name="fk_taxonomy_usage_allowed",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_element_key",
            "target_element_key",
            name="uq_taxonomy_usage",
        ),
    )
    op.create_index(
        op.f("ix_taxonomy_usage_source_element_key"),
        "taxonomy_usage",
        ["source_element_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_taxonomy_usage_id"), "taxonomy_usage", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_taxonomy_usage_source_taxonomy"),
        "taxonomy_usage",
        ["source_taxonomy"],
        unique=False,
    )
    op.create_index(
        op.f("ix_taxonomy_usage_target_element_key"),
        "taxonomy_usage",
        ["target_element_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_taxonomy_usage_target_taxonomy"),
        "taxonomy_usage",
        ["target_taxonomy"],
        unique=False,
    )

    # Seed legacy taxonomies that are managed by the system
    op.execute(
        """
        INSERT INTO taxonomy (id, created_at, updated_at, fides_key, organization_fides_key, tags, name, description)
        VALUES
          ('data_category', now(), now(), 'data_category', NULL, NULL, 'Data categories', 'Taxonomy for data categories'),
          ('data_use', now(), now(), 'data_use', NULL, NULL, 'Data uses', 'Taxonomy for data uses'),
          ('data_subject', now(), now(), 'data_subject', NULL, NULL, 'Data subjects', 'Taxonomy for data subjects'),
          ('system_group', now(), now(), 'system_group', NULL, NULL, 'System groups', 'Taxonomy for system groups')
        """
    )


def downgrade():
    # Drop taxonomy_usage
    op.drop_index(
        op.f("ix_taxonomy_usage_source_element_key"), table_name="taxonomy_usage"
    )
    op.drop_index(
        op.f("ix_taxonomy_usage_target_taxonomy"), table_name="taxonomy_usage"
    )
    op.drop_index(
        op.f("ix_taxonomy_usage_target_element_key"), table_name="taxonomy_usage"
    )
    op.drop_index(
        op.f("ix_taxonomy_usage_source_taxonomy"), table_name="taxonomy_usage"
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
    op.drop_table("taxonomy_element")

    # Drop taxonomy_allowed_usage
    op.drop_table("taxonomy_allowed_usage")

    # Drop taxonomy
    op.drop_index(op.f("ix_taxonomy_fides_key"), table_name="taxonomy")
    op.drop_table("taxonomy")
