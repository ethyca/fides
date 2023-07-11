from typing import List

from pydantic import BaseModel


class MaskingStrategyConfigurationDescription(BaseModel):
    """The description model for a specific configuration in a masking strategy"""

    key: str
    optional: bool = True
    description: str


class MaskingStrategyDescription(BaseModel):
    """The description model for a masking strategy"""

    name: str
    description: str
    configurations: List[MaskingStrategyConfigurationDescription]
