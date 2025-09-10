"""add event audit table

Revision ID: 5fa78b1f324d
Revises: fd7571bef683
Create Date: 2025-09-09 17:51:15.715976

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5fa78b1f324d"
down_revision = "fd7571bef683"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "event_audit",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("resource_type", sa.String(), nullable=True),
        sa.Column("resource_identifier", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "event_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "status",
            sa.Enum("succeeded", "failed", name="eventauditstatus"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_event_audit_event_type"), "event_audit", ["event_type"], unique=False
    )
    op.create_index(op.f("ix_event_audit_id"), "event_audit", ["id"], unique=False)
    op.create_index(
        op.f("ix_event_audit_resource_identifier"),
        "event_audit",
        ["resource_identifier"],
        unique=False,
    )
    op.create_index(
        op.f("ix_event_audit_resource_type"),
        "event_audit",
        ["resource_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_event_audit_user_id"), "event_audit", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_event_audit_status"), "event_audit", ["status"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_event_audit_status"), table_name="event_audit")
    op.drop_index(op.f("ix_event_audit_user_id"), table_name="event_audit")
    op.drop_index(op.f("ix_event_audit_resource_type"), table_name="event_audit")
    op.drop_index(op.f("ix_event_audit_resource_identifier"), table_name="event_audit")
    op.drop_index(op.f("ix_event_audit_id"), table_name="event_audit")
    op.drop_index(op.f("ix_event_audit_event_type"), table_name="event_audit")
    op.drop_table("event_audit")
