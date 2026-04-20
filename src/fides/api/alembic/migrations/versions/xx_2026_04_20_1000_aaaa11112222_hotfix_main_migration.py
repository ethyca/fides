"""DEMO: hotfix migration that landed on main

This simulates a hotfix migration added directly to main.
Both this and the "dev" migration share the same down_revision,
creating two alembic heads (a multi-head scenario).

Revision ID: aaaa11112222
Revises: d6e7f8a9b0c1
Create Date: 2026-04-20 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "aaaa11112222"
down_revision = "d6e7f8a9b0c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Simulated hotfix: add an index for a production query performance issue
    op.create_index(
        "ix_demo_hotfix_placeholder",
        "privacyrequest",
        ["status"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_demo_hotfix_placeholder", table_name="privacyrequest")
