"""cancel privacy request

Revision ID: ed1b00ff963d
Revises: 55d61eb8ed12
Create Date: 2022-06-03 15:45:14.584540

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ed1b00ff963d"
down_revision = "55d61eb8ed12"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "privacyrequest", sa.Column("cancel_reason", sa.String(200), nullable=True)
    )
    op.add_column(
        "privacyrequest",
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("alter type privacyrequeststatus add value 'canceled'")


def downgrade():
    op.drop_column("privacyrequest", "canceled_at")
    op.drop_column("privacyrequest", "cancel_reason")

    op.execute("delete from privacyrequest where status in ('canceled')")

    op.execute("alter type privacyrequeststatus rename to privacyrequeststatus_old")
    op.execute(
        "create type privacyrequeststatus as enum('in_processing', 'complete', 'pending', 'error', 'paused', 'approved', 'denied')"
    )
    op.execute(
        (
            "alter table privacyrequest alter column status type privacyrequeststatus using "
            "status::text::privacyrequeststatus"
        )
    )
    op.execute("drop type privacyrequeststatus_old")
