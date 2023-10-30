import uuid
from datetime import datetime
from typing import Optional

import pytest
from iab_tcf import decode_v2
from pydantic import ValidationError

from fides.api.common_exceptions import DecodeFidesStringError
from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.models.sql_models import PrivacyDeclaration, System
from fides.api.schemas.privacy_preference import FidesStringFidesPreferences
from fides.api.util.tcf.experience_meta import (
    TCFVersionHash,
    _build_tcf_version_hash_model,
    build_tcf_version_hash,
)
from fides.api.util.tcf.tc_mobile_data import (
    build_tc_data_for_mobile,
    convert_fides_str_to_mobile_data,
)
from fides.api.util.tcf.tc_model import (
    CMP_ID,
    convert_tcf_contents_to_tc_model,
    universal_vendor_id_to_gvl_id,
)
from fides.api.util.tcf.tc_string import (
    TCModel,
    build_tc_string,
    decode_tc_string_to_preferences,
)
from fides.api.util.tcf.tcf_experience_contents import get_tcf_contents


class TestHashTCFExperience:
    @pytest.mark.usefixtures("tcf_system", "privacy_experience_france_tcf_overlay")
    def test_build_tcf_version_hash_model(self, db):
        tcf_contents = get_tcf_contents(db)
        version_hash_model = _build_tcf_version_hash_model(tcf_contents=tcf_contents)
        assert version_hash_model == TCFVersionHash(
            policy_version=4,
            vendor_purpose_consents=["gvl.42-8"],
            vendor_purpose_legitimate_interests=[],
            gvl_vendors_disclosed=[42],
        )

        version_hash = build_tcf_version_hash(tcf_contents)
        assert version_hash == "dbde7265d5dd"

    def test_version_hash_model_sorting(self):
        """We're just doing string sorting here, we don't need to do natural language
        sorting, as long as it's repeatable"""
        version_hash_model = TCFVersionHash(
            policy_version=4,
            vendor_purpose_consents=[
                "gvl.8-1,4,6,7",
                "gvl.39-1,4,6,7",
                "gvl.5-1,2,3,4",
                "gvl.1",
                "gacp.4" "gacp.10,1",
                "gacp.1",
                "ctl_3c809e3f-96b3-4aec-a0c6-f3904104559b-9",
            ],
            vendor_purpose_legitimate_interests=["gvl.39-1,4,6,7", "gvl.100-1,2"],
            gvl_vendors_disclosed=[100, 39, 5, 8, 1],
        )

        assert version_hash_model.policy_version == 4
        assert version_hash_model.vendor_purpose_consents == [
            "ctl_3c809e3f-96b3-4aec-a0c6-f3904104559b-9",
            "gacp.1",
            "gacp.4gacp.10,1",
            "gvl.1",
            "gvl.39-1,4,6,7",
            "gvl.5-1,2,3,4",
            "gvl.8-1,4,6,7",
        ]
        assert version_hash_model.vendor_purpose_legitimate_interests == [
            "gvl.100-1,2",
            "gvl.39-1,4,6,7",
        ]
        assert version_hash_model.gvl_vendors_disclosed == [1, 5, 8, 39, 100]

    @pytest.mark.usefixtures(
        "skimbit_system",
        "emerse_system",
        "captify_technologies_system",
        "ac_system_without_privacy_declaration",
        "ac_system_with_privacy_declaration",
        "enable_ac",
    )
    def test_vendor_hash_model_contents(self, db, system):
        """Test building hash model with a mixture of GVL, AC, and regular Systems without a vendor"""
        decl = system.privacy_declarations[0]
        decl.legal_basis_for_processing = "Legitimate interests"
        decl.data_use = "marketing.advertising.first_party.targeted"
        decl.save(db)

        tcf_contents = get_tcf_contents(db)
        version_hash_model = _build_tcf_version_hash_model(tcf_contents=tcf_contents)

        assert version_hash_model.policy_version == 4
        assert version_hash_model.vendor_purpose_consents == [
            "gacp.100",
            "gacp.8-1",
            "gvl.2-1,2,3,4,7,9,10",
            "gvl.8-1,3,4",
        ]
        assert version_hash_model.vendor_purpose_legitimate_interests == [
            system.id + "-4",
            "gvl.46-7,8,10",
            "gvl.8-2,7,8,9",
        ]
        assert version_hash_model.gvl_vendors_disclosed == [2, 8, 46]

    @pytest.mark.usefixtures("captify_technologies_system")
    def test_build_tcf_version_hash_removing_declaration(
        self, db, captify_technologies_system
    ):
        tcf_contents = get_tcf_contents(db)
        version_hash_model = _build_tcf_version_hash_model(tcf_contents=tcf_contents)
        assert version_hash_model == TCFVersionHash(
            policy_version=4,
            vendor_purpose_consents=["gvl.2-1,2,3,4,7,9,10"],
            vendor_purpose_legitimate_interests=[],
            gvl_vendors_disclosed=[2],
        )

        version_hash = build_tcf_version_hash(tcf_contents)
        assert version_hash == "0429105be515"

        # Remove the privacy declaration corresponding to purpose 1
        for decl in captify_technologies_system.privacy_declarations:
            if decl.data_use == "functional.storage":
                decl.delete(db)

        # Recalculate version hash model and version
        tcf_contents = get_tcf_contents(db)
        version_hash_model = _build_tcf_version_hash_model(tcf_contents=tcf_contents)
        assert version_hash_model == TCFVersionHash(
            policy_version=4,
            vendor_purpose_consents=["gvl.2-2,3,4,7,9,10"],
            vendor_purpose_legitimate_interests=[],
            gvl_vendors_disclosed=[2],
        )

        version_hash = build_tcf_version_hash(tcf_contents)
        assert version_hash == "f2e19b4b3eae"

    def test_build_tcf_version_hash_adding_vendor(self, db, system):
        system.vendor_id = "gvl.88"
        system.save(db)

        tcf_contents = get_tcf_contents(db)
        version_hash_model = _build_tcf_version_hash_model(tcf_contents=tcf_contents)
        assert version_hash_model == TCFVersionHash(
            policy_version=4,
            vendor_purpose_consents=[],
            vendor_purpose_legitimate_interests=[],
            gvl_vendors_disclosed=[],
        )

        version_hash = build_tcf_version_hash(tcf_contents)
        assert version_hash == "6b2062179826"

        # Add declaration to system with TCF purpose, so now system shows up
        decl = system.privacy_declarations[0]
        decl.legal_basis_for_processing = "Legitimate interests"
        decl.data_use = "marketing.advertising.first_party.targeted"
        decl.save(db)

        # Recalculate version hash model and version
        tcf_contents = get_tcf_contents(db)
        version_hash_model = _build_tcf_version_hash_model(tcf_contents=tcf_contents)
        assert version_hash_model == TCFVersionHash(
            policy_version=4,
            vendor_purpose_consents=[],
            vendor_purpose_legitimate_interests=[f"gvl.88-4"],
            gvl_vendors_disclosed=[],
        )

        version_hash = build_tcf_version_hash(tcf_contents)
        assert version_hash == "c5a4e3b672e3"

    def test_build_tcf_version_hash_adding_purpose(self, db, emerse_system):
        tcf_contents = get_tcf_contents(db)
        version_hash_model = _build_tcf_version_hash_model(tcf_contents=tcf_contents)
        assert version_hash_model == TCFVersionHash(
            policy_version=4,
            vendor_purpose_consents=["gvl.8-1,3,4"],
            vendor_purpose_legitimate_interests=["gvl.8-2,7,8,9"],
            gvl_vendors_disclosed=[8],
        )

        version_hash = build_tcf_version_hash(tcf_contents)
        assert version_hash == "3a655ef13ee6"

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
            vendor_purpose_consents=["gvl.8-1,3,4,10"],
            vendor_purpose_legitimate_interests=["gvl.8-2,7,8,9"],
            gvl_vendors_disclosed=[8],
        )

        version_hash = build_tcf_version_hash(tcf_contents)
        assert version_hash == "c290c3d76a26"

    def test_build_tcf_version_hash_updating_legal_basis(self, db, system):
        system.vendor_id = "gvl.88"
        system.save(db)

        # Add declaration to system with TCF purpose, so now system shows up
        decl = system.privacy_declarations[0]
        decl.legal_basis_for_processing = "Legitimate interests"
        decl.data_use = "marketing.advertising.first_party.targeted"
        decl.save(db)

        tcf_contents = get_tcf_contents(db)
        version_hash_model = _build_tcf_version_hash_model(tcf_contents=tcf_contents)
        assert version_hash_model == TCFVersionHash(
            policy_version=4,
            vendor_purpose_consents=[],
            vendor_purpose_legitimate_interests=[f"gvl.88-4"],
            gvl_vendors_disclosed=[],
        )

        version_hash = build_tcf_version_hash(tcf_contents)
        assert version_hash == "c5a4e3b672e3"

        # Update legal basis
        decl.legal_basis_for_processing = "Consent"
        decl.save(db)

        # Recalculate version hash model and version
        tcf_contents = get_tcf_contents(db)
        version_hash_model = _build_tcf_version_hash_model(tcf_contents=tcf_contents)
        assert version_hash_model == TCFVersionHash(
            policy_version=4,
            vendor_purpose_consents=[f"gvl.88-4"],
            vendor_purpose_legitimate_interests=[],
            gvl_vendors_disclosed=[],
        )

        version_hash = build_tcf_version_hash(tcf_contents)
        assert version_hash == "a279467aec23"


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

        assert model.cmp_id == 407
        assert model.vendor_list_version == 24
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
        assert decoded.cmp_id == 407
        assert decoded.cmp_version == 1
        assert decoded.consent_screen == 1
        assert decoded.consent_language == b"EN"
        assert decoded.vendor_list_version == 24
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

        assert decoded.oob_disclosed_vendors == {1: False, 2: True}

    @pytest.mark.usefixtures("emerse_system")
    def test_build_tc_string_emerse_accept_all(self, db):
        tcf_contents = get_tcf_contents(db)
        model = convert_tcf_contents_to_tc_model(
            tcf_contents, UserConsentPreference.opt_in
        )

        assert model.cmp_id == 407
        assert model.vendor_list_version == 24
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
        assert decoded.cmp_id == 407
        assert decoded.cmp_version == 1
        assert decoded.consent_screen == 1
        assert decoded.consent_language == b"EN"
        assert decoded.vendor_list_version == 24
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

        assert model.cmp_id == 407
        assert model.vendor_list_version == 24
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
        assert decoded.cmp_id == 407
        assert decoded.cmp_version == 1
        assert decoded.consent_screen == 1
        assert decoded.consent_language == b"EN"
        assert decoded.vendor_list_version == 24
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

        assert model.cmp_id == 407
        assert model.vendor_list_version == 24
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
        assert decoded.cmp_id == 407
        assert decoded.cmp_version == 1
        assert decoded.consent_screen == 1
        assert decoded.consent_language == b"EN"
        assert decoded.vendor_list_version == 24
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

        assert model.cmp_id == 407
        assert model.vendor_list_version == 24
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
        assert decoded.cmp_id == 407
        assert decoded.cmp_version == 1
        assert decoded.consent_screen == 1
        assert decoded.consent_language == b"EN"
        assert decoded.vendor_list_version == 24
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

        assert model.cmp_id == 407
        assert model.vendor_list_version == 24
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
        assert decoded.cmp_id == 407
        assert decoded.cmp_version == 1
        assert decoded.consent_screen == 1
        assert decoded.consent_language == b"EN"
        assert decoded.vendor_list_version == 24
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

    @pytest.mark.usefixtures("captify_technologies_system")
    def test_build_tc_string_captify_accept_all(self, db):
        tcf_contents = get_tcf_contents(db)
        model = convert_tcf_contents_to_tc_model(
            tcf_contents, UserConsentPreference.opt_in
        )

        assert model.cmp_id == 407
        assert model.vendor_list_version == 24
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
        assert decoded.cmp_id == 407
        assert decoded.cmp_version == 1
        assert decoded.consent_screen == 1
        assert decoded.consent_language == b"EN"
        assert decoded.vendor_list_version == 24
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

        assert decoded.oob_disclosed_vendors == {1: False, 2: True}

    @pytest.mark.usefixtures("ac_system_with_privacy_declaration", "enable_ac")
    def test_ac_system_not_in_tc_string(self, db):
        """System with AC vendor id will not show up in the vendor consents section of the TC string, but its purpose
        with legal basis of consent does show up in purpose consents (this is the same thing we do if we
        have a system that is not in the GVL too)"""
        tcf_contents = get_tcf_contents(db)
        model = convert_tcf_contents_to_tc_model(
            tcf_contents, UserConsentPreference.opt_in
        )

        assert model.cmp_id == 407
        assert model.vendor_list_version == 24
        assert model.policy_version == 4
        assert model.cmp_version == 1
        assert model.consent_screen == 1

        assert model.vendor_consents == []
        assert model.vendor_legitimate_interests == []
        assert model.purpose_consents == [1]
        assert model.purpose_legitimate_interests == []
        assert model.special_feature_optins == []

        tc_str = build_tc_string(model)
        decoded = decode_v2(tc_str)

        assert decoded.version == 2
        assert datetime.utcnow().date() == decoded.created.date()
        assert decoded.cmp_id == 407
        assert decoded.cmp_version == 1
        assert decoded.consent_screen == 1
        assert decoded.consent_language == b"EN"
        assert decoded.vendor_list_version == 24
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

        assert decoded.oob_disclosed_vendors == {}


class TestBuildTCMobileData:
    @pytest.mark.usefixtures("captify_technologies_system", "enable_ac")
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
        assert tc_mobile_data.IABTCF_AddtlConsent == "1~"

    @pytest.mark.usefixtures("captify_technologies_system", "enable_ac")
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
        assert tc_mobile_data.IABTCF_AddtlConsent == "1~"

    @pytest.mark.usefixtures("skimbit_system", "enable_ac")
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
        assert tc_mobile_data.IABTCF_AddtlConsent == "1~"

    @pytest.mark.usefixtures("skimbit_system", "enable_ac")
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
        assert tc_mobile_data.IABTCF_AddtlConsent == "1~"

    @pytest.mark.usefixtures("ac_system_without_privacy_declaration", "enable_ac")
    def test_build_opt_in_tc_data_for_mobile_with_ac_system(self, db):
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
        assert tc_mobile_data.IABTCF_AddtlConsent == "1~100"

    @pytest.mark.usefixtures("ac_system_without_privacy_declaration")
    def test_build_opt_in_tc_data_for_mobile_with_ac_system_but_ac_disabled(self, db):
        tcf_contents = get_tcf_contents(db)
        model = convert_tcf_contents_to_tc_model(
            tcf_contents, UserConsentPreference.opt_in
        )

        tc_mobile_data = build_tc_data_for_mobile(model)

        assert tc_mobile_data.IABTCF_CmpSdkID == CMP_ID
        assert tc_mobile_data.IABTCF_CmpSdkVersion == 1
        assert tc_mobile_data.IABTCF_PolicyVersion == 4
        assert tc_mobile_data.IABTCF_AddtlConsent is None

    @pytest.mark.usefixtures("ac_system_without_privacy_declaration", "enable_ac")
    def test_build_opt_out_tc_data_for_mobile_with_ac_system(self, db):
        tcf_contents = get_tcf_contents(db)
        model = convert_tcf_contents_to_tc_model(
            tcf_contents, UserConsentPreference.opt_out
        )

        tc_mobile_data = build_tc_data_for_mobile(model)

        assert tc_mobile_data.IABTCF_VendorConsents == ""
        assert tc_mobile_data.IABTCF_VendorLegitimateInterests == ""
        assert tc_mobile_data.IABTCF_PurposeConsents == "000000000000000000000000"
        assert (
            tc_mobile_data.IABTCF_PurposeLegitimateInterests
            == "000000000000000000000000"
        )
        assert tc_mobile_data.IABTCF_SpecialFeaturesOptIns == "000000000000"
        assert tc_mobile_data.IABTCF_AddtlConsent == "1~"


class TestDecodeTcString:
    @pytest.mark.usefixtures(
        "skimbit_system", "emerse_system", "captify_technologies_system"
    )
    def test_decode_tc_string_to_preferences(self, db):
        tc_str = "CPzEX8APzEX8AAMABBENAUEEAPLAAAAAAAAAABEAAAAA.IABE"
        # Sections opted in via the string
        # expected_purpose_consent_optins = [1, 2, 3, 4, 7, 9, 10]
        # expected_purpose_li_optins = []
        expected_vendor_consent_optins = [2]
        # expected_vendor_li_optins = []
        # expected_special_feature_optins = [2]

        # All possible options that can be disclosed to the user from the datamap
        datamap_purpose_consent = [1, 2, 3, 4, 7, 9, 10]
        datamap_purpose_legitimate_interests = [2, 7, 8, 9, 10]
        datamap_vendor_consents = [2, 8]
        datamap_vendor_legitimate_interests = [8, 46]
        datamap_special_feature_optins = [2]

        tcf_contents = get_tcf_contents(db)
        fides_tcf_preferences = decode_tc_string_to_preferences(tc_str, tcf_contents)
        assert isinstance(fides_tcf_preferences, FidesStringFidesPreferences)

        assert len(fides_tcf_preferences.purpose_consent_preferences) == len(
            datamap_purpose_consent
        )
        for pref in fides_tcf_preferences.purpose_consent_preferences:
            # User opted in to every purpose consent that was disclosed
            assert pref.preference == UserConsentPreference.opt_in
            assert pref.id in datamap_purpose_consent

        assert len(
            fides_tcf_preferences.purpose_legitimate_interests_preferences
        ) == len(datamap_purpose_legitimate_interests)
        for pref in fides_tcf_preferences.purpose_legitimate_interests_preferences:
            # User opted out of every purpose legitimate interest that was disclosed: 2, 7, 8, 9, 10
            assert pref.preference == UserConsentPreference.opt_out
            assert pref.id in datamap_purpose_legitimate_interests

        assert len(fides_tcf_preferences.vendor_consent_preferences) == len(
            datamap_vendor_consents
        )
        for pref in fides_tcf_preferences.vendor_consent_preferences:
            # User opted into vendor consent 2 but not vendor consent 8
            assert (
                pref.preference == UserConsentPreference.opt_in
                if pref.id in expected_vendor_consent_optins
                else UserConsentPreference.opt_out
            )
            assert isinstance(pref.id, str)
            assert pref.id.startswith("gvl.")
            assert universal_vendor_id_to_gvl_id(pref.id) in datamap_vendor_consents

        assert len(
            fides_tcf_preferences.vendor_legitimate_interests_preferences
        ) == len(datamap_vendor_legitimate_interests)
        for pref in fides_tcf_preferences.vendor_legitimate_interests_preferences:
            # User opted out of every vendor legitimate interests preference 8 and 46
            assert pref.preference == UserConsentPreference.opt_out
            assert isinstance(pref.id, str)
            assert pref.id.startswith("gvl.")
            assert (
                universal_vendor_id_to_gvl_id(pref.id)
                in datamap_vendor_legitimate_interests
            )

        assert (
            len(fides_tcf_preferences.special_feature_preferences)
            == len(datamap_special_feature_optins)
            == 1
        )
        # User opted into the only special feature - 2
        assert (
            fides_tcf_preferences.special_feature_preferences[0].preference
            == UserConsentPreference.opt_in
        )
        assert fides_tcf_preferences.special_feature_preferences[0].id == 2


class TestConvertTCStringtoMobile:
    def test_expected_response(self):
        """
        Test expected response

        Purpose consents are 1, 2, 3, 4, 7, 9, 10
        Purpose legitimate interests are 2, 7, 8, 9, 10
        Vendor consents are 2, 8
        Vendor legitimate interests are 8, 46
        Special feature opt ins are 2
        """
        tc_str = "CPytTYAPytTYAAMABBENATEEAPLAAEPAAAAAAEEEALgCAAAAAAgAAAAA.IAXEEAAAAABA"
        tc_mobile_data = convert_fides_str_to_mobile_data(tc_str).dict()

        assert tc_mobile_data["IABTCF_CmpSdkID"] == 12
        assert tc_mobile_data["IABTCF_CmpSdkVersion"] == 1
        assert tc_mobile_data["IABTCF_PolicyVersion"] == 4
        assert tc_mobile_data["IABTCF_gdprApplies"] == 1
        assert tc_mobile_data["IABTCF_PublisherCC"] == "AA"
        assert tc_mobile_data["IABTCF_PurposeOneTreatment"] == 0
        assert tc_mobile_data["IABTCF_UseNonStandardTexts"] == 0
        assert tc_mobile_data["IABTCF_TCString"] == tc_str
        # Purpose consents: 1, 2, 3, 4, 7, 9, 10
        assert tc_mobile_data["IABTCF_PurposeConsents"] == "111100101100000000000000"
        # Purpose legitimate interests: 2, 7, 8, 9, 10
        assert (
            tc_mobile_data["IABTCF_PurposeLegitimateInterests"]
            == "010000111100000000000000"
        )
        # Vendor consents: 2, 8
        assert tc_mobile_data["IABTCF_VendorConsents"] == "01000001"
        # Vendor legitimate interests: 8, 46
        assert (
            tc_mobile_data["IABTCF_VendorLegitimateInterests"]
            == "0000000100000000000000000000000000000000000001"
        )
        #  Special feature opt ins: 2
        assert tc_mobile_data["IABTCF_SpecialFeaturesOptIns"] == "010000000000"

    def test_another_tc_string(self):
        """
        Test expected response with another contrived TC string

        Purpose consents are 1, 4, 6, 10
        Purpose legitimate interests are 2, 3, 4
        Vendor consents are 1, 6, 10, 11
        Vendor legitimate interests are 1, 2, 4, 8
        Special feature opt ins are 1
        """
        tc_str = "CPy2kiHPy2kiHfQADLENCZCYAJRAAHAAAAKwAFoRgAQ0QAA.II7Nd_X__bX9n-_7_6ft0eY1f9_r37uQzDhfNs-8F3L_W_LwX32E7NF36tq4KmR4ku1bBIQNtHMnUDUmxaolVrzHsak2cpyNKJ_JkknsZe2dYGF9Pn9lD-YKZ7_5_9_f52T_9_9_-39z3_9f___dv_-__-vjf_599n_v9fV_78_Kf9______-____________8A"
        tc_mobile_data = convert_fides_str_to_mobile_data(tc_str).dict()

        assert tc_mobile_data["IABTCF_CmpSdkID"] == 2000
        assert tc_mobile_data["IABTCF_CmpSdkVersion"] == 3
        assert tc_mobile_data["IABTCF_PolicyVersion"] == 2
        assert tc_mobile_data["IABTCF_gdprApplies"] == 1
        assert tc_mobile_data["IABTCF_PublisherCC"] == "BW"
        assert tc_mobile_data["IABTCF_PurposeOneTreatment"] == 0
        assert tc_mobile_data["IABTCF_UseNonStandardTexts"] == 1
        assert tc_mobile_data["IABTCF_TCString"] == tc_str
        assert tc_mobile_data["IABTCF_PurposeConsents"] == "100101000100000000000000"
        assert (
            tc_mobile_data["IABTCF_PurposeLegitimateInterests"]
            == "011100000000000000000000"
        )
        assert tc_mobile_data["IABTCF_VendorConsents"] == "10000100011"
        assert tc_mobile_data["IABTCF_VendorLegitimateInterests"] == "11010001"
        #  Special feature opt ins: 2
        assert tc_mobile_data["IABTCF_SpecialFeaturesOptIns"] == "100000000000"

    def test_reject_all_string(self):
        """
        Test reject all response
        """
        tc_str = "CPy2UQ3Py2UQ3AYAAAENCZCQAAAAAAAAAIAAAAAAAAAA.II7Nd_X__bX9n-_7_6ft0eY1f9_r37uQzDhfNs-8F3L_W_LwX32E7NF36tq4KmR4ku1bBIQNtHMnUDUmxaolVrzHsak2cpyNKJ_JkknsZe2dYGF9Pn9lD-YKZ7_5_9_f52T_9_9_-39z3_9f___dv_-__-vjf_599n_v9fV_78_Kf9______-____________8A"
        tc_mobile_data = convert_fides_str_to_mobile_data(tc_str).dict()

        assert tc_mobile_data["IABTCF_CmpSdkID"] == 24
        assert tc_mobile_data["IABTCF_CmpSdkVersion"] == 0
        assert tc_mobile_data["IABTCF_PolicyVersion"] == 2
        assert tc_mobile_data["IABTCF_gdprApplies"] == 1
        assert tc_mobile_data["IABTCF_PublisherCC"] == "AA"
        assert tc_mobile_data["IABTCF_PurposeOneTreatment"] == 1
        assert tc_mobile_data["IABTCF_UseNonStandardTexts"] == 1
        assert tc_mobile_data["IABTCF_TCString"] == tc_str
        assert tc_mobile_data["IABTCF_PurposeConsents"] == "000000000000000000000000"
        assert (
            tc_mobile_data["IABTCF_PurposeLegitimateInterests"]
            == "000000000000000000000000"
        )
        assert tc_mobile_data["IABTCF_VendorConsents"] == ""
        assert tc_mobile_data["IABTCF_VendorLegitimateInterests"] == ""
        assert tc_mobile_data["IABTCF_SpecialFeaturesOptIns"] == "000000000000"

    def test_bad_tc_str(self):
        """
        Test response for an invalid string
        """

        tc_str = "bad_core.bad_vendor"
        with pytest.raises(DecodeFidesStringError):
            convert_fides_str_to_mobile_data(tc_str)

        ac_str_only = ",1~1.100"
        with pytest.raises(DecodeFidesStringError):
            convert_fides_str_to_mobile_data(ac_str_only)

    def test_invalid_base64_encoded_str(self):
        """
        Test response for an invalid string
        """

        tc_str = "a"
        with pytest.raises(DecodeFidesStringError):
            convert_fides_str_to_mobile_data(tc_str)

    def test_string_with_incorrect_bits_for_field(self):
        """String was encoded with version bits as one longer than it should have been,
        which throws everything else off

        This implementation assumes each field was constructed following the number of bits in the spec
        """
        tc_str = "BH5Z8oAH5Z8oAAGAGAiGgDBAAEgAAAAAAAAAAAAAAAAA"

        tc_mobile_data = convert_fides_str_to_mobile_data(tc_str).dict()

        assert tc_mobile_data["IABTCF_CmpSdkID"] == 6  # Was supposed to be 12
        assert tc_mobile_data["IABTCF_CmpSdkVersion"] == 6  # Was supposed to be 12
        assert tc_mobile_data["IABTCF_PolicyVersion"] == 1  # Was supposed to be 2
        assert tc_mobile_data["IABTCF_gdprApplies"] == 1
        assert tc_mobile_data["IABTCF_PublisherCC"] == "AA"
        assert tc_mobile_data["IABTCF_PurposeOneTreatment"] == 0
        assert tc_mobile_data["IABTCF_UseNonStandardTexts"] == 0
        assert tc_mobile_data["IABTCF_TCString"] == tc_str
        assert (
            tc_mobile_data["IABTCF_PurposeConsents"] == "010010000000000000000000"
        )  # Supposed to be 1 and 4
        assert (
            tc_mobile_data["IABTCF_PurposeLegitimateInterests"]
            == "000000000000000000000000"
        )
        assert tc_mobile_data["IABTCF_VendorConsents"] == ""
        assert tc_mobile_data["IABTCF_VendorLegitimateInterests"] == ""
        assert tc_mobile_data["IABTCF_SpecialFeaturesOptIns"] == "000000000000"

    def test_ac_str_but_no_tc_str_string_format(self):
        fides_str = ",~12.35.1452.3313"

        with pytest.raises(DecodeFidesStringError):
            convert_fides_str_to_mobile_data(fides_str)

    def test_bad_ac_string_format(self):
        fides_str = "CPz4f8wPz4f8wKEAAAENCZCsAAwAACIAAAAAAFNdAAoAIAA.YAAAAAAAAAA,~12.35.1452.3313"

        with pytest.raises(DecodeFidesStringError):
            convert_fides_str_to_mobile_data(fides_str)

    def test_tc_string_and_ac_string(self):
        """Assert selected items off of the TC string, but primarily that the AC string is added to IABTCF_AddtlConsent"""
        fides_str = "CPz4f8wPz4f8wKEAAAENCZCsAAwAACIAAAAAAFNdAAoAIAA.YAAAAAAAAAA,1~12.35.1452.3313"

        tc_mobile_data = convert_fides_str_to_mobile_data(fides_str).dict()

        assert tc_mobile_data["IABTCF_CmpSdkID"] == 644
        assert tc_mobile_data["IABTCF_CmpSdkVersion"] == 0
        assert tc_mobile_data["IABTCF_PolicyVersion"] == 2

        assert tc_mobile_data["IABTCF_AddtlConsent"] == "1~12.35.1452.3313"

    def test_null_fides_string(self):
        assert convert_fides_str_to_mobile_data("") is None

        assert convert_fides_str_to_mobile_data(None) is None
