"""Pre-computed per-monitor aggregate statistics for the action center dashboard."""

from sqlalchemy import Column, DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.sql import func

from fides.api.db.base_class import Base


class MonitorAggregateStatistics(Base):
    """Stores pre-computed aggregate statistics per monitor.

    Each row holds one monitor's statistics as JSONB, keyed by
    monitor_config_key. Cross-monitor aggregation is done in Python
    at read time by summing per-monitor stats.

    The JSONB shape varies by monitor_type — validated with Pydantic
    on write.
    """

    __tablename__ = "monitor_aggregate_statistics"  # type: ignore[assignment]

    monitor_config_key = Column(String, nullable=False)
    monitor_type = Column(String(50), nullable=False, index=True)
    statistics = Column(
        MutableDict.as_mutable(JSONB),
        nullable=False,
        server_default="{}",
        default=dict,
    )
    computed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "monitor_config_key",
            name="uq_monitor_agg_stats_monitor_config_key",
        ),
    )
