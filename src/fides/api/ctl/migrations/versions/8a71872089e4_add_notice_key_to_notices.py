"""add_notice_key_to_notices

Revision ID: 8a71872089e4
Revises: 2661f31daffb
Create Date: 2023-05-18 19:48:33.268790

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8a71872089e4"
down_revision = "2661f31daffb"
branch_labels = None
depends_on = None


def upgrade():
    """Add new non-nullable notice_key fields to privacy notice and notice history tables
    and automatically create existing notice keys from the notice names.

    Notice keys are not unique.
    """
    op.add_column("privacynotice", sa.Column("notice_key", sa.String(), nullable=True))
    op.add_column(
        "privacynoticehistory", sa.Column("notice_key", sa.String(), nullable=True)
    )

    op.execute(
        "update privacynoticehistory set notice_key = LOWER(REPLACE(name, ' ', '_'));"
    )
    op.execute("update privacynotice set notice_key = LOWER(REPLACE(name, ' ', '_'));")

    op.alter_column("privacynotice", "notice_key", nullable=False)
    op.alter_column("privacynoticehistory", "notice_key", nullable=False)


def downgrade():
    op.drop_column("privacynoticehistory", "notice_key")
    op.drop_column("privacynotice", "notice_key")
