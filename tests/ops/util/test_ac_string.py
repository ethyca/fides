import pytest

from fides.api.common_exceptions import DecodeFidesStringError
from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.schemas.tcf import TCFVendorConsentRecord, TCFVendorSave
from fides.api.util.tcf.ac_string import (
    build_ac_string,
    build_ac_vendor_consents,
    build_fides_string,
    decode_ac_string_to_preferences,
    split_fides_string,
    universal_vendor_id_to_ac_id,
)
from fides.api.util.tcf.tcf_experience_contents import TCFExperienceContents


def test_universal_vendor_id_to_ac_id():
    assert universal_vendor_id_to_ac_id("gacp.42") == 42

    with pytest.raises(ValueError):
        universal_vendor_id_to_ac_id("gvl.100")


def test_build_fides_string():
    tc_string = "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA"
    ac_string = "1~1.35.41.101"

    # TC string but no AC string
    assert (
        build_fides_string(tc_string, None)
        == "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA"
    )

    # Contrived scenario, AC string but no TC string
    assert build_fides_string(None, ac_string) == ",1~1.35.41.101"

    # Both TC String and AC String
    assert (
        build_fides_string(tc_string, ac_string)
        == "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA,1~1.35.41.101"
    )

    # Neither TC String or AC String
    assert build_fides_string(None, None) == ""


def test_split_fides_string():
    tc_str, ac_str = split_fides_string(None)
    assert tc_str is None
    assert ac_str is None

    tc_str, ac_str = split_fides_string(
        "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA"
    )
    assert tc_str == "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA"
    assert ac_str is None

    tc_str, ac_str = split_fides_string(
        "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA,1~100.1000"
    )
    assert tc_str == "CPz1hddPz1hddDxAAAENCZCgADgAAAAAAAAAAEBcABioAAA.YAAAAAAAAAA"
    assert ac_str == "1~100.1000"

    tc_str, ac_str = split_fides_string(",1~100.1000")
    assert tc_str is None
    assert ac_str == "1~100.1000"


class TestBuildACString:
    def test_no_vendor_consents(self):
        contents = TCFExperienceContents()
        ac_vendor_consents = build_ac_vendor_consents(
            contents, UserConsentPreference.opt_in
        )
        assert build_ac_string(ac_vendor_consents) is None

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
        assert build_ac_string(ac_vendor_consents) is None

    def test_only_gvl_vendors(self):
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
        assert build_ac_string(ac_vendor_consents) is None

    def test_one_gacp_id(self):
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

    def test_badly_formatted_vendor_ids(self):
        contents = TCFExperienceContents(
            tcf_vendor_consents=[
                TCFVendorConsentRecord(id="gacp.1313aasd"),
                TCFVendorConsentRecord(id="gvl.asdf"),
            ]
        )
        ac_vendor_consents = build_ac_vendor_consents(
            contents, UserConsentPreference.opt_in
        )
        assert build_ac_string(ac_vendor_consents) is None

    def test_build_ac_string(self):
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
        prefs = decode_ac_string_to_preferences(None, TCFExperienceContents())
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
