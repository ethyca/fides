from typing import Any, List, Optional, Sequence, Type

from fideslang.models import Dataset, DatasetCollection, DatasetField
from fideslang.validation import FidesKey
from loguru import logger
from pydantic import BaseModel, ConfigDict, field_validator

from fides.api import common_exceptions
from fides.api.schemas.api import BulkResponse, BulkUpdateFailed
from fides.api.schemas.base_class import FidesSchema
from fides.api.util.data_category import DataCategory as DefaultTaxonomyDataCategories


def validate_data_categories_against_db(
    dataset: Dataset, defined_data_categories: List[FidesKey]
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
        fields: Sequence[FieldDataCategoryValidation] = []  # type: ignore[assignment]

    class DatasetDataCategoryValidation(Dataset, DataCategoryValidationMixin):
        collections: Sequence[CollectionDataCategoryValidation]  # type: ignore[assignment]

    DatasetDataCategoryValidation(**dataset.model_dump(mode="json"))


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
            raise common_exceptions.DataCategoryNotSupported(
                f"The data category {data_category} is not supported."
            )
        return data_category

    if proposed_data_categories:
        return [dc for dc in proposed_data_categories if validate_category(dc)]
    return proposed_data_categories


class DatasetTraversalDetails(FidesSchema):
    """
    Describes whether or not the parent dataset is traversable; if not, includes
    an error message describing the traversal issues.
    """

    is_traversable: bool
    msg: Optional[str]


class ValidateDatasetResponse(FidesSchema):
    """
    Response model for validating a dataset, which includes both the dataset
    itself (if valid) plus a details object describing if the dataset is
    traversable or not.
    """

    dataset: Dataset
    traversal_details: DatasetTraversalDetails


class DatasetConfigCtlDataset(FidesSchema):
    fides_key: FidesKey  # The fides_key for the DatasetConfig
    ctl_dataset_fides_key: FidesKey  # The fides_key for the ctl_datasets record


class DatasetConfigSchema(FidesSchema):
    """Returns the DatasetConfig fides key and the linked Ctl Dataset"""

    fides_key: FidesKey
    ctl_dataset: Dataset
    model_config = ConfigDict(from_attributes=True)


class BulkPutDataset(BulkResponse):
    """Schema with mixed success/failure responses for Bulk Create/Update of Datasets."""

    succeeded: List[Dataset]
    failed: List[BulkUpdateFailed]


class CollectionAddressResponse(FidesSchema):
    """Schema for the representation of a collection in the graph"""

    dataset: Optional[str]
    collection: Optional[str]


class DryRunDatasetResponse(FidesSchema):
    """
    Response model for dataset dry run
    """

    collectionAddress: CollectionAddressResponse
    query: Any
