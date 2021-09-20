from enum import Enum
from typing import Dict, List, Optional

from pydantic import validator, BaseModel, Field

from fideslang.validation import (
    fides_key,
    sort_list_objects_by_key,
    sort_list_objects_by_name,
    no_self_reference,
)


# Fides Base Model
class FidesModel(BaseModel):
    """The base model for all Fides Resources."""

    id: Optional[int]
    organization_fides_key: int = 1
    name: Optional[str]
    description: Optional[str]
    fides_key: fides_key

    class Config:
        extra = "ignore"
        orm_mode = True


# Privacy Data Types
class DataCategory(FidesModel):
    """The DataCategory resource model."""

    parent_key: Optional[fides_key]

    _no_self_reference = validator("parent_key", allow_reuse=True)(no_self_reference)


class DataQualifier(FidesModel):
    """The DataQualifier resource model."""

    pass


class DataSubject(FidesModel):
    pass


class DataUse(FidesModel):
    parent_key: Optional[fides_key]

    _no_self_reference = validator("parent_key", allow_reuse=True)(no_self_reference)


# Dataset
class DatasetField(BaseModel):
    name: str
    description: str
    path: str
    data_categories: Optional[List[fides_key]]
    data_qualifier: Optional[fides_key]


class Dataset(FidesModel):
    metadata: Optional[Dict[str, str]]
    data_categories: Optional[List[fides_key]]
    data_qualifier: Optional[fides_key]
    location: str
    dataset_type: str
    fields: List[DatasetField]

    _sort_fields = validator("fields", allow_reuse=True)(sort_list_objects_by_name)


# Evaluation
class EvaluationError(Exception):
    """Custom exception for when an Evaluation fails."""

    def __init__(self) -> None:
        super().__init__("Evaluation failed!")


class StatusEnum(str, Enum):
    FAIL = "FAIL"
    PASS = "PASS"


class Evaluation(BaseModel):

    status: StatusEnum = StatusEnum.PASS
    details: List[str]
    message: str = ""


# Organization
class Organization(FidesModel):
    # It inherits this from FidesModel but Organization's don't have this field
    organiztion_parent_key: None = None


# Policy
class InclusionEnum(str, Enum):
    ANY = "ANY"
    ALL = "ALL"
    NONE = "NONE"


class ActionEnum(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    REQUIRE = "REQUIRE"


class PrivacyRule(BaseModel):
    inclusion: InclusionEnum
    values: List[fides_key]


class PolicyRule(FidesModel):
    data_categories: PrivacyRule
    data_uses: PrivacyRule
    data_subjects: PrivacyRule
    data_qualifier: fides_key
    action: ActionEnum


class Policy(FidesModel):
    rules: List[PolicyRule]

    _sort_rules = validator("rules", allow_reuse=True)(sort_list_objects_by_key)


# Registry
class Registry(FidesModel):
    pass


# System
class PrivacyDeclaration(BaseModel):
    name: str
    data_categories: List[fides_key]
    data_use: fides_key
    data_qualifier: fides_key
    data_subjects: List[fides_key]
    dataset_references: Optional[List[str]]


class System(FidesModel):
    registry_id: Optional[int]
    metadata: Optional[Dict[str, str]]
    system_type: str
    privacy_declarations: List[PrivacyDeclaration]
    system_dependencies: Optional[List[fides_key]]

    _sort_privacy_declarations = validator("privacy_declarations", allow_reuse=True)(
        sort_list_objects_by_name
    )

    _no_self_reference = validator(
        "system_dependencies", allow_reuse=True, each_item=True
    )(no_self_reference)


# Taxonomy
class Taxonomy(BaseModel):
    """
    Represents an entire taxonomy of Fides Resources.

    The choice to not use pluralized forms of each resource name
    was deliberate, as this would have caused huge amounts of complexity
    elsewhere across the codebase.
    """

    data_category: List[DataCategory] = Field(default_factory=list)
    data_subject: Optional[List[DataSubject]] = Field(default_factory=list)
    data_use: Optional[List[DataUse]] = Field(default_factory=list)
    data_qualifier: Optional[List[DataQualifier]] = Field(default_factory=list)

    dataset: Optional[List[Dataset]] = Field(default_factory=list)
    system: Optional[List[System]] = Field(default_factory=list)
    policy: Optional[List[Policy]] = Field(default_factory=list)

    registry: Optional[List[Registry]] = Field(default_factory=list)
    organization: List[Organization] = Field(default_factory=list)
