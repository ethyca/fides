import pytest
from pydantic import ValidationError

from fides.api.db.seed import DEFAULT_ACCESS_POLICY
from fides.api.schemas.privacy_request import (
    PrivacyRequestCreate,
    PrivacyRequestFilter,
    PrivacyRequestSource,
    PrivacyRequestStatus,
)


class TestPrivacyRequestFilter:
    def test_single_status(self):
        params = PrivacyRequestFilter(status=PrivacyRequestStatus.pending)
        assert params.status == [PrivacyRequestStatus.pending]

    def test_list_of_statuses(self):
        params = PrivacyRequestFilter(
            status=[PrivacyRequestStatus.pending, PrivacyRequestStatus.complete]
        )
        assert params.status == [
            PrivacyRequestStatus.pending,
            PrivacyRequestStatus.complete,
        ]

    def test_none_status(self):
        params = PrivacyRequestFilter(status=None)
        assert params.status is None

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            PrivacyRequestFilter(status="invalid_status")


class TestPrivacyRequestCreate:
    def test_valid_source(self):
        PrivacyRequestCreate(
            **{
                "identity": {"email": "user@example.com"},
                "policy_key": DEFAULT_ACCESS_POLICY,
                "source": PrivacyRequestSource.privacy_center,
            }
        )

    def test_invalid_source(self):
        with pytest.raises(ValidationError):
            PrivacyRequestCreate(
                **{
                    "identity": {"email": "user@example.com"},
                    "policy_key": DEFAULT_ACCESS_POLICY,
                    "source": "Email",
                }
            )
