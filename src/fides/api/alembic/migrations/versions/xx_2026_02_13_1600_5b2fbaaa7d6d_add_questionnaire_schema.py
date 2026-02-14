"""add questionnaire and chat_message tables

Adds database tables for SME questionnaire sessions:
- questionnaire: tracks interactive questionnaire sessions linked to assessments
- chat_message: stores per-message conversation history with sender info

Revision ID: 5b2fbaaa7d6d
Revises: c0dc13ad2a05
Create Date: 2026-02-13 16:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5b2fbaaa7d6d"
down_revision = "c0dc13ad2a05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create questionnaire table
    op.create_table(
        "questionnaire",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("assessment_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "in_progress",
                "completed",
                "abandoned",
                name="questionnairestatus",
            ),
            nullable=False,
            server_default="in_progress",
        ),
        sa.Column("current_question_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_context", postgresql.JSONB(), nullable=False, server_default="{}"),
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
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_reminder_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reminder_count", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["assessment_id"],
            ["privacy_assessment.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_questionnaire_id"),
        "questionnaire",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_questionnaire_assessment_id"),
        "questionnaire",
        ["assessment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_questionnaire_status"),
        "questionnaire",
        ["status"],
        unique=False,
    )

    # Create chat_message table
    op.create_table(
        "chat_message",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("questionnaire_id", sa.String(), nullable=False),
        sa.Column("message_id", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sender_email", sa.String(), nullable=True),
        sa.Column("sender_display_name", sa.String(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("is_bot_message", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("question_index", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["questionnaire_id"],
            ["questionnaire.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_chat_message_id"),
        "chat_message",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_chat_message_questionnaire_id"),
        "chat_message",
        ["questionnaire_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_chat_message_sender_email"),
        "chat_message",
        ["sender_email"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_chat_message_sender_email"), table_name="chat_message")
    op.drop_index(op.f("ix_chat_message_questionnaire_id"), table_name="chat_message")
    op.drop_index(op.f("ix_chat_message_id"), table_name="chat_message")
    op.drop_table("chat_message")

    op.drop_index(op.f("ix_questionnaire_status"), table_name="questionnaire")
    op.drop_index(op.f("ix_questionnaire_assessment_id"), table_name="questionnaire")
    op.drop_index(op.f("ix_questionnaire_id"), table_name="questionnaire")
    op.drop_table("questionnaire")

    # Drop the enum type
    sa.Enum(name="questionnairestatus").drop(op.get_bind(), checkfirst=True)
