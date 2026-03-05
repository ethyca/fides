"""Add questionnaire_tone_prompt to privacy_assessment_config

Revision ID: ca2c622bad39
Revises: 074796d61d8a
Create Date: 2026-03-03 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "ca2c622bad39"
down_revision = "074796d61d8a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "privacy_assessment_config",
        sa.Column(
            "questionnaire_tone_prompt",
            sa.Text(),
            nullable=True,
            comment="Custom tone prompt for questionnaire messages. If null, uses default.",
        ),
    )


def downgrade():
    op.drop_column("privacy_assessment_config", "questionnaire_tone_prompt")
