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

    def __init__(self, db: Session, taxonomy_type: str) -> None:
        super().__init__(db, taxonomy_type)
        self.models = {
            "data_categories": DataCategory,
            "data_uses": DataUse,
            "data_subjects": DataSubject,
        }
        if taxonomy_type not in self.models:
            raise ValueError(
                f"Taxonomy type '{taxonomy_type}' not supported. Supported types: {list(self.models.keys())}"
            )

    def get_elements(
        self, active_only: bool, parent_key: Optional[str]
    ) -> List[Union[DataCategory, DataUse, DataSubject]]:
        model_class = self.get_model()
        query = self._build_query(model_class, active_only, parent_key)
        return query.all()

    def get_element(
        self, fides_key: str
    ) -> Optional[Union[DataCategory, DataUse, DataSubject]]:
        model_class = self.get_model()
        element = (
            self.db.query(model_class)
            .filter(model_class.fides_key == fides_key)
            .first()
        )
        return element

    def create_element(
        self, element_data: Dict
    ) -> Union[DataCategory, DataUse, DataSubject]:
        model_class = self.get_model()
        element = model_class.create(self.db, data=element_data)
        return element

    def update_element(
        self, fides_key: str, element_data: Dict
    ) -> Optional[Union[DataCategory, DataUse, DataSubject]]:
        model_class = self.get_model()
        element = (
            self.db.query(model_class)
            .filter(model_class.fides_key == fides_key)
            .first()
        )

        if not element:
            return None

        return element.update(db=self.db, data=element_data)

    def delete_element(self, fides_key: str) -> None:
        model_class = self.get_model()
        element = (
            self.db.query(model_class)
            .filter(model_class.fides_key == fides_key)
            .first()
        )

        if element:
            self.db.delete(element)

    def get_model(self) -> Type[Union[DataCategory, DataUse, DataSubject]]:
        return self.models[self.taxonomy_type]

    def _build_query(
        self, model_class: Type, active_only: bool, parent_key: Optional[str]
    ) -> Query:
        query = self.db.query(model_class)
        if active_only:
            query = query.filter(model_class.active.is_(True))
        if parent_key and hasattr(model_class, "parent_key"):
            query = query.filter(model_class.parent_key == parent_key)
        return query
