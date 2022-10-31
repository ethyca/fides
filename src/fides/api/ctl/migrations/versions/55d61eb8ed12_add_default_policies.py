"""add default policies

Revision ID: 55d61eb8ed12
Revises: b3b68c87c4a0
Create Date: 2022-06-13 19:26:24.197262

"""
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

revision = "55d61eb8ed12"
down_revision = "b3b68c87c4a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Data migration only."""

    # These data migrations have been removed, as they are now handled by
    # the `seed.py` module.
    pass


def downgrade() -> None:
    """Data migration only."""

    pass
