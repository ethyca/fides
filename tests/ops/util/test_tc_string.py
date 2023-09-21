import uuid

import pytest
from iab_tcf import decode_v2
from pydantic import ValidationError
from sqlalchemy.orm import Session

from fides.api.api.v1.endpoints.privacy_experience_endpoints import (
    _build_experience_dict,
    hash_experience,
)
from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.models.sql_models import PrivacyDeclaration, System
from fides.api.util.tcf.tc_model import build_tc_model
from fides.api.util.tcf.tc_string import TCModel, build_tc_string


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


@pytest.fixture
def skimbit_system(db):
    """Add system that only has purposes with LI legal basis"""
    system = System.create(
        db=db,
        data={
            "fides_key": f"skimbit{uuid.uuid4()}",
            "vendor_id": "46",
            "name": f"Skimbit (Skimlinks, Taboola)",
            "description": "Skimbit, a Taboola company, specializes in data-driven advertising and provides tools for brands and advertisers to analyze customer behavior and deliver targeted and personalized ads.",
            "organization_fides_key": "default_organization",
            "system_type": "Service",
        },
    )

    # Add Legitimate Interest-related Purposes
    for data_use in [
        "analytics.reporting.ad_performance",  # Purpose 7
        "analytics.reporting.content_performance",  # Purpose 8
        "functional.service.improve",  # Purpose 10
        "essential.service.security"  # Special Purpose 1
        "essential.fraud_detection",  # Special Purpose 1
        "marketing.advertising.serving",  # Special Purpose 2
    ]:
        # Includes Feature 3
        PrivacyDeclaration.create(
            db=db,
            data={
                "system_id": system.id,
                "data_use": data_use,
                "legal_basis_for_processing": "Legitimate interests",
                "features": [
                    "Identify devices based on information transmitted automatically"
                ],
            },
        )


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
            TCModel(cmp_id=-1)

        m = TCModel(cmp_id="100")  # This can be coerced to an integer
        assert m.cmp_id == 100

        m = TCModel(cmp_id=1.11)
        assert m.cmp_id == 1

    def test_invalid_vendor_list_version(self):
        with pytest.raises(ValidationError):
            TCModel(vendor_list_version=-1)

        m = TCModel(vendor_list_version="100")  # This can be coerced to an integer
        assert m.vendor_list_version == 100

        m = TCModel(vendor_list_version=1.11)
        assert m.vendor_list_version == 1

    def test_invalid_policy_version(self):
        with pytest.raises(ValidationError):
            TCModel(policy_version=-1)

        m = TCModel(policy_version="100")  # This can be coerced to an integer
        assert m.policy_version == 100

        m = TCModel(policy_version=1.11)
        assert m.policy_version == 1  # Coerced to closed integer

    def test_invalid_cmp_version(self):
        with pytest.raises(ValidationError):
            TCModel(cmp_version=-1)

        with pytest.raises(ValidationError):
            TCModel(cmp_version=0)

        m = TCModel(cmp_version="100")  # This can be coerced to an integer
        assert m.cmp_version == 100

        m = TCModel(cmp_version=1.11)
        assert m.cmp_version == 1  # Coerced to closed integer

    def test_invalid_publisher_country_code(self):
        with pytest.raises(ValidationError):
            TCModel(publisher_country_code="USA")

        with pytest.raises(ValidationError):
            TCModel(publisher_country_code="^^")

        m = TCModel(publisher_country_code="aa")
        assert m.publisher_country_code == "AA"

    def test_filter_purpose_legitimate_interests(self):
        m = TCModel(purpose_legitimate_interests=[1, 2, 3, 4, 7])
        assert m.purpose_legitimate_interests == [2, 7]

    def test_consent_language(self):
        m = TCModel(consent_language="English")
        assert m.consent_language == "EN"

    @pytest.mark.usefixtures("captify_technologies_system")
    def test_build_tc_string_captify_accept_all(self, db):
        model = build_tc_model(db, UserConsentPreference.opt_in)

        assert model.cmp_id == 12
        assert model.vendor_list_version == 18
        assert model.policy_version == 4
        assert model.cmp_version == 1
        assert model.consent_screen == 1

        assert model.vendor_consents == [2]
        assert model.vendor_legitimate_interests == []
        assert model.purpose_consents == [1, 2, 3, 4, 7, 9, 10]
        assert model.purpose_legitimate_interests == []
        assert model.special_feature_optins == [2]

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

    @pytest.mark.usefixtures("emerse_system")
    def test_build_tc_string_emerse_accept_all(self, db):
        model = build_tc_model(db, UserConsentPreference.opt_in)

        assert model.cmp_id == 12
        assert model.vendor_list_version == 18
        assert model.policy_version == 4
        assert model.cmp_version == 1
        assert model.consent_screen == 1

        assert model.purpose_consents == [1, 3, 4]
        assert model.purpose_legitimate_interests == [2, 7, 8, 9]
        assert model.vendor_consents == [8]
        assert model.vendor_legitimate_interests == [8]
        assert model.special_feature_optins == []

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

    @pytest.mark.usefixtures("skimbit_system")
    def test_build_tc_string_skimbit_accept_all(self, db):
        model = build_tc_model(db, UserConsentPreference.opt_in)

        assert model.cmp_id == 12
        assert model.vendor_list_version == 18
        assert model.policy_version == 4
        assert model.cmp_version == 1
        assert model.consent_screen == 1

        assert model.purpose_consents == []
        assert model.purpose_legitimate_interests == [7, 8, 10]
        assert model.vendor_consents == []
        assert model.vendor_legitimate_interests == [46]
        assert model.special_feature_optins == []

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
        assert decoded.purposes_legitimate_interests == {
            1: False,
            2: False,
            3: False,
            4: False,
            5: False,
            6: False,
            7: True,
            8: True,
            9: False,
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
        assert decoded.purpose_one_treatment is False
        assert decoded.publisher_cc == b"AA"
        assert decoded.consented_vendors == {}
        assert decoded.interests_vendors == {
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
            25: False,
            26: False,
            27: False,
            28: False,
            29: False,
            30: False,
            31: False,
            32: False,
            33: False,
            34: False,
            35: False,
            36: False,
            37: False,
            38: False,
            39: False,
            40: False,
            41: False,
            42: False,
            43: False,
            44: False,
            45: False,
            46: True,
        }

        assert decoded.pub_restriction_entries == []

    @pytest.mark.parametrize(
        "system_fixture",
        [("captify_technologies_system"), ("emerse_system"), ("skimbit_system")],
    )
    def test_build_tc_string_generic_reject_all(self, system_fixture, db):
        model = build_tc_model(db, UserConsentPreference.opt_out)

        assert model.cmp_id == 12
        assert model.vendor_list_version == 18
        assert model.policy_version == 4
        assert model.cmp_version == 1
        assert model.consent_screen == 1

        assert model.purpose_consents == []
        assert model.purpose_legitimate_interests == []
        assert model.vendor_consents == []
        assert model.vendor_legitimate_interests == []
        assert model.special_feature_optins == []

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
        assert decoded.consented_vendors == {}
        assert decoded.interests_vendors == {}
        assert decoded.pub_restriction_entries == []
