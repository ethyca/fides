"""
Database model for classification benchmark results.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import ARRAY, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Query, RelationshipProperty, Session, relationship

from fides.api.db.base_class import Base, FidesBase
from fides.api.models.detection_discovery.core import MonitorConfig
from fides.api.models.sql_models import Dataset  # type: ignore[attr-defined]


class ClassificationBenchmark(Base, FidesBase):
    """
    Database model for storing classification benchmark results.

    This model stores the results of classification accuracy benchmarks that compare
    system-assigned classifications on staged resources with ground truth data from datasets.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "classification_benchmark"

    # Foreign key relationships
    monitor_config_key = Column(
        String,
        ForeignKey(MonitorConfig.key, ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dataset_fides_key = Column(
        String,
        ForeignKey(Dataset.fides_key, ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Resource URNs (array of strings)
    resource_urns = Column(
        ARRAY(String),
        nullable=False,
        server_default="{}",
        default=list,
    )

    # Overall accuracy metrics stored as JSONB
    overall_metrics = Column(
        MutableDict.as_mutable(JSONB),
        nullable=True,
        server_default=None,
        default=None,
    )

    # Field-level accuracy details stored as JSONB array
    field_accuracy_details = Column(
        ARRAY(JSONB),
        nullable=False,
        server_default="{}",
        default=list,
    )

    # Status and messages for tracking benchmark execution
    status = Column(
        String,
        nullable=False,
        server_default="'pending'",
        default="pending",
        index=True,
    )
    messages = Column(
        ARRAY(String),
        nullable=False,
        server_default="{}",
        default=list,
    )

    # Relationships
    monitor_config: RelationshipProperty[MonitorConfig] = relationship(
        MonitorConfig,
        foreign_keys=[monitor_config_key],
        primaryjoin="ClassificationBenchmark.monitor_config_key == MonitorConfig.key",
    )

    dataset: RelationshipProperty[Dataset] = relationship(
        Dataset,
        foreign_keys=[dataset_fides_key],
        primaryjoin="ClassificationBenchmark.dataset_fides_key == Dataset.fides_key",
    )

    @classmethod
    def list_benchmarks(
        cls,
        db: Session,
        monitor_config_key: Optional[str] = None,
        dataset_fides_key: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> Query:
        """
        Get a filtered query for benchmarks.

        Args:
            db: Database session
            monitor_config_key: Filter by monitor config key
            dataset_fides_key: Filter by dataset fides key
            created_after: Filter by creation date (inclusive)
            created_before: Filter by creation date (exclusive)
            status: Filter by status
        Returns:
            Filtered query (not executed)
        """
        # Build the query with filters
        query = db.query(cls)

        # Apply filters
        if monitor_config_key:
            query = query.filter(cls.monitor_config_key == monitor_config_key)
        if dataset_fides_key:
            query = query.filter(cls.dataset_fides_key == dataset_fides_key)
        if created_after:
            query = query.filter(cls.created_at >= created_after)
        if created_before:
            query = query.filter(cls.created_at < created_before)
        if status:
            query = query.filter(cls.status == status)

        # Apply sorting
        query = query.order_by(cls.created_at.desc())

        return query
