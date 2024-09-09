"""purpose_header_to_translations

Adds new purpose_header field to Experience Translation table and
Privacy Experience Config History table

Revision ID: 1332815dcd71
Revises: 9cad5a5c438c
Create Date: 2024-08-28 21:05:41.933572

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1332815dcd71"
down_revision = "9cad5a5c438c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "experiencetranslation", sa.Column("purpose_header", sa.String(), nullable=True)
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("purpose_header", sa.String(), nullable=True),
    )


def downgrade():
    op.drop_column("privacyexperienceconfighistory", "purpose_header")
    op.drop_column("experiencetranslation", "purpose_header")
