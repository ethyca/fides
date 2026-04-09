"""add client id columns to user submitted data

Revision ID: d76443a8a2e3
Revises: 6a42f48c23dd
Create Date: 2026-04-09 08:38:43.724458

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd76443a8a2e3'
down_revision = '6a42f48c23dd'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "comment",
        sa.Column(
            "client_id",
            sa.String(),
            sa.ForeignKey("client.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "attachment",
        sa.Column(
            "client_id",
            sa.String(),
            sa.ForeignKey("client.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "event_audit",
        sa.Column(
            "client_id",
            sa.String(),
            sa.ForeignKey("client.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("event_audit", "client_id")
    op.drop_column("attachment", "client_id")
    op.drop_column("comment", "client_id")
