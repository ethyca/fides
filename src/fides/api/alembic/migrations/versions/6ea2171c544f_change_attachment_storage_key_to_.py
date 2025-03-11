"""Change Attachment.storage_key to foreign key

Revision ID: 6ea2171c544f
Revises: 1152c1717849
Create Date: 2025-03-10 17:36:31.504831

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "6ea2171c544f"
down_revision = "1152c1717849"
branch_labels = None
depends_on = None


def upgrade():

    # Alter the column type and add the new foreign key constraint
    op.alter_column(
        "attachment",
        "storage_key",
        existing_type=sa.String(),
        type_=sa.String(),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_attachment_storage_key",
        "attachment",
        "storageconfig",
        ["storage_key"],
        ["key"],
        ondelete="CASCADE",
    )

    # Add index on attachment_reference.reference_id
    op.create_index(
        "ix_attachment_reference_reference_id",
        "attachment_reference",
        ["reference_id"],
    )

    # Add index on attachment_reference.reference_type
    op.create_index(
        "ix_attachment_reference_reference_type",
        "attachment_reference",
        ["reference_type"],
    )
    # ### end Alembic commands ###


def downgrade():
    # Drop the index on attachment_reference.reference_id
    op.drop_index(
        "ix_attachment_reference_reference_id", table_name="attachment_reference"
    )

    # Drop the index on attachment_reference.reference_type
    op.drop_index(
        "ix_attachment_reference_reference_type", table_name="attachment_reference"
    )

    # Drop the new foreign key constraint
    op.drop_constraint("fk_attachment_storage_key", "attachment", type_="foreignkey")

    # Revert the column type change
    op.alter_column(
        "attachment",
        "storage_key",
        existing_type=sa.String(),
        type_=sa.String(),
        nullable=True,
    )
    # ### end Alembic commands ###
