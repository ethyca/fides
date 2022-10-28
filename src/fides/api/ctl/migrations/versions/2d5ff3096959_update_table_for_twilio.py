"""Update table for twilio
Revision ID: 2d5ff3096959
Revises: fb6b0150d6e4
Create Date: 2022-10-21 22:10:48.899562
"""
import sqlalchemy_utils
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2d5ff3096959'
down_revision = 'fb6b0150d6e4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('messagingconfig',
                    sa.Column('id', sa.String(length=255), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
                    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
                    sa.Column('key', sa.String(), nullable=False),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('service_type', sa.Enum('MAILGUN', 'TWILIO_TEXT', 'TWILIO_EMAIL', name='messagingservicetype'), nullable=False),
                    sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
                    sa.Column('secrets', sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_messagingconfig_id'), 'messagingconfig', ['id'], unique=False)
    op.create_index(op.f('ix_messagingconfig_key'), 'messagingconfig', ['key'], unique=True)
    op.create_index(op.f('ix_messagingconfig_name'), 'messagingconfig', ['name'], unique=True)
    op.create_index(op.f('ix_messagingconfig_service_type'), 'messagingconfig', ['service_type'], unique=True)
    op.drop_index('ix_emailconfig_id', table_name='emailconfig')
    op.drop_index('ix_emailconfig_key', table_name='emailconfig')
    op.drop_index('ix_emailconfig_name', table_name='emailconfig')
    op.drop_index('ix_emailconfig_service_type', table_name='emailconfig')
    op.drop_table('emailconfig')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('emailconfig',
                    sa.Column('id', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
                    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
                    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
                    sa.Column('key', sa.VARCHAR(), autoincrement=False, nullable=False),
                    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=True),
                    sa.Column('service_type', postgresql.ENUM('MAILGUN', name='emailservicetype'), autoincrement=False, nullable=False),
                    sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
                    sa.Column('secrets', sa.VARCHAR(), autoincrement=False, nullable=True),
                    sa.PrimaryKeyConstraint('id', name='emailconfig_pkey')
                    )
    op.create_index('ix_emailconfig_service_type', 'emailconfig', ['service_type'], unique=False)
    op.create_index('ix_emailconfig_name', 'emailconfig', ['name'], unique=False)
    op.create_index('ix_emailconfig_key', 'emailconfig', ['key'], unique=False)
    op.create_index('ix_emailconfig_id', 'emailconfig', ['id'], unique=False)
    op.drop_index(op.f('ix_messagingconfig_service_type'), table_name='messagingconfig')
    op.drop_index(op.f('ix_messagingconfig_name'), table_name='messagingconfig')
    op.drop_index(op.f('ix_messagingconfig_key'), table_name='messagingconfig')
    op.drop_index(op.f('ix_messagingconfig_id'), table_name='messagingconfig')
    op.drop_table('messagingconfig')
    # ### end Alembic commands ###