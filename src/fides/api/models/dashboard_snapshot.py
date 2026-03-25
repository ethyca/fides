"""Daily metric snapshots for dashboard trend sparklines."""

from sqlalchemy import Column, Date, Float, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from fides.api.db.base_class import Base


class DashboardSnapshot(Base):
    """Stores daily metric values for dashboard trend visualization.

    Each row is one metric on one day. The seed task populates historical
    data; a future Celery beat task will append daily snapshots.
    """

    __tablename__ = "dashboard_snapshot"  # type: ignore[assignment]

    snapshot_date = Column(Date, nullable=False, index=True)
    metric_key = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=True, server_default="{}")

    __table_args__ = (
        UniqueConstraint(
            "snapshot_date",
            "metric_key",
            name="uq_dashboard_snapshot_date_metric",
        ),
    )
