"""
Legacy taxonomy handler for DataCategory, DataUse, and DataSubject models.
"""

from typing import Dict, List, Optional, Type, Union

from sqlalchemy.orm import Query, Session

from fides.api.models.sql_models import (  # type:ignore[attr-defined]
    DataCategory,
    DataSubject,
    DataUse,
)

from .base import TaxonomyHandler


class LegacyTaxonomyHandler(TaxonomyHandler):
    """Handler for legacy taxonomy models (DataCategory, DataUse, DataSubject)."""

    def __init__(self, db: Session) -> None:
        super().__init__(db)
        self.models = {
            "data_categories": DataCategory,
            "data_uses": DataUse,
            "data_subjects": DataSubject,
        }

    def get_elements(
        self, taxonomy_type: str, active_only: bool, parent_key: Optional[str]
    ) -> List[Union[DataCategory, DataUse, DataSubject]]:
        model_class = self.get_model(taxonomy_type)
        query = self._build_query(model_class, active_only, parent_key)
        return query.all()

    def get_element(
        self, taxonomy_type: str, fides_key: str
    ) -> Optional[Union[DataCategory, DataUse, DataSubject]]:
        model_class = self.get_model(taxonomy_type)
        element = (
            self.db.query(model_class)
            .filter(model_class.fides_key == fides_key)
            .first()
        )
        return element

    def create_element(
        self, taxonomy_type: str, element_data: Dict
    ) -> Union[DataCategory, DataUse, DataSubject]:
        model_class = self.get_model(taxonomy_type)
        element = model_class.create(self.db, data=element_data)
        return element

    def update_element(
        self, taxonomy_type: str, fides_key: str, element_data: Dict
    ) -> Optional[Union[DataCategory, DataUse, DataSubject]]:
        model_class = self.get_model(taxonomy_type)
        element = (
            self.db.query(model_class)
            .filter(model_class.fides_key == fides_key)
            .first()
        )

        if not element:
            return None

        return element.update(db=self.db, data=element_data)

    def delete_element(self, taxonomy_type: str, fides_key: str) -> bool:
        model_class = self.get_model(taxonomy_type)
        element = (
            self.db.query(model_class)
            .filter(model_class.fides_key == fides_key)
            .first()
        )

        if element:
            self.db.delete(element)
            return True
        return False

    def get_model(self, taxonomy_type: str) -> Type:
        model_class = self.models.get(taxonomy_type)
        if not model_class:
            raise ValueError(
                f"Taxonomy type '{taxonomy_type}' not supported. Supported types: {list(self.models.keys())}"
            )
        return model_class

    def _build_query(
        self, model_class: Type, active_only: bool, parent_key: Optional[str]
    ) -> Query:
        query = self.db.query(model_class)
        if active_only:
            query = query.filter(model_class.active.is_(True))
        if parent_key and hasattr(model_class, "parent_key"):
            query = query.filter(model_class.parent_key == parent_key)
        return query
