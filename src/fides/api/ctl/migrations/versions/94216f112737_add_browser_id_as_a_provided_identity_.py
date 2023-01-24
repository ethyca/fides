"""Add browser_id as a provided identity type

Revision ID: 94216f112737
Revises: 392992c7733a
Create Date: 2023-01-24 20:26:25.552361

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "94216f112737"
down_revision = "392992c7733a"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE providedidentitytype ADD VALUE 'browser_id'")


def downgrade():
    # rename the existing type
    op.execute("ALTER TYPE providedidentitytype RENAME TO providedidentitytype_old")

    # create the new type
    op.execute(
        "CREATE TYPE providedidentitytype AS ENUM('email', 'phone_number', 'user_id')"
    )

    # update the columns to use the new type
    op.execute(
        "ALTER TABLE providedidentity ALTER COLUMN field_name TYPE providedidentitytype USING field_name::text::providedidentitytype"
    )

    # remove the old type
    op.execute("DROP TYPE providedidentitytype_old")
