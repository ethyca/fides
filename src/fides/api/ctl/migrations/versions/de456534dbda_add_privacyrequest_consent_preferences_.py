"""add privacyrequest consent preferences and ruleuse table

Revision ID: de456534dbda
Revises: 3caf11127442
Create Date: 2023-01-03 22:59:45.144538

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "de456534dbda"
down_revision = "3caf11127442"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "privacyrequest",
        sa.Column(
            "executable_consent_preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    op.add_column(
        "consentrequest", sa.Column("privacy_request_id", sa.String(), nullable=True)
    )
    op.create_foreign_key(
        None, "consentrequest", "privacyrequest", ["privacy_request_id"], ["id"]
    )


def downgrade():
    op.drop_column("privacyrequest", "executable_consent_preferences")

    op.drop_constraint(
        "consentrequest_privacy_request_id_fkey", "consentrequest", type_="foreignkey"
    )
    op.drop_column("consentrequest", "privacy_request_id")
