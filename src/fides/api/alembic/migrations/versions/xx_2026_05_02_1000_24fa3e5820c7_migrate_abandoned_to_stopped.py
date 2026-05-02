"""migrate abandoned questionnaires to stopped

Revision ID: 24fa3e5820c7
Revises: ae57c33876cc
Create Date: 2026-05-02 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "24fa3e5820c7"
down_revision = "ae57c33876cc"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "UPDATE questionnaire SET status = 'stopped' WHERE status = 'abandoned'"
    )


def downgrade():
    op.execute(
        "UPDATE questionnaire SET status = 'abandoned' WHERE status = 'stopped'"
    )
