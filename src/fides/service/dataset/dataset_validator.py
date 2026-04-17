from abc import ABC, abstractmethod
from typing import List, Optional, Type, TypeVar

from fideslang.models import Dataset as FideslangDataset
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.schemas.dataset import DatasetTraversalDetails, ValidateDatasetResponse

T = TypeVar("T", bound="DatasetValidationStep")


class DatasetValidationContext:
    """Context object holding state for validation"""

    def __init__(
        self,
        db: Session,
        dataset: FideslangDataset,
        connection_config: Optional[ConnectionConfig] = None,
    ):
        self.db = db
        self.dataset = dataset
        self.connection_config = connection_config
        self.traversal_details: Optional[DatasetTraversalDetails] = None


class DatasetValidationStep(ABC):
    """Abstract base class for dataset validation steps"""

    @classmethod
    def _find_all_validation_steps(cls: Type[T]) -> List[Type[T]]:
        """Find all subclasses of DatasetValidationStep"""
        return cls.__subclasses__()

    @abstractmethod
    def validate(self, context: DatasetValidationContext) -> None:
        """Perform validation step"""


class DatasetValidator:
    """Dataset validator that allows selective validation steps"""

    def __init__(
        self,
        db: Session,
        dataset: FideslangDataset,
        connection_config: Optional[ConnectionConfig] = None,
        skip_steps: Optional[List[Type[DatasetValidationStep]]] = None,
    ):
        self.context = DatasetValidationContext(db, dataset, connection_config)
        self.skip_steps = skip_steps or []
        self.validation_steps = [
            step()
            for step in DatasetValidationStep._find_all_validation_steps()
            if step not in self.skip_steps
        ]

    def validate(self) -> ValidateDatasetResponse:
        """Execute selected validation steps and return response"""
        for step in self.validation_steps:
            step.validate(self.context)

        return ValidateDatasetResponse(
            dataset=self.context.dataset,
            traversal_details=self.context.traversal_details,
        )
