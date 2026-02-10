"""additional cors configurations

Revision ID: 4d64174f422e
Revises: f85bd4c08401
Create Date: 2026-02-10 18:50:33.983004

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4d64174f422e"
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
        sa.Column(
            "verify_email", sa.BOOLEAN(), server_default=sa.text("true"), nullable=False
        ),
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
