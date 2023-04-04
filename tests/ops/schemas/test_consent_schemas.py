import pytest
from pydantic import ValidationError

from fides.api.ops.models.privacy_notice import PrivacyNoticeRegion
from fides.api.ops.schemas.privacy_notice import PrivacyNoticeHistory
from fides.api.ops.schemas.privacy_request import (
    Consent,
    PrivacyRequestConsentPreference,
)


class TestPrivacyRequestSetConsentPreferenceSchema:
    def test_preference_with_respect_to_data_use(self):
        preference = Consent(
            data_use="advertising",
            opt_in=True,
        )

        assert preference.privacy_notice_id is None
        assert preference.privacy_notice_version is None
        assert preference.data_use == "advertising"
        assert preference.opt_in is True

    def test_preference_with_respect_to_privacy_notice(self, privacy_notice):
        preference = Consent(
            privacy_notice_id=privacy_notice.id,
            privacy_notice_version=privacy_notice.version,
            user_geography=PrivacyNoticeRegion.us_co,
            opt_in=False,
            has_gpc_flag=False,
            data_use_description="Description that should not be here",
        )

        assert preference.privacy_notice_id == privacy_notice.id
        assert preference.privacy_notice_version == 1.0
        assert preference.data_use is None
        assert preference.opt_in is False
        assert preference.data_use_description is None
        assert preference.has_gpc_flag is None
        assert preference.user_geography == PrivacyNoticeRegion.us_co.value

    def test_must_specify_privacy_notice_id_and_version(self, privacy_notice):
        with pytest.raises(ValidationError):
            Consent(
                privacy_notice_id=privacy_notice.id,
                privacy_notice_version=None,
                user_geography=PrivacyNoticeRegion.us_co,
                opt_in=False,
                has_gpc_flag=False,
            )

    def test_mixing_old_and_new_workflows(self, privacy_notice):
        with pytest.raises(ValidationError):
            Consent(
                privacy_notice_id=privacy_notice.id,
                privacy_notice_version=privacy_notice.version,
                user_geoography=PrivacyNoticeRegion.us_co,
                opt_in=False,
                has_gpc_flag=False,
                data_use="data use that should not be here",
                data_use_description="Description that should not be here",
            )


class TestPrivacyRequestConsentPreference:
    def test_define_privacy_request_consent_preference(self, privacy_notice):
        PrivacyRequestConsentPreference(
            privacy_notice_id=privacy_notice.id,
            privacy_notice_version=privacy_notice.version,
            user_geoography=PrivacyNoticeRegion.us_co,
            opt_in=False,
            privacy_notice_history=PrivacyNoticeHistory(
                version=1,
                name=privacy_notice.histories[0].name,
                regions=privacy_notice.histories[0].regions,
                consent_mechanism=privacy_notice.histories[0].consent_mechanism.value,
                data_uses=privacy_notice.histories[0].data_uses,
                enforcement_level=privacy_notice.histories[0].enforcement_level.value,
                id=privacy_notice.histories[0].id,
                privacy_notice_id=privacy_notice.id,
            ),
        )

    def test_privacy_notice_mismatch(self, privacy_notice):
        with pytest.raises(ValidationError):
            PrivacyRequestConsentPreference(
                privacy_notice_id=privacy_notice.id,
                privacy_notice_version=privacy_notice.version,
                user_geoography=PrivacyNoticeRegion.us_co,
                opt_in=False,
                privacy_notice_history=PrivacyNoticeHistory(
                    version=1,
                    name=privacy_notice.histories[0].name,
                    regions=privacy_notice.histories[0].regions,
                    consent_mechanism=privacy_notice.histories[
                        0
                    ].consent_mechanism.value,
                    data_uses=privacy_notice.histories[0].data_uses,
                    enforcement_level=privacy_notice.histories[
                        0
                    ].enforcement_level.value,
                    id=privacy_notice.histories[0].id,
                    privacy_notice_id=5,
                ),
            )

    def test_privacy_notice_version_mismatch(self, privacy_notice):
        with pytest.raises(ValidationError):
            PrivacyRequestConsentPreference(
                privacy_notice_id=privacy_notice.id,
                privacy_notice_version=privacy_notice.version,
                user_geoography=PrivacyNoticeRegion.us_co,
                opt_in=False,
                privacy_notice_history=PrivacyNoticeHistory(
                    version=1000,
                    name=privacy_notice.histories[0].name,
                    regions=privacy_notice.histories[0].regions,
                    consent_mechanism=privacy_notice.histories[
                        0
                    ].consent_mechanism.value,
                    data_uses=privacy_notice.histories[0].data_uses,
                    enforcement_level=privacy_notice.histories[
                        0
                    ].enforcement_level.value,
                    id=privacy_notice.histories[0].id,
                    privacy_notice_id=privacy_notice.id,
                ),
            )
