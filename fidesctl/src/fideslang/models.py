"""
Contains all of the Fides resources modeled as Pydantic models.
"""
from enum import Enum
from typing import Dict, List, Optional

from pydantic import validator, BaseModel, Field

from fideslang.validation import (
    FidesKey,
    sort_list_objects_by_key,
    sort_list_objects_by_name,
    no_self_reference,
    matching_parent_key,
)


# Fides Base Model
class FidesModel(BaseModel):
    """The base model for all Fides Resources."""

    fides_key: FidesKey
    organization_fides_key: int = 1
    name: Optional[str]
    description: Optional[str]

    class Config:
        "Config for the FidesModel"
        extra = "ignore"
        orm_mode = True


# Privacy Data Types
class DataCategory(FidesModel):
    """The DataCategory resource model."""

    parent_key: Optional[FidesKey]

    _matching_parent_key: classmethod = validator(
        "parent_key", allow_reuse=True, always=True
    )(matching_parent_key)

    _no_self_reference: classmethod = validator("parent_key", allow_reuse=True)(
        no_self_reference
    )


class DataQualifier(FidesModel):
    """The DataQualifier resource model."""


class DataSubject(FidesModel):
    """The DataSubject resource model."""


class DataUse(FidesModel):
    """The DataUse resource model."""

    parent_key: Optional[FidesKey]

    _matching_parent_key: classmethod = validator(
        "parent_key", allow_reuse=True, always=True
    )(matching_parent_key)

    _no_self_reference: classmethod = validator("parent_key", allow_reuse=True)(
        no_self_reference
    )


# Dataset
class DatasetField(BaseModel):
    "The DatasetField resource model. This resource is nested within a Dataset."

    name: str
    description: str
    path: str
    data_categories: Optional[List[FidesKey]]
    data_qualifier: Optional[FidesKey]


class Dataset(FidesModel):
    "The Dataset resource model."

    meta: Optional[Dict[str, str]]
    data_categories: Optional[List[FidesKey]]
    data_qualifier: Optional[FidesKey]
    location: str
    dataset_type: str
    fields: List[DatasetField]

    _sort_fields: classmethod = validator("fields", allow_reuse=True)(
        sort_list_objects_by_name
    )


# Evaluation
class EvaluationError(Exception):
    """Custom exception for when an Evaluation fails."""

    def __init__(self) -> None:
        super().__init__("Evaluation failed!")


class StatusEnum(str, Enum):
    "The model for possible evaluation results."

    FAIL = "FAIL"
    PASS = "PASS"


class Evaluation(BaseModel):
    """
    The Evaluation resource model.

    This resource is created after an evaluation is executed.
    """

    status: StatusEnum
    details: List[str]
    message: str = ""


# Organization
class Organization(FidesModel):
    """
    The Organization resource model.

    This resource is used as a way to organize all other resources.
    """

    # It inherits this from FidesModel but Organization's don't have this field
    organiztion_parent_key: None = None


# Policy
class InclusionEnum(str, Enum):
    """
    The InclusionEnum resouce model.

    Determines how the listed resources are included in the evaluation logic.
    """

    ANY = "ANY"
    ALL = "ALL"
    NONE = "NONE"


class ActionEnum(str, Enum):
    """
    The ActionEnum resource model.

    Describes what the result of the PolicyRule should be if it is fulfilled.
    """

    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    REQUIRE = "REQUIRE"


class PrivacyRule(BaseModel):
    """
    The PrivacyRule resource model.

    A list of privacy data types and what inclusion method to use.
    """

    inclusion: InclusionEnum
    values: List[FidesKey]


class PolicyRule(FidesModel):
    """
    The PolicyRule resource model.

    Describes combination of the various types of privacy data types
    and what action that combination constitutes.
    """

    data_categories: PrivacyRule
    data_uses: PrivacyRule
    data_subjects: PrivacyRule
    data_qualifier: FidesKey
    action: ActionEnum


class Policy(FidesModel):
    """
    The Policy resource model.

    An object used to organize a list of PolicyRules.
    """

    rules: List[PolicyRule]

    _sort_rules: classmethod = validator("rules", allow_reuse=True)(
        sort_list_objects_by_key
    )


# Registry
class Registry(FidesModel):
    """
    The Registry resource model.

    Systems can be assigned to this resource, but it doesn't inherently
    point to any other resources.
    """


# System
class PrivacyDeclaration(BaseModel):
    """
    The PrivacyDeclaration resource model.

    States a function of a system, and describes how it relates
    to the privacy data types.
    """

    name: str
    data_categories: List[FidesKey]
    data_use: FidesKey
    data_qualifier: FidesKey
    data_subjects: List[FidesKey]
    dataset_references: Optional[List[str]]


class System(FidesModel):
    """
    The System resource model.

    Describes an application and includes a list of PrivacyDeclaration resources.
    """

    registry_id: Optional[int]
    meta: Optional[Dict[str, str]]
    system_type: str
    privacy_declarations: List[PrivacyDeclaration]
    system_dependencies: Optional[List[FidesKey]]

    _sort_privacy_declarations: classmethod = validator(
        "privacy_declarations", allow_reuse=True
    )(sort_list_objects_by_name)

    _no_self_reference: classmethod = validator(
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
