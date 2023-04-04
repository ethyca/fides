import pytest
from pydantic import ValidationError

from fides.api.ops.schemas.privacy_notice import PrivacyNoticeHistory


class TestPrivacyNoticeSchemas:
    def test_privacy_notice_history_minimum_fields(self):
        PrivacyNoticeHistory(
            version=1,
            name="Advertising",
            regions=["us_ca"],
            consent_mechanism="opt_in",
            data_uses=["advertising.first_party"],
            enforcement_level="system_wide",
            id="12345",
            privacy_notice_id="abcde",
        )

    def test_privacy_notice_history_name_required(self):
        with pytest.raises(ValidationError):
            PrivacyNoticeHistory(
                version=1,
                regions=["us_ca"],
                consent_mechanism="opt_in",
                data_uses=["advertising.first_party"],
                enforcement_level="system_wide",
                id="12345",
                privacy_notice_id="abcde",
            )

    def test_privacy_notice_history_one_data_use_required(self):
        with pytest.raises(ValidationError):
            PrivacyNoticeHistory(
                version=1,
                name="Advertising",
                regions=["us_ca"],
                consent_mechanism="opt_in",
                data_uses=[],
                enforcement_level="system_wide",
                id="12345",
                privacy_notice_id="abcde",
            )
