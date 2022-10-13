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
    A config object which allows configuring rate limits for connectors
    """

    rate: str
    period: RateLimitPeriod
    custom_key: Optional[str]
