"""add consent request relationship

Revision ID: 61a922702f4c
Revises: f396c1f84b0f
Create Date: 2024-01-04 22:57:24.155581

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "61a922702f4c"
down_revision = "f396c1f84b0f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "custom_privacy_request_field",
        sa.Column("consent_request_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        None,
        "custom_privacy_request_field",
        "consentrequest",
        ["consent_request_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(None, "custom_privacy_request_field", type_="foreignkey")
    op.drop_column("custom_privacy_request_field", "consent_request_id")
