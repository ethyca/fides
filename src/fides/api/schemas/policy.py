from enum import Enum as EnumType
from enum import StrEnum
from typing import Any, Optional

from fideslang.validation import FidesKey
from pydantic import ConfigDict, model_validator

from fides.api.schemas.api import BulkResponse, BulkUpdateFailed
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.storage.storage import StorageDestinationResponse


class ActionType(StrEnum):
    """The purpose of a particular privacy request"""

    access = "access"
    consent = "consent"
    erasure = "erasure"
    update = "update"


class CurrentStep(EnumType):
    pre_webhooks = "pre_webhooks"
    access = "access"
    upload_access = "upload_access"
    erasure = "erasure"
    finalize_erasure = "finalize_erasure"
    consent = "consent"
    finalize_consent = "finalize_consent"
    email_post_send = "email_post_send"
    post_webhooks = "post_webhooks"
    finalization = "finalization"


# action types we actively support in policies/requests
SUPPORTED_ACTION_TYPES = {ActionType.access, ActionType.consent, ActionType.erasure}


class DrpAction(EnumType):
    """
    Enum to hold valid DRP actions. For more details, see:
    https://github.com/consumer-reports-digital-lab/data-rights-protocol#301-supported-rights-actions
    """

    access = "access"
    deletion = "deletion"
    # below are not supported
    sale_opt_out = "sale:opt_out"
    sale_opt_in = "sale:opt_in"
    access_categories = "access:categories"
    access_specific = "access:specific"


class PolicyMaskingSpec(FidesSchema):
    """Models the masking strategy definition"""

    strategy: str
    configuration: dict[str, Any]


class PolicyMaskingSpecResponse(FidesSchema):
    """
    The schema to use when returning a masking strategy via the API. This schema omits other
    potentially sensitive fields in the masking configuration, for example the encryption
    algorithm.
    """

    strategy: str


class RuleTarget(FidesSchema):
    """An external representation of a Rule's target DataCategory within a Fidesops Policy"""

    name: Optional[str] = None
    key: Optional[FidesKey] = None
    # `data_category` is type str so that we can validate its contents against the DB records
    # outside of the schemas
    data_category: str
    model_config = ConfigDict(use_enum_values=True)


class RuleBase(FidesSchema):
    """An external representation of a Rule within a Fidesops Policy"""

    name: str
    key: Optional[FidesKey] = None
    action_type: ActionType
    model_config = ConfigDict(use_enum_values=True)


class RuleCreate(RuleBase):
    """
    The schema to use when creating a Rule. This schema accepts a storage_destination_key
    over a composite object.
    """

    storage_destination_key: Optional[FidesKey] = None
    masking_strategy: Optional[PolicyMaskingSpec] = None


class RuleResponse(RuleBase):
    """
    The schema to use when returning a Rule via the API. This schema uses a censored version
    of the `PolicyMaskingSpec` that omits the configuration to avoid exposing secrets.
    """

    storage_destination: Optional[StorageDestinationResponse] = None
    masking_strategy: Optional[PolicyMaskingSpecResponse] = None


class RuleResponseWithTargets(RuleBase):
    """
    The schema to use when returning a Rule via the API and when including the Rule's targets
    is desired. This schema uses a censored version of the `PolicyMaskingSpec` that omits the
    configuration to avoid exposing secrets.
    """

    targets: Optional[list[RuleTarget]] = None
    storage_destination: Optional[StorageDestinationResponse] = None
    masking_strategy: Optional[PolicyMaskingSpecResponse] = None


class Rule(RuleBase):
    """A representation of a Rule that features all storage destination data."""

    storage_destination: Optional[StorageDestinationResponse] = None
    masking_strategy: Optional[PolicyMaskingSpec] = None


class Policy(FidesSchema):
    """An external representation of a Fidesops Policy"""

    name: str
    key: Optional[FidesKey] = None
    drp_action: Optional[DrpAction] = None
    execution_timeframe: Optional[int] = None
    model_config = ConfigDict(use_enum_values=True, from_attributes=True)


class PolicyResponse(Policy):
    """A holistic view of a Policy record, including all foreign keys by default."""

    rules: Optional[list[RuleResponse]] = None
    drp_action: Optional[DrpAction] = None
    conditions: dict[str, Any] = {}

    @model_validator(mode="before")
    @classmethod
    def extract_conditions(cls, values: Any) -> Any:
        """Extract the condition tree from the ORM conditions relationship.

        Returns a dict copy to avoid mutating the ORM object's relationship
        state, which would corrupt the SQLAlchemy session.
        """
        if isinstance(values, dict) or not hasattr(values, "conditions"):
            return values
        orm_conditions = values.conditions
        conditions_data: dict[str, Any] = {}
        if orm_conditions and orm_conditions[0].condition_tree:
            conditions_data = orm_conditions[0].condition_tree
        data = {
            field_name: getattr(values, field_name)
            for field_name in cls.model_fields
            if field_name != "conditions" and hasattr(values, field_name)
        }
        data["conditions"] = conditions_data
        return data


class BulkPutRuleTargetResponse(BulkResponse):
    """Schema with mixed success/failure responses for Bulk Create/Update of RuleTarget responses."""

    succeeded: list[RuleTarget]
    failed: list[BulkUpdateFailed]


class BulkPutRuleResponse(BulkResponse):
    """Schema with mixed success/failure responses for Bulk Create/Update of Rule responses."""

    succeeded: list[RuleResponse]
    failed: list[BulkUpdateFailed]


class BulkPutPolicyResponse(BulkResponse):
    """Schema with mixed success/failure responses for Bulk Create/Update of Policy responses."""

    succeeded: list[PolicyResponse]
    failed: list[BulkUpdateFailed]
