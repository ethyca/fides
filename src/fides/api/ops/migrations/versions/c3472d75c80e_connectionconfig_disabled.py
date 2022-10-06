"""connectionconfig disabled

Revision ID: c3472d75c80e
Revises: 27fe9da9d0f9
Create Date: 2022-06-08 20:15:28.924262

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c3472d75c80e"
down_revision = "27fe9da9d0f9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "connectionconfig",
        sa.Column("disabled", sa.Boolean(), server_default="f", nullable=True),
    )
    op.add_column(
        "connectionconfig",
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("alter type executionlogstatus add value 'skipped'")


def downgrade():
    op.drop_column("connectionconfig", "disabled_at")
    op.drop_column("connectionconfig", "disabled")

    # Downgrade executionlogstatus
    op.execute("alter type executionlogstatus rename to executionlogstatus_old")
    op.execute(
        "create type executionlogstatus as enum('in_processing', 'pending', 'complete', 'error', 'retrying', 'paused')"
    )
    op.execute(
        (
            "alter table executionlog alter column status type executionlogstatus using "
            "status::text::executionlogstatus"
        )
    )
    op.execute("drop type executionlogstatus_old")
