"""drop userregistration table

Revision ID: 4e9c4168bf18
Revises: ddec29f24945
Create Date: 2023-10-26 12:15:06.316303

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4e9c4168bf18'
down_revision = 'ddec29f24945'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_userregistration_id', table_name='userregistration')
    op.drop_table('userregistration')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('userregistration',
    sa.Column('id', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('user_email', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('user_organization', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('analytics_id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('opt_in', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='userregistration_pkey'),
    sa.UniqueConstraint('analytics_id', name='userregistration_analytics_id_key')
    )
    op.create_index('ix_userregistration_id', 'userregistration', ['id'], unique=False)
    # ### end Alembic commands ###
