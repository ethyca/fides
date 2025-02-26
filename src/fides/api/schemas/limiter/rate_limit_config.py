from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, field_validator, model_validator


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
    custom_key: Optional[str] = None

    @field_validator("rate")
    @classmethod
    def rate_more_than_zero(cls, v: int) -> int:
        assert v > 0, "rate must be more than zero"
        return v


class RateLimitConfig(BaseModel):
    """
    A config object which allows configuring rate limits for connectors
    """

    limits: Optional[List[RateLimit]] = None
    enabled: Optional[bool] = True

    @model_validator(mode="after")
    def validate_all(self) -> "RateLimitConfig":
        limits: Optional[List[RateLimit]] = self.limits
        enabled: Optional[bool] = self.enabled

        if enabled:
            assert (
                limits and len(limits) > 0
            ), "limits must be set if rate limiter is enabled"
        if not enabled:
            assert not limits, "limits cannot be set if enabled is false"
        return self
