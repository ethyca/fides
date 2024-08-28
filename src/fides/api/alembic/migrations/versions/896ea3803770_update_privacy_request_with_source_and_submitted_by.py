"""update privacy request with source and submitted_by

Revision ID: 896ea3803770
Revises: ffee79245c9a
Create Date: 2024-08-15 23:08:00.169034

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "896ea3803770"
down_revision = "ffee79245c9a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("consentrequest", sa.Column("source", sa.String(), nullable=True))
    op.add_column(
        "privacyrequest", sa.Column("submitted_by", sa.String(), nullable=True)
    )
    op.add_column("privacyrequest", sa.Column("source", sa.String(), nullable=True))
    op.create_foreign_key(
        "privacyrequest_submitted_by_fkey",
        "privacyrequest",
        "fidesuser",
        ["submitted_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(
        "privacyrequest_submitted_by_fkey", "privacyrequest", type_="foreignkey"
    )
    op.drop_column("privacyrequest", "source")
    op.drop_column("privacyrequest", "submitted_by")
    op.drop_column("consentrequest", "source")
