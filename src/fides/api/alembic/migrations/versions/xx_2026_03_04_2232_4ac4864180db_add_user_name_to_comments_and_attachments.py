"""add username to comments and attachments

Revision ID: 4ac4864180db
Revises: 04281f44cc0b
Create Date: 2026-03-04 22:32:35.300783

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4ac4864180db"
down_revision = "04281f44cc0b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("comment", sa.Column("username", sa.String(), nullable=True))
    op.add_column("attachment", sa.Column("username", sa.String(), nullable=True))
    op.execute(
        """
        UPDATE comment AS c
        SET username = u.username
        FROM fidesuser AS u
        WHERE c.user_id = u.id
          AND c.username IS NULL
        """
    )
    op.execute(
        """
        UPDATE attachment AS a
        SET username = u.username
        FROM fidesuser AS u
        WHERE a.user_id = u.id
          AND a.username IS NULL
        """
    )


def downgrade():
    op.drop_column("comment", "username")
    op.drop_column("attachment", "username")
