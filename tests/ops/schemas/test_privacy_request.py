import pytest
from pydantic import ValidationError

from fides.api.models.privacy_request import PrivacyRequestStatus
from fides.api.schemas.privacy_request import PrivacyRequestFilter


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
