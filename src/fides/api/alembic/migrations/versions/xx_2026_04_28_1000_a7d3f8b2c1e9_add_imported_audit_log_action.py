"""add imported audit log action

Revision ID: a7d3f8b2c1e9
Revises: 55cf25a3e2ca
Create Date: 2026-04-28 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a7d3f8b2c1e9"
down_revision = "55cf25a3e2ca"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("alter type auditlogaction add value 'imported'")


def downgrade():
    # An 'imported' AuditLog entry records that an OWNER ran a historical
    # migration; it does not represent an approval, denial, or any other
    # lifecycle event on the underlying request. There is no equivalent value
    # in the pre-migration enum to fold these rows into without distorting
    # compliance queries, so they are dropped on downgrade. The parent
    # PrivacyRequest still carries `source='Import'` for any post-downgrade
    # triage.
    op.execute("delete from auditlog where action = 'imported'")

    # Recreate auditlogaction enum without the 'imported' value
    op.execute("alter type auditlogaction rename to auditlogaction_old")
    op.execute(
        "create type auditlogaction as enum("
        "'approved', 'denied', 'email_sent', 'finished', 'policy_evaluated', "
        "'pre_approval_webhook_triggered', 'pre_approval_eligible', "
        "'pre_approval_not_eligible')"
    )
    op.execute(
        "alter table auditlog alter column action type auditlogaction "
        "using action::text::auditlogaction"
    )
    op.execute("drop type auditlogaction_old")
