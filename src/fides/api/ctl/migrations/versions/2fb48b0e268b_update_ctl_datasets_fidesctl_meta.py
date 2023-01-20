"""update ctl_datasets fidesctl_meta

Revision ID: 2fb48b0e268b
Revises: a08024ba7e2b
Create Date: 2022-12-08 17:49:14.317905

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2fb48b0e268b"
down_revision = "a08024ba7e2b"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("ctl_datasets", "fidesctl_meta", new_column_name="fides_meta")


def downgrade():
    op.alter_column("ctl_datasets", "fides_meta", new_column_name="fidesctl_meta")
