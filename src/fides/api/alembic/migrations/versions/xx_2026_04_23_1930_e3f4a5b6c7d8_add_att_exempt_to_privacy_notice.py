"""Add att_exempt column to privacy notice tables

Adds a boolean att_exempt field to privacynotice, privacynoticehistory, and
privacynoticetemplate. When False (default), the notice is controlled by Apple's
App Tracking Transparency (ATT) prompt — it is automatically turned off and locked
when the user denies ATT. When True, the notice is exempt from ATT and remains
user-toggleable regardless of the ATT decision.

Revision ID: e3f4a5b6c7d8
Revises: d71c7d274c04
Create Date: 2026-04-23 19:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e3f4a5b6c7d8"
down_revision = "d71c7d274c04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "privacynotice",
        sa.Column(
            "att_exempt",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "privacynoticehistory",
        sa.Column(
            "att_exempt",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "privacynoticetemplate",
        sa.Column(
            "att_exempt",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("privacynoticetemplate", "att_exempt")
    op.drop_column("privacynoticehistory", "att_exempt")
    op.drop_column("privacynotice", "att_exempt")
