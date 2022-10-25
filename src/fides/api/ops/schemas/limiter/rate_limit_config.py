from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class RateLimitPeriod(str, Enum):
    """
    Defines the periods supported by rate limit config
    """

    second = "second"
    minute = "minute"
    hour = "hour"
    day = "day"


class RateLimit(BaseModel):
    """
    A config object which allows configuring rate limits for connectors
    """

    rate: int
    period: RateLimitPeriod
    custom_key: Optional[str]


class RateLimitConfig(BaseModel):
    """
    A config object which allows configuring rate limits for connectors
    """

    limits: Optional[List[RateLimit]]
    enabled: Optional[bool] = True
