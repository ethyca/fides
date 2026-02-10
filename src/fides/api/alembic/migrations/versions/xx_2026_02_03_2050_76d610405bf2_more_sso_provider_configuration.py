"""more sso provider configuration

Revision ID: 76d610405bf2
Revises: 6d5f70dd0ba5
Create Date: 2026-02-03 20:50:25.687933

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "76d610405bf2"
down_revision = "b2c3d4e5f6g7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add SSO provider configuration columns."""
    op.add_column(
        "openid_provider", sa.Column("scopes", sa.ARRAY(sa.String()), nullable=True)
    )
    op.add_column(
        "openid_provider", sa.Column("email_field", sa.String(), nullable=True)
    )
    op.add_column(
        "openid_provider",
        sa.Column("verify_email", sa.Boolean(), server_default="t", nullable=False),
    )
    op.add_column(
        "openid_provider", sa.Column("verify_email_field", sa.String(), nullable=True)
    )


def downgrade() -> None:
    """Remove SSO provider configuration columns."""
    op.drop_column("openid_provider", "verify_email_field")
    op.drop_column("openid_provider", "verify_email")
    op.drop_column("openid_provider", "email_field")
    op.drop_column("openid_provider", "scopes")
