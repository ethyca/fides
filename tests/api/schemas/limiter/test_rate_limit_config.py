import pytest
from pydantic.error_wrappers import ValidationError

from fides.api.schemas.limiter.rate_limit_config import (
    RateLimit,
    RateLimitConfig,
    RateLimitPeriod,
)


class TestRateLimitCongi:
    def test_rate_less_than_zero_validation(self):
        with pytest.raises(ValidationError):
            RateLimit(rate=0, period=RateLimitPeriod.second)

    def test_limits_set_if_disabled_validation(self):
        with pytest.raises(ValidationError):
            RateLimitConfig(
                limits=[RateLimit(rate=10, period=RateLimitPeriod.second)],
                enabled=False,
            )

    def test_limits_not_set_if_enabled_validation(self):
        with pytest.raises(ValidationError):
            RateLimitConfig(limits=[])
