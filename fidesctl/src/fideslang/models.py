"""
Contains all of the Fides resources modeled as Pydantic models.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import validator, BaseModel, Field, HttpUrl

from fideslang.validation import (
    FidesKey,
    sort_list_objects_by_name,
    no_self_reference,
    matching_parent_key,
    check_valid_country_code,
)

# Reusable components
country_code_validator = validator("third_country_transfers", allow_reuse=True)(
    check_valid_country_code
)

matching_parent_key_validator = validator("parent_key", allow_reuse=True, always=True)(
    matching_parent_key
)
no_self_reference_validator = validator("parent_key", allow_reuse=True)(
    no_self_reference
)


# Fides Base Model
class FidesModel(BaseModel):
    """The base model for all Fides Resources."""

    fides_key: FidesKey = Field(
        description="A unique key used to identify this resource."
    )
    organization_fides_key: FidesKey = Field(
        default="default_organization",
        description="Defines the Organization that this resource belongs to.",
    )
    name: Optional[str] = Field(
        description="Human-Readable string name for this resource."
    )
    description: Optional[str] = Field(
        description="In-depth description of what this resource is."
    )

    class Config:
        "Config for the FidesModel"
        extra = "ignore"
        orm_mode = True


class LegalBasisEnum(str, Enum):
    """
    The model for allowable legal basis categories

    Based upon article 6 of the GDPR
    """

    CONSENT = "Consent"
    CONTRACT = "Contract"
    LEGAL_OBLIGATION = "Legal Obligation"
    VITAL_INTEREST = "Vital Interest"
    PUBLIC_INTEREST = "Public Interest"
    LEGITIMATE_INTEREST = "Legitimate Interests"


# Privacy Data Types
class DataCategory(FidesModel):
    """The DataCategory resource model."""

    parent_key: Optional[FidesKey]

    _matching_parent_key: classmethod = matching_parent_key_validator
    _no_self_reference: classmethod = no_self_reference_validator


class DataQualifier(FidesModel):
    """The DataQualifier resource model."""

    parent_key: Optional[FidesKey]

    _matching_parent_key: classmethod = matching_parent_key_validator
    _no_self_reference: classmethod = no_self_reference_validator


class DataSubject(FidesModel):
    """The DataSubject resource model."""


class DataUse(FidesModel):
    """The DataUse resource model."""

    parent_key: Optional[FidesKey]
    legal_basis: Optional[LegalBasisEnum]
    recipients: Optional[List[str]]

    _matching_parent_key: classmethod = matching_parent_key_validator
    _no_self_reference: classmethod = no_self_reference_validator


# Dataset
class DatasetField(BaseModel):
    """
    The DatasetField resource model.

    This resource is nested within a DatasetCollection.
    """

    name: str
    description: Optional[str]
    data_categories: Optional[List[FidesKey]]
    data_qualifier: FidesKey = Field(
        default="aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
    )
    retention: Optional[str]
    fields: Optional[List[DatasetField]]


class DatasetCollection(BaseModel):
    """
    The DatasetCollection resource model.

    This resource is nested witin a Dataset.
    """

    name: str
    description: Optional[str]
    data_categories: Optional[List[FidesKey]]
    data_qualifier: FidesKey = Field(
        default="aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
    )
    retention: Optional[str]
    fields: List[DatasetField]

    _sort_fields: classmethod = validator("fields", allow_reuse=True)(
        sort_list_objects_by_name
    )


class ContactDetails(BaseModel):
    """
    The contact details information model.

    Used to capture contact information for controllers, used
    as part of exporting a data map / ROPA.

    This model is nested under an Organization and
    potentially under a system/dataset.
    """

    name: str = ""
    address: str = ""
    email: str = ""
    phone: str = ""


class Dataset(FidesModel):
    "The Dataset resource model."

    meta: Optional[Dict[str, str]]
    data_categories: Optional[List[FidesKey]]
    data_qualifier: FidesKey = Field(
        default="aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
    )
    joint_controller: Optional[ContactDetails]
    retention: Optional[str] = "No retention or erasure policy"
    third_country_transfers: Optional[List[str]]
    collections: List[DatasetCollection]
    _sort_collections: classmethod = validator("collections", allow_reuse=True)(
        sort_list_objects_by_name
    )
    _check_valid_country_code: classmethod = country_code_validator


# Evaluation
class ViolationAttributes(BaseModel):
    "The model for attributes which led to an evaluation violation"

    data_categories: List[str]
    data_subjects: List[str]
    data_uses: List[str]
    data_qualifier: str


class Violation(BaseModel):
    "The model for violations within an evaluation"

    violating_attributes: ViolationAttributes
    detail: str


class StatusEnum(str, Enum):
    "The model for possible evaluation results."

    FAIL = "FAIL"
    PASS = "PASS"


class Evaluation(BaseModel):
    """
    The Evaluation resource model.

    This resource is created after an evaluation is executed.
    """

    fides_key: FidesKey
    status: StatusEnum
    violations: List[Violation] = []
    message: str = ""

    class Config:
        "Config for the Evaluation"
        extra = "ignore"
        orm_mode = True


# Organization
class ResourceFilter(BaseModel):
    """
    The ResourceFilter resource model.
    """

    type: str
    value: str


class OrganizationMetadata(BaseModel):
    """
    The OrganizationMetadata resource model.

    Object used to hold application specific metadata for an organization
    """

    resource_filters: Optional[List[ResourceFilter]]


class Organization(FidesModel):
    """
    The Organization resource model.

    This resource is used as a way to organize all other resources.
    """

    # It inherits this from FidesModel but Organizations don't have this field
    organization_parent_key: None = None
    controller: Optional[ContactDetails]
    data_protection_officer: Optional[ContactDetails]
    fidesctl_meta: Optional[OrganizationMetadata]
    representative: Optional[ContactDetails]
    security_policy: Optional[HttpUrl]


# Policy
class MatchesEnum(str, Enum):
    """
    The MatchesEnum resource model.

    Determines how the listed resources are matched in the evaluation logic.
    """

    ANY = "ANY"
    ALL = "ALL"
    NONE = "NONE"
    OTHER = "OTHER"


class PrivacyRule(BaseModel):
    """
    The PrivacyRule resource model.

    A list of privacy data types and what match method to use.
    """

    matches: MatchesEnum
    values: List[FidesKey]


class PolicyRule(BaseModel):
    """
    The PolicyRule resource model.

    Describes the allowed combination of the various privacy data types.
    """

    name: str
    data_categories: PrivacyRule
    data_uses: PrivacyRule
    data_subjects: PrivacyRule
    data_qualifier: FidesKey = Field(
        default="aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified"
    )


class Policy(FidesModel):
    """
    The Policy resource model.

    An object used to organize a list of PolicyRules.
    """

    rules: List[PolicyRule]

    _sort_rules: classmethod = validator("rules", allow_reuse=True)(
        sort_list_objects_by_name
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
    data_qualifier: FidesKey = Field(
        default="aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
    )
    data_subjects: List[FidesKey]
    dataset_references: Optional[List[FidesKey]]


class SystemMetadata(BaseModel):
    """
    The SystemMetadata resource model.

    Object used to hold application specific metadata for a system
    """

    resource_id: Optional[str]
    endpoint_address: Optional[str]
    endpoint_port: Optional[str]


class System(FidesModel):
    """
    The System resource model.

    Describes an application and includes a list of PrivacyDeclaration resources.
    """

    registry_id: Optional[int]
    meta: Optional[Dict[str, str]]
    fidesctl_meta: Optional[SystemMetadata]
    system_type: str
    privacy_declarations: List[PrivacyDeclaration]
    system_dependencies: Optional[List[FidesKey]]
    joint_controller: Optional[ContactDetails]
    third_country_transfers: Optional[List[str]]
    administrating_department: Optional[str] = "Not defined"

    _sort_privacy_declarations: classmethod = validator(
        "privacy_declarations", allow_reuse=True
    )(sort_list_objects_by_name)

    _no_self_reference: classmethod = validator(
        "system_dependencies", allow_reuse=True, each_item=True
    )(no_self_reference)

    _check_valid_country_code: classmethod = country_code_validator


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
