"""update assessment_template schema: remove key, add fides_revision, is_managed, parent_template_id

Revision ID: f7a8b9c0d1e2
Revises: d6e7f8a9b0c1
Create Date: 2026-04-17 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "f7a8b9c0d1e2"
down_revision = "d6e7f8a9b0c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns with defaults
    op.add_column(
        "assessment_template",
        sa.Column("fides_revision", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "assessment_template",
        sa.Column("is_managed", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "assessment_template",
        sa.Column("parent_template_id", sa.String(), nullable=True),
    )

    # Add foreign key for parent_template_id
    op.create_foreign_key(
        "fk_assessment_template_parent_template_id",
        "assessment_template",
        "assessment_template",
        ["parent_template_id"],
        ["id"],
    )

    # Drop unique index on key (was created as index with unique=True)
    op.drop_index("ix_assessment_template_key", table_name="assessment_template")

    # Drop key column
    op.drop_column("assessment_template", "key")

    # Add composite unique constraint
    op.create_unique_constraint(
        "uq_assessment_template_type_version_revision",
        "assessment_template",
        ["assessment_type", "version", "fides_revision"],
    )

    # Add index on assessment_type (was previously indexed via key)
    op.create_index(
        "ix_assessment_template_assessment_type",
        "assessment_template",
        ["assessment_type"],
    )


def downgrade() -> None:
    # Drop index on assessment_type
    op.drop_index(
        "ix_assessment_template_assessment_type",
        table_name="assessment_template",
    )

    # Drop composite unique constraint
    op.drop_constraint(
        "uq_assessment_template_type_version_revision",
        "assessment_template",
        type_="unique",
    )

    # Re-add key column, populate from assessment_type
    op.add_column(
        "assessment_template",
        sa.Column("key", sa.String(), nullable=True),
    )

    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE assessment_template SET key = assessment_type")
    )

    op.alter_column("assessment_template", "key", nullable=False)
    op.create_unique_constraint(
        "assessment_template_key_key",
        "assessment_template",
        ["key"],
    )
    op.create_index(
        "ix_assessment_template_key",
        "assessment_template",
        ["key"],
    )

    # Drop foreign key and new columns
    op.drop_constraint(
        "fk_assessment_template_parent_template_id",
        "assessment_template",
        type_="foreignkey",
    )
    op.drop_column("assessment_template", "parent_template_id")
    op.drop_column("assessment_template", "is_managed")
    op.drop_column("assessment_template", "fides_revision")
