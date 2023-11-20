from typing import Any, List, Union

from pydantic import BaseModel, model_validator

from fides.api.schemas.policy import PolicyMaskingSpec


class MaskingAPIRequest(BaseModel):
    """The API Request for masking operations"""

    values: List[str]
    masking_strategy: Union[PolicyMaskingSpec, List[PolicyMaskingSpec]]
    masking_strategies: List[PolicyMaskingSpec] = []

    @model_validator(mode="after")
    def build_masking_strategies(self) -> "MaskingAPIRequest":
        """
        Update "masking_strategies" field by inspecting "masking_strategy".
        The ability to specify one or more masking strategies was added in a
        backwards-compatible way.  Pass in a single masking strategy, or a list
        of masking_strategy objects under "masking_strategy", and we
        set the "masking_strategies" value from there.
        Masking_strategies should not be supplied directly.
        """
        strategy = self.masking_strategy
        self.masking_strategies = strategy if isinstance(strategy, list) else [strategy]

        return self


class MaskingAPIResponse(BaseModel):
    """The API Response returned upon masking completion"""

    plain: List[str]
    masked_values: List[Any]
