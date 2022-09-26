"""identity_verification

Revision ID: 97801300fedd
Revises: c61fd9d4f73e
Create Date: 2022-08-18 19:13:07.393937

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "97801300fedd"
down_revision = "c61fd9d4f73e"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("alter type privacyrequeststatus add value 'identity_unverified'")
    op.add_column(
        "privacyrequest",
        sa.Column("identity_verified_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_column("privacyrequest", "identity_verified_at")
    op.execute("alter type privacyrequeststatus rename to privacyrequeststatus_old")
    op.execute(
        "create type privacyrequeststatus as enum('in_processing', 'complete', 'pending', 'error', 'paused', 'approved', 'denied', 'canceled')"
    )
    op.execute(
        (
            "alter table privacyrequest alter column status type privacyrequeststatus using "
            "status::text::privacyrequeststatus"
        )
    )
    op.execute("drop type privacyrequeststatus_old")
