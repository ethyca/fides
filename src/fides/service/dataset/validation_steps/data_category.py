from typing import List, Optional, Type

from fideslang.models import Dataset as FideslangDataset
from fideslang.models import DatasetCollection, DatasetField
from fideslang.validation import FidesKey
from loguru import logger
from pydantic import BaseModel, field_validator

from fides.api.common_exceptions import DataCategoryNotSupported
from fides.api.util.data_category import DataCategory as DefaultTaxonomyDataCategories
from fides.api.util.data_category import get_data_categories_from_db
from fides.service.dataset.dataset_validator import (
    DatasetValidationContext,
    DatasetValidationStep,
)


def _valid_data_categories(
    proposed_data_categories: Optional[List[FidesKey]],
    defined_data_categories: List[FidesKey],
) -> Optional[List[FidesKey]]:
    """
    Ensure that every data category provided matches a valid defined data category.
    Throws an error if any of the categories are invalid,
    or otherwise returns the list of categories unchanged.
    """

    def validate_category(data_category: FidesKey) -> FidesKey:
        if data_category not in defined_data_categories:
            raise DataCategoryNotSupported(
                f"The data category {data_category} is not supported."
            )
        return data_category

    categories = proposed_data_categories or []
    for category in categories:
        validate_category(category)

    return categories


def validate_data_categories_against_db(
    dataset: FideslangDataset, defined_data_categories: List[FidesKey]
) -> None:
    """
    Validate that data_categories defined on the Dataset, Collection, and Field levels exist
    in the database.  Doing this instead of a traditional validator function to have
    access to a database session.

    If no data categories in the database, default to using data categories from the default taxonomy.
    """
    if not defined_data_categories:
        logger.info(
            "No data categories in the database: reverting to default data categories."
        )
        defined_data_categories = [
            FidesKey(key) for key in DefaultTaxonomyDataCategories.__members__.keys()
        ]

    class DataCategoryValidationMixin(BaseModel):
        @field_validator("data_categories", check_fields=False)
        @classmethod
        def valid_data_categories(
            cls: Type["DataCategoryValidationMixin"], v: Optional[List[FidesKey]]
        ) -> Optional[List[FidesKey]]:
            """Validate that all annotated data categories exist in the taxonomy"""
            return _valid_data_categories(v, defined_data_categories)

    class FieldDataCategoryValidation(DatasetField, DataCategoryValidationMixin):
        fields: Optional[List["FieldDataCategoryValidation"]] = None  # type: ignore[assignment]

    FieldDataCategoryValidation.model_rebuild()

    class CollectionDataCategoryValidation(
        DatasetCollection, DataCategoryValidationMixin
    ):
        fields: List[FieldDataCategoryValidation] = []  # type: ignore[assignment]

    class DatasetDataCategoryValidation(FideslangDataset, DataCategoryValidationMixin):
        collections: List[CollectionDataCategoryValidation]  # type: ignore[assignment]

    DatasetDataCategoryValidation(**dataset.model_dump(mode="json"))


class DataCategoryValidationStep(DatasetValidationStep):
    """Validates data categories against database"""

    def validate(self, context: DatasetValidationContext) -> None:
        defined_data_categories = get_data_categories_from_db(context.db)
        validate_data_categories_against_db(context.dataset, defined_data_categories)
