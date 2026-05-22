"""add imported audit log action

Revision ID: a7d3f8b2c1e9
Revises: b034cd68950d
Create Date: 2026-04-28 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a7d3f8b2c1e9"
down_revision = "b034cd68950d"
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

    # Recreate auditlogaction enum without the 'imported' value. The list
    # below must contain every enum value that legitimately exists at this
    # point in the migration chain — including `access_package_approved`
    # and `access_package_redacted`, added by revision 1e07732ff193 — so the
    # subsequent `USING action::text::auditlogaction` cast does not fail on
    # rows holding those actions.
    op.execute("alter type auditlogaction rename to auditlogaction_old")
    op.execute(
        "create type auditlogaction as enum("
        "'approved', 'denied', 'email_sent', 'finished', 'policy_evaluated', "
        "'pre_approval_webhook_triggered', 'pre_approval_eligible', "
        "'pre_approval_not_eligible', "
        "'access_package_approved', 'access_package_redacted')"
    )
    op.execute(
        "alter table auditlog alter column action type auditlogaction "
        "using action::text::auditlogaction"
    )
    op.execute("drop type auditlogaction_old")
