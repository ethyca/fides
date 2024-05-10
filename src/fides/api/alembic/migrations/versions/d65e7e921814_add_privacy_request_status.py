"""Add privacy request status

Revision ID: d65e7e921814
Revises: c5336b841d70
Create Date: 2021-12-02 22:06:16.270442

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d65e7e921814"
down_revision = "c5336b841d70"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("alter type privacyrequeststatus add value 'paused'")


def downgrade():
    op.execute("delete from privacyrequest where status in ('paused')")
    op.execute("alter type privacyrequeststatus rename to privacyrequeststatus_old")
    op.execute(
        "create type privacyrequeststatus as enum('in_processing', 'complete', 'pending', 'error')"
    )
    op.execute(
        (
            "alter table privacyrequest alter column status type privacyrequeststatus using "
            "status::text::privacyrequeststatus"
        )
    )
    op.execute("drop type privacyrequeststatus_old")
