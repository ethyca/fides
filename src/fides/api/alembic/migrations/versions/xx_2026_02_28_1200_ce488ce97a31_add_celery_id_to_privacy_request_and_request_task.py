"""Add celery_id column to privacyrequest and requesttask tables

Moves Celery task ID tracking from ephemeral Redis cache to durable DB
columns, following the pattern already established by MonitorTask.

Revision ID: ce488ce97a31
Revises: 074796d61d8a
Create Date: 2026-02-28 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "ce488ce97a31"
down_revision = "074796d61d8a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "privacyrequest",
        sa.Column("celery_id", sa.String(length=255), nullable=True, index=True),
    )
    op.add_column(
        "requesttask",
        sa.Column("celery_id", sa.String(length=255), nullable=True, index=True),
    )


def downgrade():
    op.drop_column("requesttask", "celery_id")
    op.drop_column("privacyrequest", "celery_id")
