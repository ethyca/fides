"""DEMO: merge divergent heads from main and dev

This is the resolution. When main is merged back into dev (or vice versa),
alembic detects two heads. Running `alembic merge heads` generates this
migration automatically. It has no schema changes — just unifies the chain.

In practice you'd run:
    alembic merge heads -m "merge main hotfix and dev feature"

Revision ID: cccc55556666
Revises: ('aaaa11112222', 'bbbb33334444')
Create Date: 2026-04-20 11:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = "cccc55556666"
down_revision = ("aaaa11112222", "bbbb33334444")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
