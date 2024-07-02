"""update consent mechanism

Revision ID: 144d9b85c712
Revises: 8188ddbf8cae
Create Date: 2023-04-12 14:57:07.532660

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "144d9b85c712"
down_revision = "8188ddbf8cae"
branch_labels = None
depends_on = None


def upgrade():
    """
    Extra steps added here to avoid the error that enums have to be committed before they can be used.  This
    avoids having to commit in the middle of this migration and lets the entire thing be completed in a single transaction
    """
    op.execute("alter type consentmechanism rename to consentmechanismold")

    op.execute(
        "create type consentmechanism as enum ('opt_in', 'opt_out', 'notice_only', 'necessary');"
    )
    op.execute(
        "create type consentmechanismnew as enum ('opt_in', 'opt_out', 'notice_only');"
    )
    op.execute(
        (
            "alter table privacynoticehistory alter column consent_mechanism type consentmechanism using "
            "consent_mechanism::text::consentmechanism"
        )
    )
    op.execute(
        (
            "alter table privacynotice alter column consent_mechanism type consentmechanism using "
            "consent_mechanism::text::consentmechanism"
        )
    )
    op.execute(
        (
            "update privacynoticehistory set consent_mechanism = 'notice_only' where consent_mechanism = 'necessary';"
        )
    )
    op.execute(
        (
            "update privacynotice set consent_mechanism = 'notice_only' where consent_mechanism = 'necessary';"
        )
    )
    op.execute(
        (
            "alter table privacynoticehistory alter column consent_mechanism type consentmechanismnew using "
            "consent_mechanism::text::consentmechanismnew"
        )
    )
    op.execute(
        (
            "alter table privacynotice alter column consent_mechanism type consentmechanismnew using "
            "consent_mechanism::text::consentmechanismnew"
        )
    )
    op.execute(("drop type consentmechanismold;"))
    op.execute(("drop type consentmechanism;"))
    op.execute(("alter type consentmechanismnew rename to consentmechanism;"))


def downgrade():
    op.execute("alter type consentmechanism rename to consentmechanismold")

    op.execute(
        "create type consentmechanism as enum ('opt_in', 'opt_out', 'notice_only', 'necessary');"
    )
    op.execute(
        "create type consentmechanismnew as enum ('opt_in', 'opt_out', 'necessary');"
    )
    op.execute(
        (
            "alter table privacynoticehistory alter column consent_mechanism type consentmechanism using "
            "consent_mechanism::text::consentmechanism"
        )
    )
    op.execute(
        (
            "alter table privacynotice alter column consent_mechanism type consentmechanism using "
            "consent_mechanism::text::consentmechanism"
        )
    )
    op.execute(
        (
            "update privacynoticehistory set consent_mechanism = 'necessary' where consent_mechanism = 'notice_only';"
        )
    )
    op.execute(
        (
            "update privacynotice set consent_mechanism = 'necessary' where consent_mechanism = 'notice_only';"
        )
    )
    op.execute(
        (
            "alter table privacynoticehistory alter column consent_mechanism type consentmechanismnew using "
            "consent_mechanism::text::consentmechanismnew"
        )
    )
    op.execute(
        (
            "alter table privacynotice alter column consent_mechanism type consentmechanismnew using "
            "consent_mechanism::text::consentmechanismnew"
        )
    )
    op.execute(("drop type consentmechanismold;"))
    op.execute(("drop type consentmechanism;"))
    op.execute(("alter type consentmechanismnew rename to consentmechanism;"))
