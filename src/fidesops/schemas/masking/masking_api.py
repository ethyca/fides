from typing import List, Any

from pydantic import BaseModel

from fidesops.schemas.policy import PolicyMaskingSpec


class MaskingAPIRequest(BaseModel):
    """The API Request for masking operations"""

    values: List[str]
    masking_strategy: PolicyMaskingSpec


class MaskingAPIResponse(BaseModel):
    """The API Response returned upon masking completion"""

    plain: List[str]
    masked_values: List[Any]
