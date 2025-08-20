"""
Base taxonomy handler and core validation functions.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from sqlalchemy.orm import Session

from fides.api.db.base_class import FidesBase


class TaxonomyHandler(ABC):
    """Abstract handler for taxonomy CRUD operations."""

    def __init__(self, db: Session, taxonomy_type: str):
        self.db = db
        self.taxonomy_type = taxonomy_type

    @abstractmethod
    def get_model(self) -> Type[FidesBase]:
        pass

    @abstractmethod
    def get_elements(self, active_only: bool, parent_key: Optional[str]) -> List[Any]:
        pass

    @abstractmethod
    def get_element(self, fides_key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def create_element(self, element_data: Dict) -> Any:
        pass

    @abstractmethod
    def update_element(self, fides_key: str, element_data: Dict) -> Optional[Any]:
        pass

    @abstractmethod
    def delete_element(self, fides_key: str) -> None:
        pass
