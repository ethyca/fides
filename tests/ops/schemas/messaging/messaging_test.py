import pytest

from fides.api.schemas.messaging.messaging import (
    SubjectIdentityVerificationBodyParams,
)


@pytest.mark.parametrize("ttl, expected", [(600, 10), (155, 2), (33, 0)])
def test_get_verification_code_ttl_minutes_calc(ttl, expected):
    result = SubjectIdentityVerificationBodyParams(
        verification_code="123123", verification_code_ttl_seconds=ttl
    )
    assert result.get_verification_code_ttl_minutes() == expected
