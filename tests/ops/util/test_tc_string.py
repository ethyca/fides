import uuid

import pytest
from iab_tcf import decode_v2
from pydantic import ValidationError
from sqlalchemy.orm import Session

from fides.api.api.v1.endpoints.privacy_experience_endpoints import (
    _build_experience_dict,
    embed_experience_details,
    hash_experience,
)
from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.models.sql_models import PrivacyDeclaration, System
from fides.api.util.tc_string import TCModel, build_tc_model, build_tc_string


# Comparison string opt in to all for Captify
# "CPyZhwAPyZhwAAMABBENDUCEAPLAAAAAAAAAABEAAAAA.IgoNV_H__bX9v8X7_6ft0eY1f9_j77uQxBhfJs-4F3LvW_JwX_2E7NF36tq4KmRoEu3ZBIUNtHJnUTVmxaokVrzHsak2cpTNKJ-BkkHMRe2dYCF5vm5tjeQKZ5_p_d3f52T_97dv-39z33913v3d9f-_1-Pjde5_9H_v_fRfb-_If9_7-_8v8_t_rk2_eT1__9-_____-_______2AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQ"
@pytest.fixture(scope="function")
def captify_technologies_system(db: Session) -> System:
    """Add system that only has purposes with Consent legal basis"""
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


@pytest.fixture(scope="function")
def emerse_system(db: Session) -> System:
    """This system has purposes that are both consent and legitimate interest legal basis"""
    system = System.create(
        db=db,
        data={
            "fides_key": f"emerse{uuid.uuid4()}",
            "vendor_id": "8",
            "name": f"Emerse",
            "description": "Emerse Sverige AB is a provider of programmatic advertising solutions, offering advertisers and publishers tools to manage and optimize their digital ad campaigns.",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    # Add Consent-related Purposes
    for data_use in [
        "functional.storage",  # Purpose 1
        "marketing.advertising.profiling",  # Purpose 3
        "marketing.advertising.third_party.targeted",  # Purpose 4
        "marketing.advertising.first_party.targeted",  # Purpose 4
    ]:
        # Includes Feature 2, Special Feature 2
        PrivacyDeclaration.create(
            db=db,
            data={
                "system_id": system.id,
                "data_use": data_use,
                "legal_basis_for_processing": "Consent",
                "features": [
                    "Match and combine data from other data sources",  # Feature 1
                    "Link different devices",  # Feature 2
                ],
            },
        )

    # Add Legitimate Interest-related Purposes
    for data_use in [
        "marketing.advertising.negative_targeting",  # Purpose 2
        "marketing.advertising.first_party.contextual",  # Purpose 2
        "marketing.advertising.frequency_capping",  # Purpose 2
        "analytics.reporting.ad_performance",  # Purpose 7
        "analytics.reporting.content_performance",  # Purpose 8
        "analytics.reporting.campaign_insights",  # Purpose 9
        "essential.fraud_detection",  # Special Purpose 1
        "essential.service.security",  # Special Purpose 1
        "marketing.advertising.serving",  # Special Purpose 2
    ]:
        # Includes Feature 2, Special Feature 2
        PrivacyDeclaration.create(
            db=db,
            data={
                "system_id": system.id,
                "data_use": data_use,
                "legal_basis_for_processing": "Legitimate interests",
                "features": [
                    "Match and combine data from other data sources",  # Feature 1
                    "Link different devices",  # Feature 2
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

    def test_build_tc_string_captify_accept_all(self, db, captify_technologies_system):
        model = build_tc_model(db, UserConsentPreference.opt_in)

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
        decoded = decode_v2(tc_str)

        assert decoded.version == 2
        assert decoded.cmp_id == 12
        assert decoded.cmp_version == 1
        assert decoded.consent_screen == 1
        assert decoded.consent_language == b"EN"
        assert decoded.vendor_list_version == 18
        assert decoded.tcf_policy_version == 4
        assert decoded.is_service_specific is False
        assert decoded.use_non_standard_stacks is False
        assert decoded.special_features_optin == {
            1: False,
            2: True,
            3: False,
            4: False,
            5: False,
            6: False,
            7: False,
            8: False,
            9: False,
            10: False,
            11: False,
            12: False,
        }
        assert decoded.purposes_consent == {
            1: True,
            2: True,
            3: True,
            4: True,
            5: False,
            6: False,
            7: True,
            8: False,
            9: True,
            10: True,
            11: False,
            12: False,
            13: False,
            14: False,
            15: False,
            16: False,
            17: False,
            18: False,
            19: False,
            20: False,
            21: False,
            22: False,
            23: False,
            24: False,
        }
        assert decoded.purposes_legitimate_interests == {
            1: False,
            2: False,
            3: False,
            4: False,
            5: False,
            6: False,
            7: False,
            8: False,
            9: False,
            10: False,
            11: False,
            12: False,
            13: False,
            14: False,
            15: False,
            16: False,
            17: False,
            18: False,
            19: False,
            20: False,
            21: False,
            22: False,
            23: False,
            24: False,
        }
        assert decoded.purpose_one_treatment is False
        assert decoded.publisher_cc == b"AA"
        assert decoded.consented_vendors == {1: False, 2: True}
        assert decoded.interests_vendors == {}
        assert decoded.pub_restriction_entries == []

    def test_build_tc_string_emerse_accept_all(self, db, emerse_system):
        model = build_tc_model(db, UserConsentPreference.opt_in)

        assert model.cmpId == 12
        assert model.vendorListVersion == 18
        assert model.policyVersion == 4
        assert model.cmpVersion == 1
        assert model.consentScreen == 1

        assert model.purposeConsents == [1, 3, 4]
        assert model.purposeLegitimateInterests == [2, 7, 8, 9]
        assert model.vendorConsents == [8]
        assert model.vendorLegitimateInterests == [8]
        assert model.specialFeatureOptins == []

        # Build the TC string and then decode it
        tc_str = build_tc_string(model)
        decoded = decode_v2(tc_str)

        assert decoded.version == 2
        assert decoded.cmp_id == 12
        assert decoded.cmp_version == 1
        assert decoded.consent_screen == 1
        assert decoded.consent_language == b"EN"
        assert decoded.vendor_list_version == 18
        assert decoded.tcf_policy_version == 4
        assert decoded.is_service_specific is False
        assert decoded.use_non_standard_stacks is False
        assert decoded.special_features_optin == {
            1: False,
            2: False,
            3: False,
            4: False,
            5: False,
            6: False,
            7: False,
            8: False,
            9: False,
            10: False,
            11: False,
            12: False,
        }
        assert decoded.purposes_consent == {
            1: True,
            2: False,
            3: True,
            4: True,
            5: False,
            6: False,
            7: False,
            8: False,
            9: False,
            10: False,
            11: False,
            12: False,
            13: False,
            14: False,
            15: False,
            16: False,
            17: False,
            18: False,
            19: False,
            20: False,
            21: False,
            22: False,
            23: False,
            24: False,
        }
        assert decoded.purposes_legitimate_interests == {
            1: False,
            2: True,
            3: False,
            4: False,
            5: False,
            6: False,
            7: True,
            8: True,
            9: True,
            10: False,
            11: False,
            12: False,
            13: False,
            14: False,
            15: False,
            16: False,
            17: False,
            18: False,
            19: False,
            20: False,
            21: False,
            22: False,
            23: False,
            24: False,
        }
        assert decoded.purpose_one_treatment is False
        assert decoded.publisher_cc == b"AA"
        assert decoded.consented_vendors == {
            1: False,
            2: False,
            3: False,
            4: False,
            5: False,
            6: False,
            7: False,
            8: True,
        }
        assert decoded.interests_vendors == {
            1: False,
            2: False,
            3: False,
            4: False,
            5: False,
            6: False,
            7: False,
            8: True,
        }
        assert decoded.pub_restriction_entries == []
