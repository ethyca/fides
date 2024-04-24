"""privacy request approve

Revision ID: 906d7198df28
Revises: 5a966cd643d7
Create Date: 2022-03-11 19:49:26.450054

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "906d7198df28"
down_revision = "5a966cd643d7"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("alter type privacyrequeststatus add value 'approved'")
    op.execute("alter type privacyrequeststatus add value 'denied'")

    op.add_column(
        "privacyrequest",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "privacyrequest", sa.Column("reviewed_by", sa.String(), nullable=True)
    )
    op.create_foreign_key(
        "privacyrequest_reviewed_by_fkey",
        "privacyrequest",
        "fidesopsuser",
        ["reviewed_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.execute("delete from privacyrequest where status in ('approved', 'denied')")
    op.drop_constraint(
        "privacyrequest_reviewed_by_fkey", "privacyrequest", type_="foreignkey"
    )
    op.drop_column("privacyrequest", "reviewed_by")
    op.drop_column("privacyrequest", "reviewed_at")

    op.execute("alter type privacyrequeststatus rename to privacyrequeststatus_old")
    op.execute(
        "create type privacyrequeststatus as enum('in_processing', 'complete', 'pending', 'error', 'paused')"
    )
    op.execute(
        (
            "alter table privacyrequest alter column status type privacyrequeststatus using "
            "status::text::privacyrequeststatus"
        )
    )
    op.execute("drop type privacyrequeststatus_old")
