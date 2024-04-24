"""adds fides_user_device_id enum

Revision ID: 3842d1acac5f
Revises: 8342453518cc
Create Date: 2023-04-21 20:10:01.389078

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "3842d1acac5f"
down_revision = "8342453518cc"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE providedidentitytype RENAME TO providedidentitytype_old")
    op.execute(
        "CREATE TYPE providedidentitytype AS ENUM('email', 'phone_number', 'ga_client_id', 'ljt_readerID', 'fides_user_device_id')"
    )
    op.execute(
        "ALTER TABLE providedidentity ALTER COLUMN field_name TYPE providedidentitytype USING field_name::text::providedidentitytype"
    )
    op.execute("DROP TYPE providedidentitytype_old")


def downgrade():
    op.execute("ALTER TYPE providedidentitytype RENAME TO providedidentitytype_old")
    op.execute(
        "CREATE TYPE providedidentitytype AS ENUM('email', 'phone_number', 'ga_client_id', 'ljt_readerID')"
    )
    op.execute(
        "ALTER TABLE providedidentity ALTER COLUMN field_name TYPE providedidentitytype USING field_name::text::providedidentitytype"
    )
    op.execute("DROP TYPE providedidentitytype_old")
