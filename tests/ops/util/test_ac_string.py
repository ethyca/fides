import pytest

from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.schemas.tcf import TCFVendorConsentRecord
from fides.api.util.tcf.ac_string import (
    build_ac_string,
    build_fides_string,
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


class TestBuildACString:
    def test_no_vendor_consents(self):
        contents = TCFExperienceContents()
        assert build_ac_string(contents, UserConsentPreference.opt_in) is None

    def test_opt_out_preference(self):
        contents = TCFExperienceContents(
            tcf_vendor_consents=[
                TCFVendorConsentRecord(id="gacp.1313"),
                TCFVendorConsentRecord(id="gacp.231"),
                TCFVendorConsentRecord(id="gacp.8844"),
            ]
        )
        assert build_ac_string(contents, UserConsentPreference.opt_out) is None

    def test_only_gvl_vendors(self):
        contents = TCFExperienceContents(
            tcf_vendor_consents=[
                TCFVendorConsentRecord(id="gvl.1313"),
                TCFVendorConsentRecord(id="gvl.231"),
                TCFVendorConsentRecord(id="gvl.8844"),
            ]
        )

        assert build_ac_string(contents, UserConsentPreference.opt_in) is None

    def test_one_gacp_id(self):
        contents = TCFExperienceContents(
            tcf_vendor_consents=[
                TCFVendorConsentRecord(id="gacp.12"),
                TCFVendorConsentRecord(id="gvl.29"),
            ]
        )
        assert build_ac_string(contents, UserConsentPreference.opt_in) == "1~12"

    def test_badly_formatted_vendor_ids(self):
        contents = TCFExperienceContents(
            tcf_vendor_consents=[
                TCFVendorConsentRecord(id="gacp.1313aasd"),
                TCFVendorConsentRecord(id="gvl.asdf"),
            ]
        )
        assert build_ac_string(contents, UserConsentPreference.opt_in) is None

    def test_build_ac_string(self):
        contents = TCFExperienceContents(
            tcf_vendor_consents=[
                TCFVendorConsentRecord(id="gacp.1313"),
                TCFVendorConsentRecord(id="gacp.231"),
                TCFVendorConsentRecord(id="gacp.8844"),
            ]
        )
        assert (
            build_ac_string(contents, UserConsentPreference.opt_in) == "1~231.1313.8844"
        )
