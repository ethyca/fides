"""SQLAlchemy model for MCP decision audit rows."""

from __future__ import annotations

from sqlalchemy import Boolean, Column, Enum, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from fides.api.db.base_class import Base


class MCPDecision(Base):
    __tablename__ = "mcp_decisions"

    id = Column(String(255), primary_key=True)
    delivery = Column(
        Enum("pdp", "gateway", name="mcp_decision_delivery", create_type=False),
        nullable=False,
    )
    consumer_fides_key = Column(String(255), nullable=False)
    consumer_mode = Column(
        Enum("agent", "interactive", name="mcp_consumer_mode", create_type=False),
        nullable=True,
    )
    upstream_id = Column(String(255), nullable=True)
    tool_name = Column(String(255), nullable=True)
    tool_schema_hash = Column(String(64), nullable=True)
    scrubbed_args_hash = Column(String(64), nullable=True)
    intent_resolution_json = Column(JSONB, nullable=True)
    purpose_source = Column(
        Enum("declared", "explicit_hint", "session", "inferred", name="mcp_purpose_source", create_type=False),
        nullable=True,
    )
    chat_context_used = Column(Boolean, nullable=False, default=False)
    evaluation_input_json = Column(JSONB, nullable=False)
    decision = Column(
        Enum("ALLOW", "DENY", "NO_DECISION", name="mcp_decision_outcome", create_type=False),
        nullable=False,
    )
    decisive_policy_key = Column(String(255), nullable=True)
    action_message = Column(Text, nullable=True)
    intent_source = Column(
        Enum("cache", "inference", "fallback", name="mcp_intent_source", create_type=False),
        nullable=True,
    )
    intent_ms = Column(Integer, nullable=True)
    evaluation_ms = Column(Integer, nullable=False)
    forward_ms = Column(Integer, nullable=True)
    error_type = Column(String(255), nullable=True)

    # mcp_decisions has no updated_at column — suppress the FidesBase default
    updated_at = None  # type: ignore[assignment]

    __table_args__ = (
        Index("ix_mcp_decisions_created_at", "created_at"),
        Index("ix_mcp_decisions_consumer", "consumer_fides_key", "created_at"),
    )
