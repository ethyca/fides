from enum import Enum as EnumType
from typing import Any, Dict, List, Optional

from fideslang.validation import FidesKey

from fides.api.schemas.api import BulkResponse, BulkUpdateFailed
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.storage.storage import StorageDestinationResponse


class ActionType(str, EnumType):
    """The purpose of a particular privacy request"""

    access = "access"
    consent = "consent"
    erasure = "erasure"
    update = "update"


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
    configuration: Dict[str, Any]


class PolicyMaskingSpecResponse(FidesSchema):
    """
    The schema to use when returning a masking strategy via the API. This schema omits other
    potentially sensitive fields in the masking configuration, for example the encryption
    algorithm.
    """

    strategy: str


class RuleTarget(FidesSchema):
    """An external representation of a Rule's target DataCategory within a Fidesops Policy"""

    name: Optional[str]
    key: Optional[FidesKey]
    # `data_category` is type str so that we can validate its contents against the DB records
    # outside of the schemas
    data_category: str

    class Config:
        """Populate models with the raw value of enum fields, rather than the enum itself"""

        use_enum_values = True


class RuleBase(FidesSchema):
    """An external representation of a Rule within a Fidesops Policy"""

    name: str
    key: Optional[FidesKey]
    action_type: ActionType

    class Config:
        """Populate models with the raw value of enum fields, rather than the enum itself"""

        use_enum_values = True


class RuleCreate(RuleBase):
    """
    The schema to use when creating a Rule. This schema accepts a storage_destination_key
    over a composite object.
    """

    storage_destination_key: Optional[FidesKey]
    masking_strategy: Optional[PolicyMaskingSpec]


class RuleResponse(RuleBase):
    """
    The schema to use when returning a Rule via the API. This schema uses a censored version
    of the `PolicyMaskingSpec` that omits the configuration to avoid exposing secrets.
    """

    storage_destination: Optional[StorageDestinationResponse]
    masking_strategy: Optional[PolicyMaskingSpecResponse]


class RuleResponseWithTargets(RuleBase):
    """
    The schema to use when returning a Rule via the API and when including the Rule's targets
    is desired. This schema uses a censored version of the `PolicyMaskingSpec` that omits the
    configuration to avoid exposing secrets.
    """

    targets: Optional[List[RuleTarget]]
    storage_destination: Optional[StorageDestinationResponse]
    masking_strategy: Optional[PolicyMaskingSpecResponse]


class Rule(RuleBase):
    """A representation of a Rule that features all storage destination data."""

    storage_destination: Optional[StorageDestinationResponse]
    masking_strategy: Optional[PolicyMaskingSpec]


class Policy(FidesSchema):
    """An external representation of a Fidesops Policy"""

    name: str
    key: Optional[FidesKey]
    drp_action: Optional[DrpAction]
    execution_timeframe: Optional[int]

    class Config:
        """Populate models with the raw value of enum fields, rather than the enum itself"""

        use_enum_values = True
        orm_mode = True


class PolicyResponse(Policy):
    """A holistic view of a Policy record, including all foreign keys by default."""

    rules: Optional[List[RuleResponse]]
    drp_action: Optional[DrpAction]


class BulkPutRuleTargetResponse(BulkResponse):
    """Schema with mixed success/failure responses for Bulk Create/Update of RuleTarget responses."""

    succeeded: List[RuleTarget]
    failed: List[BulkUpdateFailed]


class BulkPutRuleResponse(BulkResponse):
    """Schema with mixed success/failure responses for Bulk Create/Update of Rule responses."""

    succeeded: List[RuleResponse]
    failed: List[BulkUpdateFailed]


class BulkPutPolicyResponse(BulkResponse):
    """Schema with mixed success/failure responses for Bulk Create/Update of Policy responses."""

    succeeded: List[PolicyResponse]
    failed: List[BulkUpdateFailed]
