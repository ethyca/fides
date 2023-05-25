from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, root_validator, validator


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

    @validator("rate")
    def rate_more_than_zero(cls, v: int) -> int:
        assert v > 0, "rate must be more than zero"
        return v


class RateLimitConfig(BaseModel):
    """
    A config object which allows configuring rate limits for connectors
    """

    limits: Optional[List[RateLimit]]
    enabled: Optional[bool] = True

    @root_validator
    def validate_all(cls, values: Dict) -> Dict:
        limits: Optional[List[RateLimit]] = values["limits"]
        enabled: Optional[bool] = values["enabled"]

        if enabled:
            assert (
                limits and len(limits) > 0
            ), "limits must be set if rate limiter is enabled"
        if not enabled:
            assert not limits, "limits cannot be set if enabled is false"
        return values
