"""Add finished audit log

Revision ID: bab75915670a
Revises: 3c5e1253465d
Create Date: 2022-08-04 20:18:29.339116

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "bab75915670a"
down_revision = "3c5e1253465d"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("alter type auditlogaction add value 'finished'")


def downgrade():
    op.execute("delete from auditlog where action in ('finished')")
    op.execute("alter type auditlogaction rename to auditlogaction_old")
    op.execute("create type auditlogaction as enum('approved', 'denied')")
    op.execute(
        (
            "alter table auditlog alter column action type auditlogaction using "
            "action::text::auditlogaction"
        )
    )
    op.execute("drop type auditlogaction_old")
