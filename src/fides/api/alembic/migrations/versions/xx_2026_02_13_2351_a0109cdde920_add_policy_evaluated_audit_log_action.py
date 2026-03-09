"""add policy_evaluated audit log action

Revision ID: a0109cdde920
Revises: c0dc13ad2a05
Create Date: 2026-02-13 23:51:05.601661

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a0109cdde920"
down_revision = "c0dc13ad2a05"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("alter type auditlogaction add value 'policy_evaluated'")


def downgrade():
    op.execute(
        "update auditlog set action = 'finished' where action = 'policy_evaluated'"
    )
    op.execute("alter type auditlogaction rename to auditlogaction_old")
    op.execute(
        "create type auditlogaction as enum('approved', 'denied', 'email_sent', 'finished')"
    )
    op.execute(
        (
            "alter table auditlog alter column action type auditlogaction using "
            "action::text::auditlogaction"
        )
    )
    op.execute("drop type auditlogaction_old")
