import pytest

from fides.config import SecuritySettings


def test_rate_limit_validation():
    """Tests `SecuritySettings.validate_rate_limits` for both request_rate_limit and auth_rate_limit"""
    VALID_VALUES = [
        "10 per hour",
        "10/hour",
        "10/hour;100/day;2000 per year",
        "100/day, 500/7days",
    ]
    for value in VALID_VALUES:
        assert SecuritySettings.validate_rate_limits(v=value)

    INVALID_VALUE = "invalid-value"
    with pytest.raises(ValueError) as exc:
        SecuritySettings.validate_rate_limits(v=INVALID_VALUE)
