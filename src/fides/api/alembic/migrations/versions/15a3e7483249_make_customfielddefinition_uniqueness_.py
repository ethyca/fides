"""make customfielddefinition uniqueness case insensitive

Revision ID: 15a3e7483249
Revises: e92da354691e
Create Date: 2023-05-02 15:03:56.256982

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.exc import IntegrityError

# revision identifiers, used by Alembic.
revision = "15a3e7483249"
down_revision = "e92da354691e"
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.execute(
            """ CREATE UNIQUE INDEX ix_plus_custom_field_definition_unique_lowername_resourcetype
                ON plus_custom_field_definition
                (lower(name), resource_type)
            """
        )
    except IntegrityError as exc:
        raise Exception(
            f"Fides attempted to create new custom field definition unique index but got error: {exc}. "
            f"Adjust custom field names to avoid case-insensitive name overlaps for the same resource type."
        )

    # remove unnecessary index of unused field
    op.drop_index(
        "ix_plus_custom_field_definition_field_definition",
        table_name="plus_custom_field_definition",
    )


def downgrade():
    op.drop_index(
        op.f("ix_plus_custom_field_definition_unique_lowername_resourcetype"),
        table_name="plus_custom_field_definition",
    )

    # re-add unnecessray index of unused field in downgrade, for consistency
    op.create_index(
        op.f("ix_plus_custom_field_definition_field_definition"),
        "plus_custom_field_definition",
        ["field_definition"],
        unique=False,
    )
