"""
Database model for classification benchmark results.
"""

from typing import Any, Dict, Optional

from sqlalchemy import ARRAY, Column, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict

from fides.api.db.base_class import Base, FidesBase


class ClassificationBenchmark(Base, FidesBase):
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
        default=dict,
    )
