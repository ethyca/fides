"""add_reject_all_mechanism_to_privacy_experience_config

Revision ID: 67d01c4e124e
Revises: 1d2f04ac19f2
Create Date: 2025-03-27 15:26:24.635947

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "67d01c4e124e"
down_revision = "1d2f04ac19f2"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    # Add the reject all mechanism enum and column
    op.execute(
        "CREATE TYPE rejectallmechanism AS ENUM ('REJECT_ALL', 'REJECT_CONSENT_ONLY')"
    )
    op.add_column(
        "privacyexperienceconfig",
        sa.Column(
            "reject_all_mechanism",
            sa.Enum("REJECT_ALL", "REJECT_CONSENT_ONLY", name="rejectallmechanism"),
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column(
            "reject_all_mechanism",
            sa.Enum("REJECT_ALL", "REJECT_CONSENT_ONLY", name="rejectallmechanism"),
            nullable=True,
        ),
    )

    # Data migration - set the reject_all_mechanism for all TCF experience configs to REJECT_ALL
    op.execute(
        "UPDATE privacyexperienceconfig SET reject_all_mechanism = 'REJECT_ALL' WHERE component = 'tcf_overlay'"
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("privacyexperienceconfig", "reject_all_mechanism")
    op.drop_column("privacyexperienceconfighistory", "reject_all_mechanism")
    op.execute("DROP TYPE IF EXISTS rejectallmechanism")
    # ### end Alembic commands ###
