"""
Base taxonomy handler and core validation functions.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from sqlalchemy.orm import Session


class TaxonomyHandler(ABC):
    """Abstract handler for taxonomy CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def get_model(self, taxonomy_type: str) -> Type:
        pass

    @abstractmethod
    def get_elements(
        self, taxonomy_type: str, active_only: bool, parent_key: Optional[str]
    ) -> List[Any]:
        pass

    @abstractmethod
    def get_element(self, taxonomy_type: str, fides_key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def create_element(self, taxonomy_type: str, element_data: Dict) -> Any:
        pass

    @abstractmethod
    def update_element(
        self, taxonomy_type: str, fides_key: str, element_data: Dict
    ) -> Optional[Any]:
        pass

    @abstractmethod
    def delete_element(self, taxonomy_type: str, fides_key: str) -> bool:
        pass
