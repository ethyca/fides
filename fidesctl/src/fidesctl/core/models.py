"""This module contains all of the models for the Fides API."""
# pylint: skip-file
from typing import Dict, List, Optional, Type, Union

from pydantic import BaseModel, validator


class DataCategory(BaseModel):
    id: Optional[int]
    organizationId: int
    fidesKey: str
    name: str
    clause: str
    description: str


class DataQualifier(BaseModel):
    id: Optional[int]
    organizationId: int
    fidesKey: str
    name: str
    clause: str
    description: str


class DatasetField(BaseModel):
    name: str
    description: str
    dataCategories: Optional[List[str]]
    dataQualifier: Optional[str]


class DatasetTable(BaseModel):
    name: str
    description: str
    fields: List[DatasetField]

    @validator("fields")
    def sort_list_objects(cls, v: List) -> List:
        v.sort(key=lambda x: x.name)
        return v


class Dataset(BaseModel):
    id: Optional[int]
    organizationId: int
    fidesKey: str
    name: str
    description: str
    location: str
    datasetType: str
    tables: List[DatasetTable]

    @validator("tables")
    def sort_list_objects(cls, v: List) -> List:
        v.sort(key=lambda x: x.name)
        return v


class DataSubjectCategory(BaseModel):
    id: Optional[int]
    organizationId: int
    fidesKey: str
    name: str
    description: str


class DataUse(BaseModel):
    id: Optional[int]
    organizationId: int
    fidesKey: str
    name: str
    clause: str
    description: str


class DataRule(BaseModel):
    inclusion: str
    values: List[str]


class PolicyRule(BaseModel):
    organizationId: int
    policyId: int
    fidesKey: str
    name: str
    description: str
    dataCategories: DataRule
    dataUses: DataRule
    dataSubjectCategories: DataRule
    dataQualifier: str
    action: str


class Policy(BaseModel):
    id: Optional[int]
    organizationId: int
    fidesKey: str
    name: str
    description: str
    rules: List[PolicyRule]

    @validator("rules")
    def sort_list_objects(cls, v: List) -> List:
        v.sort(key=lambda x: x.name)
        return v


class Registry(BaseModel):
    id: Optional[int]
    organizationId: int
    fidesKey: str
    name: str
    description: str


class DataDeclaration(BaseModel):
    name: str
    dataCategories: List[str]
    dataUse: str
    dataQualifier: str
    dataSubjectCategories: List[str]


class System(BaseModel):
    id: Optional[int]
    organizationId: int
    registryId: int
    fidesKey: str
    fidesSystemType: str
    name: str
    description: str
    declarations: Optional[List[DataDeclaration]]
    systemDependencies: List[str]
    datasets: List[str]


class User(BaseModel):
    id: Optional[int]
    organizationId: int
    userName: str
    firstName: str
    lastName: str
    role: str
    apiKey: str


class Organization(BaseModel):
    id: Optional[int]
    fidesKey: str
    name: str
    description: str


# A mapping of object names to their Endpoints
FidesTypes = Union[
    Type[DataCategory],
    Type[DataQualifier],
    Type[Dataset],
    Type[DataSubjectCategory],
    Type[DataUse],
    Type[Organization],
    Type[Policy],
    Type[Registry],
    Type[System],
    Type[User],
]
MODEL_DICT: Dict[str, FidesTypes] = {
    "data-category": DataCategory,
    "data-qualifier": DataQualifier,
    "dataset": Dataset,
    "data-subject": DataSubjectCategory,
    "data-use": DataUse,
    "organization": Organization,
    "policy": Policy,
    "registry": Registry,
    "system": System,
}
MODEL_LIST = list(MODEL_DICT.keys())

FidesModel = Union[
    DataCategory,
    DataQualifier,
    Dataset,
    DataSubjectCategory,
    DataUse,
    Organization,
    Policy,
    Registry,
    System,
    User,
]
