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
    path: str
    dataCategories: Optional[List[str]]
    dataQualifier: Optional[str]


class Dataset(BaseModel):
    id: Optional[int]
    organizationId: int
    fidesKey: str
    metadata: Optional[Dict[str, str]]
    name: str
    description: str
    dataCategories: Optional[List[str]]
    dataQualifier: Optional[str]
    location: str
    datasetType: str
    fields: List[DatasetField]

    @validator("fields")
    def sort_list_objects(cls, v: List) -> List:
        v.sort(key=lambda x: x.name)
        return v


class DataSubject(BaseModel):
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


class PrivacyRule(BaseModel):
    inclusion: str
    values: List[str]


class PolicyRule(BaseModel):
    organizationId: int
    fidesKey: str
    name: str
    description: str
    dataCategories: PrivacyRule
    dataUses: PrivacyRule
    dataSubjects: PrivacyRule
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


class PrivacyDeclaration(BaseModel):
    name: str
    dataCategories: List[str]
    dataUse: str
    dataQualifier: str
    dataSubjects: List[str]
    datasetReferences: Optional[List[str]]


class System(BaseModel):
    id: Optional[int]
    organizationId: int
    registryId: Optional[int]
    fidesKey: str
    metadata: Optional[Dict[str, str]]
    systemType: str
    name: str
    description: str
    privacyDeclarations: Optional[List[PrivacyDeclaration]]
    systemDependencies: Optional[List[str]]


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
    Type[DataSubject],
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
    "data-subject": DataSubject,
    "data-use": DataUse,
    "organization": Organization,
    "policy": Policy,
    "registry": Registry,
    "system": System,
    "user": User,
}
MODEL_LIST = list(MODEL_DICT.keys())

FidesModel = Union[
    DataCategory,
    DataQualifier,
    Dataset,
    DataSubject,
    DataUse,
    Organization,
    Policy,
    Registry,
    System,
    User,
]
