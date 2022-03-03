from typing import Union

from pydantic import BaseModel


class StrategyConfiguration(BaseModel):
    """Base class for strategy configuration"""


class UnwrapPostProcessorConfiguration(StrategyConfiguration):
    """Dynamic JSON path access"""

    data_path: str


class IdentityParamRef(BaseModel):
    """A reference to the identity type in the filter Post Processor Config"""

    identity: str


class FilterPostProcessorConfiguration(StrategyConfiguration):
    """Returns objects where a field has a given value"""

    field: str
    value: Union[str, IdentityParamRef]
