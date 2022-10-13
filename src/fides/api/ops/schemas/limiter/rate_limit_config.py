from enum import Enum
from typing import Optional

from pydantic import BaseModel


class RateLimitPeriod(str, Enum):
    """
    Defines the periods supported by rate limit config
    """

    second = "second"
    minute = "minute"
    hour = "hour"
    day = "day"


class RateLimitConfig(BaseModel):
    """
    A named variable which can be sourced from identities, dataset references, or connector params. These values
    are used to replace the placeholders in the path, header, query, and body param values.
    """

    rate: str
    period: RateLimitPeriod
    custom_key: Optional[str]
