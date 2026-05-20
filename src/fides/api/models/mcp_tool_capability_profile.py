"""SQLAlchemy model for cached tool capability profiles."""

from __future__ import annotations

from sqlalchemy import Column, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from fides.api.db.base_class import Base


class MCPToolCapabilityProfile(Base):
    __tablename__ = "mcp_tool_capability_profiles"

    id = Column(String(255), primary_key=True)
    upstream_key = Column(String(255), nullable=False)
    tool_name = Column(String(255), nullable=False)
    tool_schema_hash = Column(String(64), nullable=False)
    profile_json = Column(JSONB, nullable=False)
    model_used = Column(String(255), nullable=False)
    model_metadata = Column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "upstream_key", "tool_name", "tool_schema_hash",
            name="uq_capability_profile_upstream_tool_schema",
        ),
    )
