"""audit log email send

Revision ID: 912d801f06c0
Revises: bde646a6f51e
Create Date: 2022-09-01 16:23:10.905356

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "912d801f06c0"
down_revision = "bde646a6f51e"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("alter type auditlogaction add value 'email_sent'")


def downgrade():
    op.execute("delete from auditlog where action in ('email_sent')")
    op.execute("alter type auditlogaction rename to auditlogaction_old")
    op.execute("create type auditlogaction as enum('approved', 'denied', 'finished')")
    op.execute(
        (
            "alter table auditlog alter column action type auditlogaction using "
            "action::text::auditlogaction"
        )
    )
    op.execute("drop type auditlogaction_old")
