from typing import Dict, List, Optional

from pydantic import BaseModel, validator

from fideslang.models.fides_model import FidesModel


class DatasetField(BaseModel):
    name: str
    description: str
    path: str
    dataCategories: Optional[List[str]]
    dataQualifier: Optional[str]


class Dataset(FidesModel):
    organizationId: int
    metadata: Optional[Dict[str, str]]
    name: str
    description: str
    dataCategories: Optional[List[str]]
    dataQualifier: Optional[str]
    location: str
    datasetType: str
    fields: List[DatasetField]

    @validator("fields")
    def sort_list_objects(cls, values: List) -> List:
        values.sort(key=lambda value: value.name)
        return values
