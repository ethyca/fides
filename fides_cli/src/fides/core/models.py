"""This module contains all of the models for the Fides API."""
# pylint: skip-file
from typing import List, Optional

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
    def sort_list_objects(cls, v):
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
    def sort_list_objects(cls, v):
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
    def sort_list_objects(cls, v):
        v.sort(key=lambda x: x.name)
        return v


class Registry(BaseModel):
    id: Optional[int]
    organizationId: int
    fidesKey: str
    name: str
    description: str


class DataDeclaration(BaseModel):
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
    fidesKey: str
    userName: str
    firstName: str
    lastName: str
    role: str


class Organization(BaseModel):
    id: Optional[int]
    fidesKey: str
    name: str
    description: str
