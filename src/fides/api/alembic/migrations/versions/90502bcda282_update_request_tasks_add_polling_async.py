"""Update Request Tasks

Revision ID: 90502bcda282
Revises: a7065df4dcf1
Create Date: 2025-08-05 16:31:45.335384

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '90502bcda282'
down_revision = 'a7065df4dcf1'
branch_labels = None
depends_on = None


def upgrade():
    # Polling async task: Determines if the task as a polling async strategy. Used to lookup the async tasks in the database.
    op.add_column('requesttask', sa.Column('polling_async_task', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('requesttask', 'polling_async_task')
