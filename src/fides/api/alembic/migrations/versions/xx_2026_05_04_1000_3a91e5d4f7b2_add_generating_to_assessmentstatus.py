"""add generating to assessmentstatus

Revision ID: 3a91e5d4f7b2
Revises: ae57c33876cc
Create Date: 2026-05-04 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "3a91e5d4f7b2"
down_revision = "ae57c33876cc"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE assessmentstatus ADD VALUE IF NOT EXISTS 'generating'")


def downgrade():
    # Any rows still in 'generating' at downgrade time fall back to 'in_progress'
    # (the state they would have landed in once LLM work completed).
    op.execute(
        "UPDATE privacy_assessment SET status = 'in_progress' WHERE status = 'generating'"
    )

    op.execute("ALTER TYPE assessmentstatus RENAME TO assessmentstatus_old")
    op.execute(
        "CREATE TYPE assessmentstatus AS ENUM ("
        "'in_progress', 'completed', 'outdated'"
        ")"
    )
    op.execute(
        "ALTER TABLE privacy_assessment ALTER COLUMN status TYPE assessmentstatus USING "
        "status::text::assessmentstatus"
    )
    op.execute("DROP TYPE assessmentstatus_old")
