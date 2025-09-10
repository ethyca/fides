"""
Database model for classification benchmark results.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import ARRAY, Column, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Query, Session

from fides.api.db.base_class import Base


class ClassificationBenchmark(Base):
    """
    Database model for storing classification benchmark results.

    This model stores the results of classification accuracy benchmarks that compare
    system-assigned classifications on staged resources with ground truth data from datasets.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "classification_benchmark"

    # Basic benchmark information
    monitor_config_key = Column(String, nullable=False, index=True)
    dataset_fides_key = Column(String, nullable=False, index=True)
    resource_urn = Column(String, nullable=False)

    # Overall accuracy metrics stored as JSONB
    overall_metrics = Column(
        MutableDict.as_mutable(JSONB),
        nullable=False,
        server_default="{}",
        default=dict,
    )

    # Field-level accuracy details stored as JSONB array
    field_accuracy_details = Column(
        ARRAY(JSONB),
        nullable=False,
        server_default="{}",
        default=list,
    )

    @classmethod
    def list_benchmarks(
        cls,
        db: Session,
        monitor_config_key: Optional[str] = None,
        dataset_fides_key: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
    ) -> Query:
        """
        Get a filtered query for benchmarks.

        Args:
            db: Database session
            monitor_config_key: Filter by monitor config key
            dataset_fides_key: Filter by dataset fides key
            created_after: Filter by creation date (inclusive)
            created_before: Filter by creation date (exclusive)

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

        # Apply sorting
        query = query.order_by(cls.created_at.desc())

        return query
