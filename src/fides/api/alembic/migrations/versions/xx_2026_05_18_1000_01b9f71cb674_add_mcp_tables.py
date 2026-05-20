"""add mcp tables (decisions, consumer settings, tool capability profiles)

Revision ID: 01b9f71cb674
Revises: b034cd68950d
Create Date: 2026-05-19 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "01b9f71cb674"
down_revision = "b034cd68950d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mcp_consumer_settings",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("consumer_fides_key", sa.String(length=255), nullable=False),
        sa.Column(
            "mode",
            sa.Enum("agent", "interactive", name="mcp_consumer_mode"),
            nullable=False,
        ),
        sa.Column(
            "allowable_purpose_keys",
            postgresql.ARRAY(sa.String(length=255)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "chat_context_inference",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "confidence_floor_overrides",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "consumer_fides_key", name="uq_mcp_consumer_settings_consumer_fides_key"
        ),
    )

    op.create_table(
        "mcp_tool_capability_profiles",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("upstream_key", sa.String(length=255), nullable=False),
        sa.Column("tool_name", sa.String(length=255), nullable=False),
        sa.Column("tool_schema_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "profile_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("model_used", sa.String(length=255), nullable=False),
        sa.Column(
            "model_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_used_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "upstream_key", "tool_name", "tool_schema_hash",
            name="uq_capability_profile_upstream_tool_schema",
        ),
    )

    op.create_table(
        "mcp_decisions",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "delivery",
            sa.Enum("pdp", "gateway", name="mcp_decision_delivery"),
            nullable=False,
        ),
        sa.Column("consumer_fides_key", sa.String(length=255), nullable=False),
        sa.Column(
            "consumer_mode",
            sa.Enum("agent", "interactive", name="mcp_consumer_mode"),
            nullable=True,  # nullable for evaluate_policy callers without a consumer mode
        ),
        sa.Column("upstream_id", sa.String(length=255), nullable=True),
        sa.Column("tool_name", sa.String(length=255), nullable=True),
        sa.Column("tool_schema_hash", sa.String(length=64), nullable=True),
        sa.Column("scrubbed_args_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "intent_resolution_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "purpose_source",
            sa.Enum("declared", "explicit_hint", "session", "inferred", name="mcp_purpose_source"),
            nullable=True,
        ),
        sa.Column("chat_context_used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "evaluation_input_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "decision",
            sa.Enum("ALLOW", "DENY", "NO_DECISION", name="mcp_decision_outcome"),
            nullable=False,
        ),
        sa.Column("decisive_policy_key", sa.String(length=255), nullable=True),
        sa.Column("action_message", sa.Text(), nullable=True),
        sa.Column(
            "intent_source",
            sa.Enum("cache", "inference", "fallback", name="mcp_intent_source"),
            nullable=True,
        ),
        sa.Column("intent_ms", sa.Integer(), nullable=True),
        sa.Column("evaluation_ms", sa.Integer(), nullable=False),
        sa.Column("forward_ms", sa.Integer(), nullable=True),
        sa.Column("error_type", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mcp_decisions_created_at", "mcp_decisions", ["created_at"])
    op.create_index(
        "ix_mcp_decisions_consumer", "mcp_decisions", ["consumer_fides_key", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_mcp_decisions_consumer", table_name="mcp_decisions")
    op.drop_index("ix_mcp_decisions_created_at", table_name="mcp_decisions")
    op.drop_table("mcp_decisions")
    op.drop_table("mcp_tool_capability_profiles")
    op.drop_table("mcp_consumer_settings")
    sa.Enum(name="mcp_intent_source").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="mcp_purpose_source").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="mcp_decision_outcome").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="mcp_decision_delivery").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="mcp_consumer_mode").drop(op.get_bind(), checkfirst=True)
