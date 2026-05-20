"""SQLAlchemy model for MCP-specific consumer settings."""

from __future__ import annotations

from sqlalchemy import Boolean, Column, Enum, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from fides.api.db.base_class import Base


class MCPConsumerSettings(Base):
    __tablename__ = "mcp_consumer_settings"

    consumer_fides_key = Column(String(255), nullable=False)
    mode = Column(
        Enum("agent", "interactive", name="mcp_consumer_mode", create_type=False),
        nullable=False,
    )
    allowable_purpose_keys = Column(
        ARRAY(String(255)), nullable=False, default=list, server_default="{}"
    )
    chat_context_inference = Column(Boolean, nullable=False, default=False)
    confidence_floor_overrides = Column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "consumer_fides_key", name="uq_mcp_consumer_settings_consumer_fides_key"
        ),
    )
