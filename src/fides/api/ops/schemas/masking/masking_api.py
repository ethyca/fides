from typing import Any, Dict, List, Union

from pydantic import BaseModel, root_validator

from fides.api.ops.schemas.policy import PolicyMaskingSpec


class MaskingAPIRequest(BaseModel):
    """The API Request for masking operations"""

    values: List[str]
    masking_strategy: Union[PolicyMaskingSpec, List[PolicyMaskingSpec]]
    masking_strategies: List[PolicyMaskingSpec] = []

    @root_validator(pre=False)
    def build_masking_strategies(cls, values: Dict) -> Dict:
        """
        Update "masking_strategies" field by inspecting "masking_strategy".
        The ability to specify one or more masking strategies was added in a
        backwards-compatible way.  Pass in a single masking strategy, or a list
        of masking_strategy objects under "masking_strategy", and we
        set the "masking_strategies" value from there.
        Masking_strategies should not be supplied directly.
        """
        strategy = values.get("masking_strategy")
        values["masking_strategies"] = (
            strategy if isinstance(strategy, list) else [strategy]
        )

        return values


class MaskingAPIResponse(BaseModel):
    """The API Response returned upon masking completion"""

    plain: List[str]
    masked_values: List[Any]
