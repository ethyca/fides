import uuid
from datetime import datetime

import pytest
from iab_tcf import decode_v2
from pydantic import ValidationError
from sqlalchemy.orm import Session

from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.models.sql_models import PrivacyDeclaration, System
from fides.api.util.tcf.experience_meta import (
    TCFVersionHash,
    _build_tcf_version_hash_model,
    build_tcf_version_hash,
)
from fides.api.util.tcf.tc_mobile_data import build_tc_data_for_mobile
from fides.api.util.tcf.tc_model import CMP_ID, convert_tcf_contents_to_tc_model
from fides.api.util.tcf.tc_string import TCModel, build_tc_string
from fides.api.util.tcf.tcf_experience_contents import get_tcf_contents


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


@pytest.fixture(scope="function")
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
    return system


class TestHashTCFExperience:
    @pytest.mark.usefixtures("tcf_system", "privacy_experience_france_tcf_overlay")
    def test_build_tcf_version_hash_model(self, db):
        tcf_contents = get_tcf_contents(db)
        version_hash_model = _build_tcf_version_hash_model(tcf_contents=tcf_contents)
        assert version_hash_model == TCFVersionHash(
            policy_version=4,
            purpose_consents=[8],
            purpose_legitimate_interests=[],
            special_feature_optins=[],
            vendor_consents=[],
            vendor_legitimate_interests=[],
        )

        version_hash = build_tcf_version_hash(tcf_contents)
        assert version_hash == "75fb2dafef58"

    def test_version_hash_model_sorts_ascending(self):
        version_hash_model = TCFVersionHash(
            policy_version=4,
            purpose_consents=[5, 4, 3, 1],
            purpose_legitimate_interests=[7, 8],
            special_feature_optins=[2, 1],
            vendor_consents=[8, 2, 1],
            vendor_legitimate_interests=[141, 14, 1],
        )

        assert version_hash_model.policy_version == 4
        assert version_hash_model.purpose_consents == [1, 3, 4, 5]
        assert version_hash_model.purpose_legitimate_interests == [7, 8]
        assert version_hash_model.special_feature_optins == [1, 2]
        assert version_hash_model.vendor_legitimate_interests == [1, 14, 141]

    @pytest.mark.usefixtures("captify_technologies_system")
    def test_build_tcf_version_hash_removing_declaration(
        self, db, captify_technologies_system
    ):
        tcf_contents = get_tcf_contents(db)
        version_hash_model = _build_tcf_version_hash_model(tcf_contents=tcf_contents)
        assert version_hash_model == TCFVersionHash(
            policy_version=4,
            purpose_consents=[1, 2, 3, 4, 7, 9, 10],
            purpose_legitimate_interests=[],
            special_feature_optins=[2],
            vendor_consents=[2],
            vendor_legitimate_interests=[],
        )

        version_hash = build_tcf_version_hash(tcf_contents)
        assert version_hash == "eaab1c195073"

        # Remove the privacy declaration corresponding to purpose 1
        for decl in captify_technologies_system.privacy_declarations:
            if decl.data_use == "functional.storage":
                decl.delete(db)

        # Recalculate version hash model and version
        tcf_contents = get_tcf_contents(db)
        version_hash_model = _build_tcf_version_hash_model(tcf_contents=tcf_contents)
        assert version_hash_model == TCFVersionHash(
            policy_version=4,
            purpose_consents=[2, 3, 4, 7, 9, 10],
            purpose_legitimate_interests=[],
            special_feature_optins=[2],
            vendor_consents=[2],
            vendor_legitimate_interests=[],
        )

        version_hash = build_tcf_version_hash(tcf_contents)
        assert version_hash == "77ed45ac8d43"

    def test_build_tcf_version_hash_adding_data_use(self, db, emerse_system):
        tcf_contents = get_tcf_contents(db)
        version_hash_model = _build_tcf_version_hash_model(tcf_contents=tcf_contents)
        assert version_hash_model == TCFVersionHash(
            policy_version=4,
            purpose_consents=[1, 3, 4],
            purpose_legitimate_interests=[2, 7, 8, 9],
            special_feature_optins=[],
            vendor_consents=[8],
            vendor_legitimate_interests=[8],
        )

        version_hash = build_tcf_version_hash(tcf_contents)
        assert version_hash == "a2e85860c68b"

        # Adding privacy declaration for purpose 10
        PrivacyDeclaration.create(
            db=db,
            data={
                "system_id": emerse_system.id,
                "data_use": "functional.service.improve",
                "legal_basis_for_processing": "Consent",
                "features": [
                    "Match and combine data from other data sources",  # Feature 1
                    "Link different devices",  # Feature 2
                ],
            },
        )

        # Recalculate version hash model and version
        tcf_contents = get_tcf_contents(db)
        version_hash_model = _build_tcf_version_hash_model(tcf_contents=tcf_contents)
        assert version_hash_model == TCFVersionHash(
            policy_version=4,
            purpose_consents=[1, 3, 4, 10],
            purpose_legitimate_interests=[2, 7, 8, 9],
            special_feature_optins=[],
            vendor_consents=[8],
            vendor_legitimate_interests=[8],
        )

        version_hash = build_tcf_version_hash(tcf_contents)
        assert version_hash == "73c0762c9442"


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

    def test_filter_invalid_vendor_legal_basis(self):
        m = TCModel(
            vendor_consents=[56]
        )  # This vendor has no purposes, and shouldn't be in this list
        assert m.vendor_consents == []

        m = TCModel(
            vendor_legitimate_interests=[56]
        )  # This vendor doesn't have leg int purposes, but it does have
        # special purposes, which allows it to show up here
        assert m.vendor_legitimate_interests == [56]

        m = TCModel(
            vendor_legitimate_interests=[66]
        )  # This vendor doesn't have leg int purposes, or special purposes. It does have flexible purposes,
        # but this isn't an option right now, as is_service_specific is False
        assert m.vendor_legitimate_interests == []

        m = TCModel(
            vendor_legitimate_interests=[66], is_service_specific=True
        )  # This vendor doesn't have leg int purposes, or special purposes. It does have flexible purposes,
        # and is_service_specific, but we don't yet support setting publisher restrictions
        assert m.vendor_legitimate_interests == []

        m = TCModel(vendor_consents=[1231323])
        assert m.vendor_consents == []

    def test_consent_language(self):
        m = TCModel(consent_language="English")
        assert m.consent_language == "EN"

    @pytest.mark.usefixtures("captify_technologies_system")
    def test_build_tc_string_captify_accept_all(self, db):
        tcf_contents = get_tcf_contents(db)
        model = convert_tcf_contents_to_tc_model(
            tcf_contents, UserConsentPreference.opt_in
        )

        assert model.cmp_id == 12
        assert model.vendor_list_version == 20
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
        assert datetime.utcnow().date() == decoded.created.date()
        assert decoded.cmp_id == 12
        assert decoded.cmp_version == 1
        assert decoded.consent_screen == 1
        assert decoded.consent_language == b"EN"
        assert decoded.vendor_list_version == 20
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

        assert (decoded.oob_disclosed_vendors) == {1: False, 2: True}

    @pytest.mark.usefixtures("emerse_system")
    def test_build_tc_string_emerse_accept_all(self, db):
        tcf_contents = get_tcf_contents(db)
        model = convert_tcf_contents_to_tc_model(
            tcf_contents, UserConsentPreference.opt_in
        )

        assert model.cmp_id == 12
        assert model.vendor_list_version == 20
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
        assert decoded.vendor_list_version == 20
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

        assert decoded.oob_disclosed_vendors == {
            1: False,
            2: False,
            3: False,
            4: False,
            5: False,
            6: False,
            7: False,
            8: True,
        }

    @pytest.mark.usefixtures("skimbit_system")
    def test_build_tc_string_skimbit_accept_all(self, db):
        tcf_contents = get_tcf_contents(db)
        model = convert_tcf_contents_to_tc_model(
            tcf_contents, UserConsentPreference.opt_in
        )

        assert model.cmp_id == 12
        assert model.vendor_list_version == 20
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
        assert decoded.vendor_list_version == 20
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

        assert decoded.oob_disclosed_vendors == {
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

    @pytest.mark.usefixtures(
        "skimbit_system", "emerse_system", "captify_technologies_system"
    )
    def test_build_tc_string_three_systems_accept_all(self, db):
        """Do a test combining three gvl systems, and assert data is combined as expected"""
        tcf_contents = get_tcf_contents(db)
        model = convert_tcf_contents_to_tc_model(
            tcf_contents, UserConsentPreference.opt_in
        )

        assert model.cmp_id == 12
        assert model.vendor_list_version == 20
        assert model.policy_version == 4
        assert model.cmp_version == 1
        assert model.consent_screen == 1

        assert model.purpose_consents == [1, 2, 3, 4, 7, 9, 10]
        assert model.purpose_legitimate_interests == [2, 7, 8, 9, 10]
        assert model.vendor_consents == [2, 8]
        assert model.vendor_legitimate_interests == [8, 46]
        assert model.special_feature_optins == [2]

        # Build the TC string and then decode it
        tc_str = build_tc_string(model)

        decoded = decode_v2(tc_str)

        assert decoded.version == 2
        assert decoded.cmp_id == 12
        assert decoded.cmp_version == 1
        assert decoded.consent_screen == 1
        assert decoded.consent_language == b"EN"
        assert decoded.vendor_list_version == 20
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
            2: True,
            3: False,
            4: False,
            5: False,
            6: False,
            7: True,
            8: True,
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
        assert decoded.purpose_one_treatment is False
        assert decoded.publisher_cc == b"AA"
        assert decoded.consented_vendors == {
            1: False,
            2: True,
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

        assert decoded.oob_disclosed_vendors == {
            1: False,
            2: True,
            3: False,
            4: False,
            5: False,
            6: False,
            7: False,
            8: True,
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

    def test_build_tc_string_not_vendor(self, db, skimbit_system):
        """
        Test where we have a system in Fides that has a vendor id that came from our dictionary,
        not the GVL, so the vendor itself shouldn't show up in the string. It's purposes still do,
        but it is removed from the vendor_* and  *_vendors sections
        """
        skimbit_system.vendor_id = "dictionary_id"
        skimbit_system.save(db)

        tcf_contents = get_tcf_contents(db)
        model = convert_tcf_contents_to_tc_model(
            tcf_contents, UserConsentPreference.opt_in
        )

        assert model.cmp_id == 12
        assert model.vendor_list_version == 20
        assert model.policy_version == 4
        assert model.cmp_version == 1
        assert model.consent_screen == 1

        assert model.purpose_consents == []
        assert model.purpose_legitimate_interests == [7, 8, 10]
        assert model.vendor_consents == []
        assert model.vendor_legitimate_interests == []  # This is the primary change
        assert model.special_feature_optins == []

        # Build the TC string and then decode it
        tc_str = build_tc_string(model)

        decoded = decode_v2(tc_str)

        assert decoded.version == 2
        assert decoded.cmp_id == 12
        assert decoded.cmp_version == 1
        assert decoded.consent_screen == 1
        assert decoded.consent_language == b"EN"
        assert decoded.vendor_list_version == 20
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
        assert decoded.interests_vendors == {}  # This is the other primary change

        assert decoded.pub_restriction_entries == []

        assert decoded.oob_disclosed_vendors == {}

    @pytest.mark.parametrize(
        "system_fixture,vendor_id",
        [
            ("captify_technologies_system", 2),
            ("emerse_system", 8),
            ("skimbit_system", 46),
        ],
    )
    def test_build_tc_string_generic_reject_all(
        self, system_fixture, vendor_id, db, request
    ):
        request.getfixturevalue(system_fixture)
        tcf_contents = get_tcf_contents(db)
        model = convert_tcf_contents_to_tc_model(
            tcf_contents, UserConsentPreference.opt_out
        )

        assert model.cmp_id == 12
        assert model.vendor_list_version == 20
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
        assert datetime.utcnow().date() == decoded.created.date()
        assert datetime.utcnow().date() == decoded.last_updated.date()
        assert decoded.cmp_id == 12
        assert decoded.cmp_version == 1
        assert decoded.consent_screen == 1
        assert decoded.consent_language == b"EN"
        assert decoded.vendor_list_version == 20
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

        decoded.oob_disclosed_vendors = {
            num: num == vendor_id for num in range(1, vendor_id + 1)
        }


class TestBuildTCMobileData:
    @pytest.mark.usefixtures("captify_technologies_system")
    def test_build_accept_all_tc_data_for_mobile_consent_purposes_only(self, db):
        tcf_contents = get_tcf_contents(db)
        model = convert_tcf_contents_to_tc_model(
            tcf_contents, UserConsentPreference.opt_in
        )

        tc_mobile_data = build_tc_data_for_mobile(model)

        assert tc_mobile_data.IABTCF_CmpSdkID == CMP_ID
        assert tc_mobile_data.IABTCF_CmpSdkVersion == 1
        assert tc_mobile_data.IABTCF_PolicyVersion == 4
        assert tc_mobile_data.IABTCF_gdprApplies == 1
        assert tc_mobile_data.IABTCF_PublisherCC == "AA"
        assert tc_mobile_data.IABTCF_PurposeOneTreatment == 0
        assert tc_mobile_data.IABTCF_TCString is not None
        assert tc_mobile_data.IABTCF_UseNonStandardTexts == 0
        assert tc_mobile_data.IABTCF_VendorConsents == "01"
        assert tc_mobile_data.IABTCF_VendorLegitimateInterests == ""
        assert tc_mobile_data.IABTCF_PurposeConsents == "111100101100000000000000"
        assert (
            tc_mobile_data.IABTCF_PurposeLegitimateInterests
            == "000000000000000000000000"
        )
        assert tc_mobile_data.IABTCF_SpecialFeaturesOptIns == "010000000000"

        assert tc_mobile_data.IABTCF_PublisherConsent is None
        assert tc_mobile_data.IABTCF_PublisherLegitimateInterests is None
        assert tc_mobile_data.IABTCF_PublisherCustomPurposesConsents is None
        assert tc_mobile_data.IABTCF_PublisherCustomPurposesLegitimateInterests is None

    @pytest.mark.usefixtures("captify_technologies_system")
    def test_build_reject_all_tc_data_for_mobile_consent_purposes_only(self, db):
        tcf_contents = get_tcf_contents(db)
        model = convert_tcf_contents_to_tc_model(
            tcf_contents, UserConsentPreference.opt_out
        )

        tc_mobile_data = build_tc_data_for_mobile(model)

        assert tc_mobile_data.IABTCF_CmpSdkID == CMP_ID
        assert tc_mobile_data.IABTCF_CmpSdkVersion == 1
        assert tc_mobile_data.IABTCF_PolicyVersion == 4
        assert tc_mobile_data.IABTCF_gdprApplies == 1
        assert tc_mobile_data.IABTCF_PublisherCC == "AA"
        assert tc_mobile_data.IABTCF_PurposeOneTreatment == 0
        assert tc_mobile_data.IABTCF_TCString is not None
        assert tc_mobile_data.IABTCF_UseNonStandardTexts == 0
        assert tc_mobile_data.IABTCF_VendorConsents == ""
        assert tc_mobile_data.IABTCF_VendorLegitimateInterests == ""
        assert tc_mobile_data.IABTCF_PurposeConsents == "000000000000000000000000"
        assert (
            tc_mobile_data.IABTCF_PurposeLegitimateInterests
            == "000000000000000000000000"
        )
        assert tc_mobile_data.IABTCF_SpecialFeaturesOptIns == "000000000000"

        assert tc_mobile_data.IABTCF_PublisherConsent is None
        assert tc_mobile_data.IABTCF_PublisherLegitimateInterests is None
        assert tc_mobile_data.IABTCF_PublisherCustomPurposesConsents is None
        assert tc_mobile_data.IABTCF_PublisherCustomPurposesLegitimateInterests is None

    @pytest.mark.usefixtures("skimbit_system")
    def test_build_accept_all_tc_data_for_mobile_with_legitimate_interest_purposes(
        self, db
    ):
        tcf_contents = get_tcf_contents(db)
        model = convert_tcf_contents_to_tc_model(
            tcf_contents, UserConsentPreference.opt_in
        )

        tc_mobile_data = build_tc_data_for_mobile(model)

        assert tc_mobile_data.IABTCF_CmpSdkID == CMP_ID
        assert tc_mobile_data.IABTCF_CmpSdkVersion == 1
        assert tc_mobile_data.IABTCF_PolicyVersion == 4
        assert tc_mobile_data.IABTCF_gdprApplies == 1
        assert tc_mobile_data.IABTCF_PublisherCC == "AA"
        assert tc_mobile_data.IABTCF_PurposeOneTreatment == 0
        assert tc_mobile_data.IABTCF_TCString is not None
        assert tc_mobile_data.IABTCF_UseNonStandardTexts == 0
        assert tc_mobile_data.IABTCF_VendorConsents == ""
        assert (
            tc_mobile_data.IABTCF_VendorLegitimateInterests
            == "0000000000000000000000000000000000000000000001"
        )
        assert tc_mobile_data.IABTCF_PurposeConsents == "000000000000000000000000"
        assert (
            tc_mobile_data.IABTCF_PurposeLegitimateInterests
            == "000000110100000000000000"
        )
        assert tc_mobile_data.IABTCF_SpecialFeaturesOptIns == "000000000000"

        assert tc_mobile_data.IABTCF_PublisherConsent is None
        assert tc_mobile_data.IABTCF_PublisherLegitimateInterests is None
        assert tc_mobile_data.IABTCF_PublisherCustomPurposesConsents is None
        assert tc_mobile_data.IABTCF_PublisherCustomPurposesLegitimateInterests is None

    @pytest.mark.usefixtures("skimbit_system")
    def test_build_reject_all_tc_data_for_mobile_with_legitimate_interest_purposes(
        self, db
    ):
        tcf_contents = get_tcf_contents(db)
        model = convert_tcf_contents_to_tc_model(
            tcf_contents, UserConsentPreference.opt_out
        )

        tc_mobile_data = build_tc_data_for_mobile(model)

        assert tc_mobile_data.IABTCF_CmpSdkID == CMP_ID
        assert tc_mobile_data.IABTCF_CmpSdkVersion == 1
        assert tc_mobile_data.IABTCF_PolicyVersion == 4
        assert tc_mobile_data.IABTCF_gdprApplies == 1
        assert tc_mobile_data.IABTCF_PublisherCC == "AA"
        assert tc_mobile_data.IABTCF_PurposeOneTreatment == 0
        assert tc_mobile_data.IABTCF_TCString is not None
        assert tc_mobile_data.IABTCF_UseNonStandardTexts == 0
        assert tc_mobile_data.IABTCF_VendorConsents == ""
        assert tc_mobile_data.IABTCF_VendorLegitimateInterests == ""
        assert tc_mobile_data.IABTCF_PurposeConsents == "000000000000000000000000"
        assert (
            tc_mobile_data.IABTCF_PurposeLegitimateInterests
            == "000000000000000000000000"
        )
        assert tc_mobile_data.IABTCF_SpecialFeaturesOptIns == "000000000000"

        assert tc_mobile_data.IABTCF_PublisherConsent is None
        assert tc_mobile_data.IABTCF_PublisherLegitimateInterests is None
        assert tc_mobile_data.IABTCF_PublisherCustomPurposesConsents is None
        assert tc_mobile_data.IABTCF_PublisherCustomPurposesLegitimateInterests is None
