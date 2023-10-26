"""update cookie max age to bigint

Revision ID: ddec29f24945
Revises: c5a218831820
Create Date: 2023-10-24 13:05:40.442124

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import BIGINT

# revision identifiers, used by Alembic.
revision = "ddec29f24945"
down_revision = "c5a218831820"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("ctl_systems", "cookie_max_age_seconds", type_=BIGINT)


def downgrade():
    op.alter_column("ctl_systems", "cookie_max_age_seconds", type_=Integer)
