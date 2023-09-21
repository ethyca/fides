import uuid
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from fides.api.api.v1.endpoints.privacy_experience_endpoints import (
    _build_experience_dict,
    hash_experience,
    embed_experience_details,
)
from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.models.sql_models import System, PrivacyDeclaration
from fides.api.util.tc_string import build_tc_model, TCModel, build_tc_string


@pytest.fixture(scope="function")
def captify_technologies_system(db: Session) -> System:
    system = System.create(
        db=db,
        data={
            "fides_key": f"captify_{uuid.uuid4()}",
            "vendor_id": "2",
            "name": f"Captify",
            "description": "Captify is a search intelligence platform that helps brands and advertisers leverage search insights to improve their ad targeting and relevance.",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
            "uses_profiling": False,
            "legal_basis_for_transfers": ["SCCs"],
        },
    )

    for data_use in [
        "functional.storage",  # Purpose 1
        "marketing.advertising.negative_targeting",  # Purpose 2
        "marketing.advertising.frequency_capping",  # Purpose 2
        "marketing.advertising.first_party.contextual",  # Purpose 2
        "marketing.advertising.profiling",  # Purpose 3
        "marketing.advertising.first_party.targeted",  # Purpose 4
        "marketing.advertising.third_party.targeted",  # Purpose 4
        "analytics.reporting.ad_performance",  # Purpose 7
        "analytics.reporting.campaign_insights",  # Purpose 9
        "functional.service.improve",  # Purpose 10
        "essential.fraud_detection",  # Special Purpose 1
        "essential.service.security"  # Special Purpose 1
        "marketing.advertising.serving",  # Special Purpose 2
    ]:
        # Includes Feature 2, Special Feature 2
        PrivacyDeclaration.create(
            db=db,
            data={
                "system_id": system.id,
                "data_use": data_use,
                "legal_basis_for_processing": "Consent",
                "features": [
                    "Link different devices",
                    "Actively scan device characteristics for identification",
                ],
            },
        )

    db.refresh(system)
    return system


class TestHashExperience:
    def test_hash_experience(
        self, db, tcf_system, privacy_experience_france_tcf_overlay
    ):
        # These ids will change each time the fixture is creating them, so setting them here
        privacy_experience_france_tcf_overlay.experience_config.experience_config_history_id = (
            "test_experience_config_history_id"
        )
        privacy_experience_france_tcf_overlay.id = "test_experience_id"

        hashed = "224edc90c8a349e60defde4d06e798c2ccc0ff699cabfe2cc8e37669217533b1"

        built_experience_dict_1 = _build_experience_dict(
            db, privacy_experience_france_tcf_overlay
        )
        built_experience_dict_2 = _build_experience_dict(
            db, privacy_experience_france_tcf_overlay
        )
        assert built_experience_dict_1 == built_experience_dict_2

        first_hashed_dict = hash_experience(db, privacy_experience_france_tcf_overlay)
        second_hashed_dict = hash_experience(db, privacy_experience_france_tcf_overlay)

        assert first_hashed_dict == second_hashed_dict == hashed


class TestBuildTCModel:
    def test_invalid_cmp_id(self):
        with pytest.raises(ValidationError):
            TCModel(cmpId=-1)

        m = TCModel(cmpId="100")  # This can be coerced to an integer
        assert m.cmpId == 100

        m = TCModel(cmpId=1.11)
        assert m.cmpId == 1

    def test_invalid_vendor_list_version(self):
        with pytest.raises(ValidationError):
            TCModel(vendorListVersion=-1)

        m = TCModel(vendorListVersion="100")  # This can be coerced to an integer
        assert m.vendorListVersion == 100

        m = TCModel(vendorListVersion=1.11)
        assert m.vendorListVersion == 1

    def test_invalid_policyversion(self):
        with pytest.raises(ValidationError):
            TCModel(policyVersion=-1)

        m = TCModel(policyVersion="100")  # This can be coerced to an integer
        assert m.policyVersion == 100

        m = TCModel(policyVersion=1.11)
        assert m.policyVersion == 1  # Coerced to closed integer

    def test_invalid_cmpVersion(self):
        with pytest.raises(ValidationError):
            TCModel(cmpVersion=-1)

        with pytest.raises(ValidationError):
            TCModel(cmpVersion=0)

        m = TCModel(cmpVersion="100")  # This can be coerced to an integer
        assert m.cmpVersion == 100

        m = TCModel(cmpVersion=1.11)
        assert m.cmpVersion == 1  # Coerced to closed integer

    def test_invalid_publisherCountryCode(self):
        with pytest.raises(ValidationError):
            TCModel(publisherCountryCode="USA")

        with pytest.raises(ValidationError):
            TCModel(publisherCountryCode="^^")

        m = TCModel(publisherCountryCode="aa")
        assert m.publisherCountryCode == "AA"

    def test_filter_purpose_legitimate_interests(self):
        m = TCModel(purposeLegitimateInterests=[1, 2, 3, 4, 7])
        assert m.purposeLegitimateInterests == [2, 7]

    def test_consent_language(self):
        m = TCModel(consentLanguage="English")
        assert m.consentLanguage == "EN"

    def test_build_tc_model_accept_all(
        self, db, captify_technologies_system, privacy_experience_france_tcf_overlay
    ):
        embed_experience_details(
            db=db,
            privacy_experience=privacy_experience_france_tcf_overlay,
            show_disabled=False,
            systems_applicable=True,
            fides_user_provided_identity=None,
            should_unescape="true",
        )

        model = build_tc_model(
            privacy_experience_france_tcf_overlay, UserConsentPreference.opt_in
        )

        assert model.cmpId == 12
        assert model.vendorListVersion == 18
        assert model.policyVersion == 4
        assert model.cmpVersion == 1
        assert model.consentScreen == 1

        assert model.vendorConsents == [2]
        assert model.vendorLegitimateInterests == []
        assert model.purposeConsents == [1, 2, 3, 4, 7, 9, 10]
        assert model.purposeLegitimateInterests == []
        assert model.specialFeatureOptins == [2]

        tc_str = build_tc_string(model)
