"""fix message template indexes

Revision ID: 52b2cfd1af47
Revises: f17f92237383
Create Date: 2023-09-15 21:29:23.060892

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "52b2cfd1af47"
down_revision = "f17f92237383"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index("ix_messagingtemplate_id", table_name="messaging_template")
    op.drop_index("ix_messagingtemplate_key", table_name="messaging_template")
    op.create_index(
        op.f("ix_messaging_template_id"), "messaging_template", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_messaging_template_key"), "messaging_template", ["key"], unique=True
    )


def downgrade():
    op.drop_index(op.f("ix_messaging_template_key"), table_name="messaging_template")
    op.drop_index(op.f("ix_messaging_template_id"), table_name="messaging_template")
    op.create_index(
        "ix_messagingtemplate_key", "messaging_template", ["key"], unique=False
    )
    op.create_index(
        "ix_messagingtemplate_id", "messaging_template", ["id"], unique=False
    )
