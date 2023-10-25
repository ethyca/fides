import pytest

from fides.api.common_exceptions import DecodeFidesStringError
from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.schemas.tcf import TCFVendorConsentRecord, TCFVendorSave
from fides.api.util.tcf.ac_string import (
    build_ac_string,
    build_ac_vendor_consents,
    decode_ac_string_to_preferences,
    universal_vendor_id_to_ac_id,
)
from fides.api.util.tcf.tcf_experience_contents import TCFExperienceContents


def test_universal_vendor_id_to_ac_id():
    assert universal_vendor_id_to_ac_id("gacp.42") == 42

    with pytest.raises(ValueError):
        universal_vendor_id_to_ac_id("gvl.100")

    with pytest.raises(ValueError):
        universal_vendor_id_to_ac_id("gacp.bad_id")

    with pytest.raises(ValueError):
        universal_vendor_id_to_ac_id("gacp.gacp")


class TestBuildACString:
    def test_opt_in_but_no_vendors(self):
        contents = TCFExperienceContents()
        ac_vendor_consents = build_ac_vendor_consents(
            contents, UserConsentPreference.opt_in
        )
        assert build_ac_string(ac_vendor_consents) == "1~"

    def test_opt_out_preference(self):
        contents = TCFExperienceContents(
            tcf_vendor_consents=[
                TCFVendorConsentRecord(id="gacp.1313"),
                TCFVendorConsentRecord(id="gacp.231"),
                TCFVendorConsentRecord(id="gacp.8844"),
            ]
        )
        ac_vendor_consents = build_ac_vendor_consents(
            contents, UserConsentPreference.opt_out
        )
        assert build_ac_string(ac_vendor_consents) == "1~"

    def test_opt_in_only_gvl_vendors(self):
        contents = TCFExperienceContents(
            tcf_vendor_consents=[
                TCFVendorConsentRecord(id="gvl.1313"),
                TCFVendorConsentRecord(id="gvl.231"),
                TCFVendorConsentRecord(id="gvl.8844"),
            ]
        )
        ac_vendor_consents = build_ac_vendor_consents(
            contents, UserConsentPreference.opt_in
        )
        assert build_ac_string(ac_vendor_consents) == "1~"

    def test_opt_in_one_gacp_id(self):
        contents = TCFExperienceContents(
            tcf_vendor_consents=[
                TCFVendorConsentRecord(id="gacp.12"),
                TCFVendorConsentRecord(id="gvl.29"),
            ]
        )
        ac_vendor_consents = build_ac_vendor_consents(
            contents, UserConsentPreference.opt_in
        )
        assert build_ac_string(ac_vendor_consents) == "1~12"

    def test_badly_formatted_vendor_ids_skipped(self):
        contents = TCFExperienceContents(
            tcf_vendor_consents=[
                TCFVendorConsentRecord(id="gacp.1313aasd"),
                TCFVendorConsentRecord(id="gvl.asdf"),
            ]
        )
        ac_vendor_consents = build_ac_vendor_consents(
            contents, UserConsentPreference.opt_in
        )
        assert build_ac_string(ac_vendor_consents) == "1~"

    def test_build_opt_in_ac_string(self):
        contents = TCFExperienceContents(
            tcf_vendor_consents=[
                TCFVendorConsentRecord(id="gacp.1313"),
                TCFVendorConsentRecord(id="gacp.231"),
                TCFVendorConsentRecord(id="gacp.8844"),
            ]
        )
        ac_vendor_consents = build_ac_vendor_consents(
            contents, UserConsentPreference.opt_in
        )
        assert build_ac_string(ac_vendor_consents) == "1~231.1313.8844"


class TestDecodeACStringToPreferences:
    def test_no_ac_str(self):
        prefs = decode_ac_string_to_preferences(
            None,
            TCFExperienceContents(
                tcf_vendor_consents=[TCFVendorConsentRecord(id="gacp.122")]
            ),
        )
        assert prefs.vendor_consent_preferences == []

        prefs = decode_ac_string_to_preferences(
            "",
            TCFExperienceContents(
                tcf_vendor_consents=[TCFVendorConsentRecord(id="gacp.122")]
            ),
        )
        assert prefs.vendor_consent_preferences == []

    def test_bad_ac_str(self):
        with pytest.raises(DecodeFidesStringError):
            decode_ac_string_to_preferences("bad_string", TCFExperienceContents())

    def test_no_systems_in_data_map(self):
        prefs = decode_ac_string_to_preferences("1~100", TCFExperienceContents())
        assert prefs.vendor_consent_preferences == []

    def test_no_ac_systems_in_data_map(self):
        prefs = decode_ac_string_to_preferences(
            "1~100",
            TCFExperienceContents(
                tcf_vendor_consents=[TCFVendorConsentRecord(id="gvl.122")]
            ),
        )
        assert prefs.vendor_consent_preferences == []

    def test_matching_ac_system_in_data_map(self):
        prefs = decode_ac_string_to_preferences(
            "1~100",
            TCFExperienceContents(
                tcf_vendor_consents=[TCFVendorConsentRecord(id="gacp.100")]
            ),
        )
        assert prefs.vendor_consent_preferences == [
            TCFVendorSave(id="gacp.100", preference=UserConsentPreference.opt_in)
        ]

    def test_pass_in_optout_string(self):
        prefs = decode_ac_string_to_preferences(
            "1~",
            TCFExperienceContents(
                tcf_vendor_consents=[TCFVendorConsentRecord(id="gacp.100")]
            ),
        )
        assert prefs.vendor_consent_preferences == [
            TCFVendorSave(id="gacp.100", preference=UserConsentPreference.opt_out)
        ]

    def test_pass_in_optout_string_no_systems_in_datamap(self):
        prefs = decode_ac_string_to_preferences(
            "1~",
            TCFExperienceContents(tcf_vendor_consents=[]),
        )
        assert prefs.vendor_consent_preferences == []

    def test_ac_system_in_data_map_not_in_string_gets_opt_out(self):
        prefs = decode_ac_string_to_preferences(
            "1~100",
            TCFExperienceContents(
                tcf_vendor_consents=[
                    TCFVendorConsentRecord(id="gacp.100"),
                    TCFVendorConsentRecord(id="gacp.250"),
                ]
            ),
        )
        assert prefs.vendor_consent_preferences == [
            TCFVendorSave(id="gacp.100", preference=UserConsentPreference.opt_in),
            TCFVendorSave(id="gacp.250", preference=UserConsentPreference.opt_out),
        ]

    def test_multiple_ac_vendors_in_the_string(self):
        prefs = decode_ac_string_to_preferences(
            "1~100.250.300.400",
            TCFExperienceContents(
                tcf_vendor_consents=[
                    TCFVendorConsentRecord(id="gacp.100"),
                    TCFVendorConsentRecord(id="gacp.250"),
                    TCFVendorConsentRecord(id="gacp.300"),
                    TCFVendorConsentRecord(id="gacp.500"),
                ],
                tcf_vendor_legitimate_interests=[  # No bearing on preferences saved
                    TCFVendorConsentRecord(id="gacp.1000"),
                ],
            ),
        )
        assert prefs.vendor_consent_preferences == [
            TCFVendorSave(id="gacp.100", preference=UserConsentPreference.opt_in),
            TCFVendorSave(id="gacp.250", preference=UserConsentPreference.opt_in),
            TCFVendorSave(id="gacp.300", preference=UserConsentPreference.opt_in),
            TCFVendorSave(id="gacp.500", preference=UserConsentPreference.opt_out),
        ]
