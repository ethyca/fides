"""additional sso provider configuration

Revision ID: 4c32b41a7e11
Revises: f85bd4c08401
Create Date: 2026-02-10 16:28:08.759425

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4c32b41a7e11"
down_revision = "f85bd4c08401"
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
