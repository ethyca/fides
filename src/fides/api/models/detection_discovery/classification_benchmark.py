"""
Database model for classification benchmark results.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import ARRAY, Column, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base, FidesBase


class ClassificationBenchmark(Base, FidesBase):
    """
    Database model for storing classification benchmark results.

    This model stores the results of classification accuracy benchmarks that compare
    system-assigned classifications on staged resources with ground truth data from datasets.
    """

    @property
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
        default=dict,
    )

    @classmethod
    def store_benchmark(
        cls, db: Session, benchmark_data: Dict[str, Any]
    ) -> "ClassificationBenchmark":
        """
        Store a benchmark result in the database.

        Args:
            db: Database session
            benchmark_data: Dictionary containing benchmark data

        Returns:
            The created ClassificationBenchmark instance
        """
        benchmark = cls(
            monitor_config_key=benchmark_data["monitor_config_key"],
            dataset_fides_key=benchmark_data["dataset_fides_key"],
            resource_urn=benchmark_data["resource_urn"],
            created_at=benchmark_data["created_at"],
            overall_metrics=benchmark_data["overall_metrics"],
            field_accuracy_details=benchmark_data["field_accuracy_details"],
        )
        db.add(benchmark)
        return benchmark

    @classmethod
    def get_benchmark(
        cls, db: Session, benchmark_id: str
    ) -> Optional["ClassificationBenchmark"]:
        """
        Retrieve a benchmark by ID.

        Args:
            db: Database session
            benchmark_id: The benchmark ID to retrieve

        Returns:
            The ClassificationBenchmark instance or None if not found
        """
        return db.query(cls).filter(cls.id == benchmark_id).first()

    @classmethod
    def delete_benchmark(cls, db: Session, benchmark_id: str) -> bool:
        """
        Delete a benchmark by ID.

        Args:
            db: Database session
            benchmark_id: The benchmark ID to delete

        Returns:
            True if deleted, False if not found
        """
        benchmark = cls.get_benchmark(db, benchmark_id)
        if benchmark:
            db.delete(benchmark)
            return True
        return False

    @classmethod
    def clear_all(cls, db: Session) -> int:
        """
        Clear all benchmark results.

        Args:
            db: Database session

        Returns:
            Number of benchmarks deleted
        """
        count = db.query(cls).count()
        db.query(cls).delete()
        return count
