"""
Contains all of the Fides resources modeled as Pydantic models.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import AnyUrl, BaseModel, Field, HttpUrl, root_validator, validator

from fideslang.validation import (
    FidesKey,
    check_valid_country_code,
    matching_parent_key,
    no_self_reference,
    sort_list_objects_by_name,
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

name_field = Field(description="Human-Readable name for this resource.")
description_field = Field(
    description="A detailed description of what this resource is."
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
    name: Optional[str] = name_field
    description: Optional[str] = description_field

    class Config:
        "Config for the FidesModel"
        extra = "ignore"
        orm_mode = True
        use_enum_values = True


class DataResponsibilityTitle(str, Enum):
    """
    The model defining the responsibility or role over
    the system that processes personal data.

    Used to identify whether the organization is a
    Controller, Processor, or Sub-Processor of the data
    """

    CONTROLLER = "Controller"
    PROCESSOR = "Processor"
    SUB_PROCESSOR = "Sub-Processor"


class IncludeExcludeEnum(str, Enum):
    """
    Determine whether or not defined rights are
    being included or excluded.
    """

    ALL = "ALL"
    EXCLUDE = "EXCLUDE"
    INCLUDE = "INCLUDE"
    NONE = "NONE"


class DataSubjectRightsEnum(str, Enum):
    """
    The model for data subject rights over
    personal data.

    Based upon chapter 3 of the GDPR
    """

    INFORMED = "Informed"
    ACCESS = "Access"
    RECTIFICATION = "Rectification"
    ERASURE = "Erasure"
    PORTABILITY = "Portability"
    RESTRICT_PROCESSING = "Restrict Processing"
    WITHDRAW_CONSENT = "Withdraw Consent"
    OBJECT = "Object"
    OBJECT_TO_AUTOMATED_PROCESSING = "Object to Automated Processing"


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


class SpecialCategoriesEnum(str, Enum):
    """
    The model for processing special categories
    of personal data.

    Based upon article 9 of the GDPR
    """

    CONSENT = "Consent"
    EMPLOYMENT = "Employment"
    VITAL_INTEREST = "Vital Interests"
    NON_PROFIT_BODIES = "Non-profit Bodies"
    PUBLIC_BY_DATA_SUBJECT = "Public by Data Subject"
    LEGAL_CLAIMS = "Legal Claims"
    PUBLIC_INTEREST = "Substantial Public Interest"
    MEDICAL = "Medical"
    PUBLIC_HEALTH_INTEREST = "Public Health Interest"


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


class DataSubjectRights(BaseModel):
    """
    The DataSubjectRights resource model.

    Includes a strategy and optionally a
    list of data subject rights to apply
    via the set strategy.
    """

    strategy: IncludeExcludeEnum = Field(
        description="Defines the strategy used when mapping data rights to a data subject.",
    )
    values: Optional[List[DataSubjectRightsEnum]] = Field(
        description="A list of valid data subject rights to be used when applying data rights to a data subject via a strategy.",
    )

    @root_validator()
    @classmethod
    def include_exclude_has_values(cls, values: Dict) -> Dict:
        """
        Validate the if include or exclude is chosen, that at least one
        value is present.
        """
        strategy, rights = values.get("strategy"), values.get("values")
        if strategy in ("INCLUDE", "EXCLUDE"):
            assert (
                rights is not None
            ), f"If {strategy} is chosen, rights must also be listed."
        return values


class DataSubject(FidesModel):
    """The DataSubject resource model."""

    rights: Optional[DataSubjectRights] = Field(description=DataSubjectRights.__doc__)
    automated_decisions_or_profiling: Optional[bool] = Field(
        description="A boolean value to annotate whether or not automated decisions/profiling exists for the data subject.",
    )


class DataUse(FidesModel):
    """The DataUse resource model."""

    parent_key: Optional[FidesKey]
    legal_basis: Optional[LegalBasisEnum] = Field(
        description="The legal basis category of which the data use falls under. This field is used as part of the creation of an exportable data map.",
    )
    special_category: Optional[SpecialCategoriesEnum] = Field(
        description="The special category for processing of which the data use falls under. This field is used as part of the creation of an exportable data map.",
    )
    recipients: Optional[List[str]] = Field(
        description="An array of recipients when sharing personal data outside of your organization.",
    )
    legitimate_interest: bool = Field(
        default=False,
        description="A boolean representation of if the legal basis used is `Legitimate Interest`. Validated at run time and looks for a `legitimate_interest_impact_assessment` to exist if true.",
    )
    legitimate_interest_impact_assessment: Optional[AnyUrl] = Field(
        description="A url pointing to the legitimate interest impact assessment. Required if the legal bases used is legitimate interest.",
    )

    _matching_parent_key: classmethod = matching_parent_key_validator
    _no_self_reference: classmethod = no_self_reference_validator

    @validator("legitimate_interest", always=True)
    @classmethod
    def set_legitimate_interest(cls, value: bool, values: Dict) -> bool:
        """Sets if a legitimate interest is used."""
        if values["legal_basis"] == "Legitimate Interests":
            value = True
        return value

    @validator("legitimate_interest_impact_assessment", always=True)
    @classmethod
    def ensure_impact_assessment(cls, value: AnyUrl, values: Dict) -> AnyUrl:
        """
        Validates an impact assessment is applied if a
        legitimate interest has been defined.
        """
        if values["legitimate_interest"]:
            assert (
                value is not None
            ), "Impact assessment cannot be null for a legitimate interest, please provide a valid url"
        return value


# Dataset
class DatasetField(BaseModel):
    """
    The DatasetField resource model.

    This resource is nested within a DatasetCollection.
    """

    name: str = name_field
    description: Optional[str] = description_field
    data_categories: Optional[List[FidesKey]] = Field(
        description="Arrays of Data Categories, identified by `fides_key`, that applies to this field.",
    )
    data_qualifier: FidesKey = Field(
        default="aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
        description="A Data Qualifier that applies to this field. Note that this field holds a single value, therefore, the property name is singular.",
    )
    retention: Optional[str] = Field(
        description="An optional string to describe the retention policy for a dataset. This field can also be applied more granularly at either the Collection or field level of a Dataset.",
    )
    fields: Optional[List[DatasetField]] = Field(
        description="An optional array of objects that describe hierarchical/nested fields (typically found in NoSQL databases).",
    )


class DatasetCollection(BaseModel):
    """
    The DatasetCollection resource model.

    This resource is nested witin a Dataset.
    """

    name: str = name_field
    description: Optional[str] = description_field
    data_categories: Optional[List[FidesKey]] = Field(
        description="Array of Data Category resources identified by `fides_key`, that apply to all fields in the collection.",
    )
    data_qualifier: FidesKey = Field(
        default="aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
        description="Array of Data Qualifier resources identified by `fides_key`, that apply to all fields in the collection.",
    )
    retention: Optional[str] = Field(
        description="An optional string to describe the retention policy for a Dataset collection. This field can also be applied more granularly at the field level of a Dataset.",
    )
    fields: List[DatasetField] = Field(
        description="An array of objects that describe the collection's fields.",
    )

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

    name: str = Field(
        default="",
        description="An individual name used as part of publishing contact information. Encrypted at rest on the server.",
    )
    address: str = Field(
        default="",
        description="An individual address used as part of publishing contact information. Encrypted at rest on the server.",
    )
    email: str = Field(
        default="",
        description="An individual email used as part of publishing contact information. Encrypted at rest on the server.",
    )
    phone: str = Field(
        default="",
        description="An individual phone number used as part of publishing contact information. Encrypted at rest on the server.",
    )


class DatasetMetadata(BaseModel):
    """
    The DatasetMetadata resource model.

    Object used to hold application specific metadata for a dataset
    """

    resource_id: Optional[str]


class Dataset(FidesModel):
    "The Dataset resource model."

    meta: Optional[Dict[str, str]] = Field(
        description="An optional object that provides additional information about the Dataset. You can structure the object however you like. It can be a simple set of `key: value` properties or a deeply nested hierarchy of objects. How you use the object is up to you: Fides ignores it."
    )
    data_categories: Optional[List[FidesKey]] = Field(
        description="Array of Data Category resources identified by `fides_key`, that apply to all collections in the Dataset.",
    )
    data_qualifier: FidesKey = Field(
        default="aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
        description="Array of Data Qualifier resources identified by `fides_key`, that apply to all collections in the Dataset.",
    )
    fidesctl_meta: Optional[DatasetMetadata] = Field(
        description=DatasetMetadata.__doc__,
    )
    joint_controller: Optional[ContactDetails] = Field(
        description=ContactDetails.__doc__,
    )
    retention: Optional[str] = Field(
        default="No retention or erasure policy",
        description="An optional string to describe the retention policy for a dataset. This field can also be applied more granularly at either the Collection or field level of a Dataset.",
    )
    third_country_transfers: Optional[List[str]] = Field(
        description="An optional array to identify any third countries where data is transited to. For consistency purposes, these fields are required to follow the Alpha-3 code set in [ISO 3166-1](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3).",
    )
    collections: List[DatasetCollection] = Field(
        description="An array of objects that describe the Dataset's collections.",
    )
    _sort_collections: classmethod = validator("collections", allow_reuse=True)(
        sort_list_objects_by_name
    )
    _check_valid_country_code: classmethod = country_code_validator


# Evaluation
class ViolationAttributes(BaseModel):
    "The model for attributes which led to an evaluation violation"

    data_categories: List[str] = Field(
        description="A list of data categories which led to an evaluation violation.",
    )
    data_subjects: List[str] = Field(
        description="A list of data subjects which led to an evaluation violation.",
    )
    data_uses: List[str] = Field(
        description="A list of data uses which led to an evaluation violation.",
    )
    data_qualifier: str = Field(
        description="The data qualifier which led to an evaluation violation.",
    )


class Violation(BaseModel):
    "The model for violations within an evaluation."

    violating_attributes: ViolationAttributes = Field(
        description=ViolationAttributes.__doc__
    )
    detail: str = Field(
        description="A human-readable string detailing the evaluation violation.",
    )


class StatusEnum(str, Enum):
    "The model for possible evaluation results."

    FAIL = "FAIL"
    PASS = "PASS"


class Evaluation(BaseModel):
    """
    The Evaluation resource model.

    This resource is created after an evaluation is executed.
    """

    fides_key: FidesKey = Field(
        description="A uuid generated for each unique evaluation.",
    )
    status: StatusEnum = Field(description=StatusEnum.__doc__)
    violations: List[Violation] = Field(
        default=[],
        description=Violation.__doc__,
    )
    message: str = Field(
        default="",
        description="A human-readable string response for the evaluation.",
    )

    class Config:
        "Config for the Evaluation"
        extra = "ignore"
        orm_mode = True


# Organization
class ResourceFilter(BaseModel):
    """
    The ResourceFilter resource model.
    """

    type: str = Field(
        description="The type of filter to be used (i.e. ignore_resource_arn)",
    )
    value: str = Field(
        description="A string representation of resources to be filtered. Can include wildcards.",
    )


class OrganizationMetadata(BaseModel):
    """
    The OrganizationMetadata resource model.

    Object used to hold application specific metadata for an organization
    """

    resource_filters: Optional[List[ResourceFilter]] = Field(
        description="A list of filters that can be used when generating or scanning systems."
    )


class Organization(FidesModel):
    """
    The Organization resource model.

    This resource is used as a way to organize all other resources.
    """

    # It inherits this from FidesModel but Organizations don't have this field
    organization_parent_key: None = Field(
        default=None,
        description="An inherited field from the FidesModel that is unused with an Organization.",
    )
    controller: Optional[ContactDetails] = Field(
        description=ContactDetails.__doc__,
    )
    data_protection_officer: Optional[ContactDetails] = Field(
        description=ContactDetails.__doc__,
    )
    fidesctl_meta: Optional[OrganizationMetadata] = Field(
        description=OrganizationMetadata.__doc__,
    )
    representative: Optional[ContactDetails] = Field(
        description=ContactDetails.__doc__,
    )
    security_policy: Optional[HttpUrl] = Field(
        description="Am optional URL to the organization security policy."
    )


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

    matches: MatchesEnum = Field(
        description=MatchesEnum.__doc__,
    )
    values: List[FidesKey] = Field(
        description="A list of fides keys to be used with the matching type in a privacy rule.",
    )


class PolicyRule(BaseModel):
    """
    The PolicyRule resource model.

    Describes the allowed combination of the various privacy data types.
    """

    name: str
    data_categories: PrivacyRule = Field(
        description=PrivacyRule.__doc__,
    )
    data_uses: PrivacyRule = Field(
        description=PrivacyRule.__doc__,
    )
    data_subjects: PrivacyRule = Field(
        description=PrivacyRule.__doc__,
    )
    data_qualifier: FidesKey = Field(
        default="aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
        description="The fides key of the data qualifier to be used in a privacy rule.",
    )


class Policy(FidesModel):
    """
    The Policy resource model.

    An object used to organize a list of PolicyRules.
    """

    rules: List[PolicyRule] = Field(
        description=PolicyRule.__doc__,
    )

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
class DataProtectionImpactAssessment(BaseModel):
    """
    The DataProtectionImpactAssessment (DPIA) resource model.

    Contains information in regard to the data protection
    impact assessment exported on a data map or Record of
    Processing Activities (RoPA).

    A legal requirement under GDPR for any project that
    introduces a high risk to personal information.
    """

    is_required: bool = Field(
        default=False,
        description="A boolean value determining if a data protection impact assessment is required. Defaults to False.",
    )
    progress: Optional[str] = Field(
        description="The optional status of a Data Protection Impact Assessment. Returned on an exported data map or RoPA.",
    )
    link: Optional[AnyUrl] = Field(
        description="The optional link to the Data Protection Impact Assessment. Returned on an exported data map or RoPA.",
    )


class PrivacyDeclaration(BaseModel):
    """
    The PrivacyDeclaration resource model.

    States a function of a system, and describes how it relates
    to the privacy data types.
    """

    name: str = Field(
        description="The name of the privacy declaration on the system.",
    )
    data_categories: List[FidesKey] = Field(
        description="An array of data categories describing a system in a privacy declaration.",
    )
    data_use: FidesKey = Field(
        description="The Data Use describing a system in a privacy declaration.",
    )
    data_qualifier: FidesKey = Field(
        default="aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
        description="The fides key of the data qualifier describing a system in a privacy declaration.",
    )
    data_subjects: List[FidesKey] = Field(
        description="An array of data subjects describing a system in a privacy declaration.",
    )
    dataset_references: Optional[List[FidesKey]] = Field(
        description="Referenced Dataset fides keys used by the system.",
    )


class SystemMetadata(BaseModel):
    """
    The SystemMetadata resource model.

    Object used to hold application specific metadata for a system
    """

    resource_id: Optional[str] = Field(
        description="The external resource id for the system being modeled."
    )
    endpoint_address: Optional[str] = Field(
        description="The host of the external resource for the system being modeled."
    )
    endpoint_port: Optional[str] = Field(
        description="The port of the external resource for the system being modeled."
    )


class System(FidesModel):
    """
    The System resource model.

    Describes an application and includes a list of PrivacyDeclaration resources.
    """

    registry_id: Optional[int] = Field(
        description="The id of the system registry, if used.",
    )
    meta: Optional[Dict[str, str]] = Field(
        description="An optional property to store any extra information for a system. Not used by fidesctl.",
    )
    fidesctl_meta: Optional[SystemMetadata] = Field(
        description=SystemMetadata.__doc__,
    )
    system_type: str = Field(
        description="A required value to describe the type of system being modeled, examples include: Service, Application, Third Party, etc.",
    )
    data_responsibility_title: DataResponsibilityTitle = Field(
        default=DataResponsibilityTitle.CONTROLLER,
        description=DataResponsibilityTitle.__doc__,
    )
    privacy_declarations: List[PrivacyDeclaration] = Field(
        description=PrivacyDeclaration.__doc__,
    )
    system_dependencies: Optional[List[FidesKey]] = Field(
        description="A list of fides keys to model dependencies."
    )
    joint_controller: Optional[ContactDetails] = Field(
        description=ContactDetails.__doc__,
    )
    third_country_transfers: Optional[List[str]] = Field(
        description="An optional array to identify any third countries where data is transited to. For consistency purposes, these fields are required to follow the Alpha-3 code set in ISO 3166-1.",
    )
    administrating_department: Optional[str] = Field(
        default="Not defined",
        description="An optional value to identify the owning department or group of the system within your organization",
    )
    data_protection_impact_assessment: DataProtectionImpactAssessment = Field(
        default=DataProtectionImpactAssessment(),
        description=DataProtectionImpactAssessment.__doc__,
    )

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
