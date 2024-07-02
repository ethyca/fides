"""Add ga_client_id as a provided identity type

Revision ID: 392992c7733a
Revises: de456534dbda
Create Date: 2023-01-20 15:33:24.084841

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "392992c7733a"
down_revision = "de456534dbda"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE providedidentitytype ADD VALUE 'ga_client_id'")


def downgrade():
    # rename the existing type
    op.execute("ALTER TYPE providedidentitytype RENAME TO providedidentitytype_old")

    # create the new type
    op.execute("CREATE TYPE providedidentitytype AS ENUM('email', 'phone_number')")

    # update the columns to use the new type
    op.execute(
        "ALTER TABLE providedidentity ALTER COLUMN field_name TYPE providedidentitytype USING field_name::text::providedidentitytype"
    )

    # remove the old type
    op.execute("DROP TYPE providedidentitytype_old")
