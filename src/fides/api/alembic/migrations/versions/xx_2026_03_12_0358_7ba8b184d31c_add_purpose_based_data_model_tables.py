"""add purpose based data model tables

Revision ID: 7ba8b184d31c
Revises: 4ac4864180db
Create Date: 2026-03-12 03:58:30.461412

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "7ba8b184d31c"
down_revision = "4ac4864180db"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("data_consumer",
    sa.Column("id", sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    sa.Column("name", sa.String(), nullable=False),
    sa.Column("description", sa.String(), nullable=True),
    sa.Column("type", sa.String(), nullable=False),
    sa.Column("external_id", sa.String(), nullable=True),
    sa.Column("egress", sa.JSON(), nullable=True),
    sa.Column("ingress", sa.JSON(), nullable=True),
    sa.Column("data_shared_with_third_parties", sa.Boolean(), server_default="f", nullable=False),
    sa.Column("third_parties", sa.String(), nullable=True),
    sa.Column("shared_categories", sa.ARRAY(sa.String()), server_default="{}", nullable=False),
    sa.Column("contact_email", sa.String(), nullable=True),
    sa.Column("contact_slack_channel", sa.String(), nullable=True),
    sa.Column("contact_details", sa.JSON(), nullable=True),
    sa.Column("tags", sa.ARRAY(sa.String()), server_default="{}", nullable=False),
    sa.CheckConstraint("type != 'system'", name="ck_data_consumer_not_system"),
    sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_data_consumer_id"), "data_consumer", ["id"], unique=False)
    op.create_index(op.f("ix_data_consumer_type"), "data_consumer", ["type"], unique=False)
    op.create_table("data_purpose",
    sa.Column("id", sa.String(length=255), nullable=False),
    sa.Column("fides_key", sa.String(), nullable=False),
    sa.Column("organization_fides_key", sa.Text(), nullable=True),
    sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("description", sa.Text(), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    sa
    sa.PrimaryKeyConstraint("id", "fides_key")
    )
    op.create_index(op.f("ix_data_consumer_purpose_data_consumer_id"), "data_consumer_purpose", ["data_consumer_id"], unique=False)
    op.create_index(op.f("ix_data_consumer_purpose_data_purpose_id"), "data_consumer_purpose", ["data_purpose_id"], unique=False)
    op.create_index(op.f("ix_data_consumer_purpose_id"), "data_consumer_purpose", ["id"], unique=False)
    op.create_table("system_purpose",
    sa.Column("id", sa.String(length=255), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    sa.Column("system_id", sa.String(), nullable=False),
    sa.Column("data_purpose_id", sa.String(), nullable=False),
    sa.Column("assigned_by", sa.String(), nullable=True),
    sa.ForeignKeyConstraint(["assigned_by"], ["fidesuser.id"], ondelete="SET NULL"),
    sa.ForeignKeyConstraint(["data_purpose_id"], ["data_purpose.id"], ondelete="RESTRICT"),
    sa.ForeignKeyConstraint(["system_id"], ["ctl_systems.id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("id"),
    sa.UniqueConstraint("system_id", "data_purpose_id", name="uq_system_purpose")
    )
    op.create_index(op.f("ix_system_purpose_data_purpose_id"), "system_purpose", ["data_purpose_id"], unique=False)
    op.create_index(op.f("ix_system_purpose_id"), "system_purpose", ["id"], unique=False)
    op.create_index(op.f("ix_system_purpose_system_id"), "system_purpose", ["system_id"], unique=False)
    op.create_table("data_producer",
    sa.Column("id", sa.String(length=255), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    sa.Column("name", sa.String(), nullable=False),
    sa.Column("description", sa.String(), nullable=True),
    sa.Column("external_id", sa.String(), nullable=True),
    sa.Column("monitor_id", sa.String(), nullable=True),
    sa.Column("contact_email", sa.String(), nullable=True),
    sa.Column("contact_slack_channel", sa.String(), nullable=True),
    sa.Column("contact_details", sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(["monitor_id"], ["monitorconfig.id"], ),
    sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_data_producer_id"), "data_producer", ["id"], unique=False)
    op.create_table("data_producer_member",
    sa.Column("id", sa.String(length=255), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    sa.Column("data_producer_id", sa.String(), nullable=False),
    sa.Column("user_id", sa.String(), nullable=False),
    sa.ForeignKeyConstraint(["data_producer_id"], ["data_producer.id"], ondelete="CASCADE"),
    sa.ForeignKeyConstraint(["user_id"], ["fidesuser.id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("id"),
    sa.UniqueConstraint("data_producer_id", "user_id", name="uq_data_producer_member")
    )
    op.create_index(op.f("ix_data_producer_member_data_producer_id"), "data_producer_member", ["data_producer_id"], unique=False)
    op.create_index(op.f("ix_data_producer_member_id"), "data_producer_member", ["id"], unique=False)
    op.create_index(op.f("ix_data_producer_member_user_id"), "data_producer_member", ["user_id"], unique=False)
    op.add_column("ctl_datasets", sa.Column("data_purposes", postgresql.ARRAY(sa.String()), server_default="{}", nullable=True))
    op.add_column("ctl_datasets", sa.Column("data_producer_id", sa.String(), nullable=True))
    op.create_foreign_key("fk_ctl_datasets_data_producer_id", "ctl_datasets", "data_producer", ["data_producer_id"], ["id"], ondelete="SET NULL")
    # ### end Alembic commands ###


def downgrade():
    op.drop_constraint("fk_ctl_datasets_data_producer_id", "ctl_datasets", type_="foreignkey")
    op.drop_column("ctl_datasets", "data_producer_id")
    op.drop_column("ctl_datasets", "data_purposes")
    op.drop_index(op.f("ix_data_producer_member_user_id"), table_name="data_producer_member")
    op.drop_index(op.f("ix_data_producer_member_id"), table_name="data_producer_member")
    op.drop_index(op.f("ix_data_producer_member_data_producer_id"), table_name="data_producer_member")
    op.drop_table("data_producer_member")
    op.drop_index(op.f("ix_data_producer_id"), table_name="data_producer")
    op.drop_table("data_producer")
    op.drop_index(op.f("ix_system_purpose_system_id"), table_name="system_purpose")
    op.drop_index(op.f("ix_system_purpose_id"), table_name="system_purpose")
    op.drop_index(op.f("ix_system_purpose_data_purpose_id"), table_name="system_purpose")
    op.drop_table("system_purpose")
    op.drop_index(op.f("ix_data_consumer_purpose_id"), table_name="data_consumer_purpose")
    op.drop_index(op.f("ix_data_consumer_purpose_data_purpose_id"), table_name="data_consumer_purpose")
    op.drop_index(op.f("ix_data_consumer_purpose_data_consumer_id"), table_name="data_consumer_purpose")
    op.drop_table("data_consumer_purpose")
    op.drop_index(op.f("ix_data_purpose_id"), table_name="data_purpose")
    op.drop_index(op.f("ix_data_purpose_fides_key"), table_name="data_purpose")
    op.drop_index(op.f("ix_data_purpose_data_use"), table_name="data_purpose")
    op.drop_table("data_purpose")
    op.drop_index(op.f("ix_data_consumer_type"), table_name="data_consumer")
    op.drop_index(op.f("ix_data_consumer_id"), table_name="data_consumer")
    op.drop_table("data_consumer")
