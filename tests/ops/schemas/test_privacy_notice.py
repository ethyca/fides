import pytest
from fideslang import DataUse as DataUse
from starlette.exceptions import HTTPException

from fides.api.ctl.sql_models import DataUse as sql_DataUse
from fides.api.ops.models.privacy_notice import (
    ConsentMechanism,
    EnforcementLevel,
    PrivacyNoticeRegion,
)
from fides.api.ops.schemas.privacy_notice import PrivacyNotice, PrivacyNoticeCreation


class TestPrivacyNoticeSchema:
    @pytest.fixture(scope="function")
    def privacy_notice_request(self):
        return PrivacyNoticeCreation(
            name="sample privacy notice",
            regions=[PrivacyNoticeRegion.us_ca],
            consent_mechanism=ConsentMechanism.opt_in,
            data_uses=["placeholder"],
            enforcement_level=EnforcementLevel.system_wide,
        )

    @pytest.fixture(scope="function")
    def custom_data_use(self, db):
        return sql_DataUse.create(
            db=db,
            data=DataUse(
                fides_key="new_data_use",
                organization_fides_key="default_organization",
                name="New data use",
                description="A test data use",
                parent_key=None,
                is_default=True,
            ).dict(),
        )

    @pytest.mark.usefixtures("load_default_data_uses")
    def test_validate_data_uses_invalid(
        self, db, privacy_notice_request: PrivacyNoticeCreation
    ):
        privacy_notice_request.data_uses = ["invalid_data_use"]
        with pytest.raises(HTTPException):
            PrivacyNotice.validate_notice_data_uses([privacy_notice_request], db)

        privacy_notice_request.data_uses = ["advertising", "invalid_data_use"]
        with pytest.raises(HTTPException):
            PrivacyNotice.validate_notice_data_uses([privacy_notice_request], db)

        privacy_notice_request.data_uses = [
            "advertising",
            "advertising.invalid_data_use",
        ]
        with pytest.raises(HTTPException):
            PrivacyNotice.validate_notice_data_uses([privacy_notice_request], db)

    @pytest.mark.usefixtures("load_default_data_uses")
    def test_validate_data_uses_default_taxonomy(
        self, db, privacy_notice_request: PrivacyNoticeCreation
    ):
        privacy_notice_request.data_uses = ["advertising"]
        PrivacyNotice.validate_notice_data_uses([privacy_notice_request], db)
        privacy_notice_request.data_uses = ["advertising", "provide"]
        PrivacyNotice.validate_notice_data_uses([privacy_notice_request], db)
        privacy_notice_request.data_uses = ["advertising", "provide", "provide.service"]
        PrivacyNotice.validate_notice_data_uses([privacy_notice_request], db)

    @pytest.mark.usefixtures("load_default_data_uses")
    def test_validate_data_uses_custom_uses(
        self,
        db,
        privacy_notice_request: PrivacyNoticeCreation,
        custom_data_use: sql_DataUse,
    ):
        """
        Ensure custom data uses added to the DB are considered valid
        """

        privacy_notice_request.data_uses = [custom_data_use.fides_key]
        PrivacyNotice.validate_notice_data_uses([privacy_notice_request], db)
        privacy_notice_request.data_uses = ["advertising", custom_data_use.fides_key]
        PrivacyNotice.validate_notice_data_uses([privacy_notice_request], db)
