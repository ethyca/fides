"""additional tcf fields system

Revision ID: c5a218831820
Revises: 81226042d7d4
Create Date: 2023-10-05 15:40:09.294013

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c5a218831820"
down_revision = "81226042d7d4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "ctl_systems",
        sa.Column("cookie_max_age_seconds", sa.Integer(), nullable=True),
    )
    op.add_column(
        "ctl_systems",
        sa.Column(
            "uses_cookies",
            sa.Boolean(),
            nullable=False,
            server_default="f",
        ),
    )
    op.add_column(
        "ctl_systems",
        sa.Column(
            "cookie_refresh",
            sa.Boolean(),
            nullable=False,
            server_default="f",
        ),
    )
    op.add_column(
        "ctl_systems",
        sa.Column(
            "uses_non_cookie_access",
            sa.Boolean(),
            nullable=False,
            server_default="f",
        ),
    )
    op.add_column(
        "ctl_systems",
        sa.Column("legitimate_interest_disclosure_url", sa.String(), nullable=True),
    )

    op.add_column(
        "privacydeclaration",
        sa.Column(
            "flexible_legal_basis_for_processing",
            sa.Boolean(),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column(
        "ctl_systems",
        "cookie_max_age_seconds",
    )
    op.drop_column(
        "ctl_systems",
        "uses_cookies",
    )
    op.drop_column(
        "ctl_systems",
        "cookie_refresh",
    )
    op.drop_column(
        "ctl_systems",
        "uses_non_cookie_access",
    )
    op.drop_column(
        "ctl_systems",
        "legitimate_interest_disclosure_url",
    )
    op.drop_column(
        "privacydeclaration",
        "flexible_legal_basis_for_processing",
    )
