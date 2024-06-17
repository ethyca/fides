"""update custom field resource type enum

Revision ID: 5b03859e51b5
Revises: 451684a726a5
Create Date: 2023-04-19 19:22:47.566852

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "5b03859e51b5"
down_revision = "451684a726a5"
branch_labels = None
depends_on = None


def upgrade():
    """
    Extra steps added here to avoid the error that enums have to be committed before they can be used.  This
    avoids having to commit in the middle of this migration and lets the entire thing be completed in a single transaction
    """
    op.execute("alter type resourcetypes rename to resourcetypesold")

    op.execute(
        "create type resourcetypes as enum ('system', 'data_use', 'data_category', 'data_subject', 'privacy_declaration');"
    )

    op.execute(
        (
            "alter table plus_custom_field_definition alter column resource_type type resourcetypes using "
            "resource_type::text::resourcetypes"
        )
    )
    op.execute(
        (
            "alter table plus_custom_field alter column resource_type type resourcetypes using "
            "resource_type::text::resourcetypes"
        )
    )

    op.execute(("drop type resourcetypesold;"))


def downgrade():
    op.execute("alter type resourcetypes rename to resourcetypesold")

    op.execute(
        "create type resourcetypes as enum ('system', 'data_use', 'data_category', 'data_subject');"
    )

    # Data migration - delete rows with a resource type of 'privacy_declaration'
    op.execute(
        "delete from plus_custom_field where resource_type = 'privacy_declaration'"
    )
    # Data migration - delete rows with a resource type of 'privacy_declaration'
    op.execute(
        "delete from plus_custom_field_definition where resource_type = 'privacy_declaration'"
    )

    op.execute(
        (
            "alter table plus_custom_field_definition alter column resource_type type resourcetypes using "
            "resource_type::text::resourcetypes"
        )
    )

    op.execute(
        (
            "alter table plus_custom_field alter column resource_type type resourcetypes using "
            "resource_type::text::resourcetypes"
        )
    )

    op.execute(("drop type resourcetypesold;"))
