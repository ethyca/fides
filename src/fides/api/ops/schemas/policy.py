from typing import Any, Dict, List, Optional

from fides.api.ops.models.policy import ActionType, DrpAction
from fides.api.ops.schemas.api import BulkResponse, BulkUpdateFailed
from fides.api.ops.schemas.base_class import BaseSchema
from fides.api.ops.schemas.shared_schemas import FidesOpsKey
from fides.api.ops.schemas.storage.storage import StorageDestinationResponse
from fides.api.ops.util.data_category import DataCategory


class PolicyMaskingSpec(BaseSchema):
    """Models the masking strategy definition"""

    strategy: str
    configuration: Dict[str, Any]


class PolicyMaskingSpecResponse(BaseSchema):
    """
    The schema to use when returning a masking strategy via the API. This schema omits other
    potentially sensitive fields in the masking configuration, for example the encryption
    algorithm.
    """

    strategy: str


class RuleTarget(BaseSchema):
    """An external representation of a Rule's target DataCategory within a Fidesops Policy"""

    name: Optional[str]
    key: Optional[FidesOpsKey]
    data_category: DataCategory  # type: ignore

    class Config:
        """Populate models with the raw value of enum fields, rather than the enum itself"""

        use_enum_values = True


class RuleBase(BaseSchema):
    """An external representation of a Rule within a Fidesops Policy"""

    name: str
    key: Optional[FidesOpsKey]
    action_type: ActionType

    class Config:
        """Populate models with the raw value of enum fields, rather than the enum itself"""

        use_enum_values = True


class RuleCreate(RuleBase):
    """
    The schema to use when creating a Rule. This schema accepts a storage_destination_key
    over a composite object.
    """

    storage_destination_key: Optional[FidesOpsKey]
    masking_strategy: Optional[PolicyMaskingSpec]


class RuleResponse(RuleBase):
    """
    The schema to use when returning a Rule via the API. This schema uses a censored version
    of the `PolicyMaskingSpec` that omits the configuration to avoid exposing secrets.
    """

    storage_destination: Optional[StorageDestinationResponse]
    masking_strategy: Optional[PolicyMaskingSpecResponse]


class Rule(RuleBase):
    """A representation of a Rule that features all storage destination data."""

    storage_destination: Optional[StorageDestinationResponse]
    masking_strategy: Optional[PolicyMaskingSpec]


class Policy(BaseSchema):
    """An external representation of a Fidesops Policy"""

    name: str
    key: Optional[FidesOpsKey]
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
