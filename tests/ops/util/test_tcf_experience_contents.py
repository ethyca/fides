from uuid import uuid4

import pytest
from fideslang import MAPPED_PURPOSES
from fideslang.models import LegalBasisForProcessingEnum

from fides.api.models.sql_models import PrivacyDeclaration, System
from fides.api.schemas.tcf import EmbeddedVendor
from fides.api.util.tcf.tcf_experience_contents import get_tcf_contents


def assert_length_of_tcf_sections(
    tcf_contents,
    p_c_len: int,
    p_li_len: int,
    f_len: int,
    sp_len: int,
    sf_len: int,
    v_c_len: int,
    v_li_len: int,
    v_r_len: int,
    s_c_len: int,
    s_li_len: int,
    s_r_len: int,
):
    assert len(tcf_contents.tcf_purpose_consents) == p_c_len
    assert len(tcf_contents.tcf_purpose_legitimate_interests) == p_li_len

    assert len(tcf_contents.tcf_features) == f_len
    assert len(tcf_contents.tcf_special_purposes) == sp_len
    assert len(tcf_contents.tcf_special_features) == sf_len

    assert len(tcf_contents.tcf_vendor_consents) == v_c_len
    assert len(tcf_contents.tcf_vendor_legitimate_interests) == v_li_len
    assert len(tcf_contents.tcf_vendor_relationships) == v_r_len

    assert len(tcf_contents.tcf_system_consents) == s_c_len
    assert len(tcf_contents.tcf_system_legitimate_interests) == s_li_len
    assert len(tcf_contents.tcf_system_relationships) == s_r_len


class TestTCFContents:
    def test_load_tcf_data_uses_no_applicable_systems(self, db):
        tcf_contents = get_tcf_contents(db)
        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=0,
            p_li_len=0,
            f_len=0,
            sp_len=0,
            sf_len=0,
            v_c_len=0,
            v_li_len=0,
            v_r_len=0,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

    @pytest.mark.usefixtures("system")
    def test_load_tcf_data_uses_systems_but_no_overlapping_data_use(self, db):
        tcf_contents = get_tcf_contents(db)
        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=0,
            p_li_len=0,
            f_len=0,
            sp_len=0,
            sf_len=0,
            v_c_len=0,
            v_li_len=0,
            v_r_len=0,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

    def test_system_has_appropriate_data_use_but_missing_legal_bases(self, db, system):
        """Test system has relevant data use but legal basis is not Consent or Legitimate Interests."""
        decl = system.privacy_declarations[0]
        decl.data_use = "analytics.reporting.content_performance"
        decl.legal_basis_for_processing = "Vital interests"
        decl.save(db)
        db.refresh(decl)

        tcf_contents = get_tcf_contents(db)
        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=0,
            p_li_len=0,
            f_len=0,
            sp_len=0,
            sf_len=0,
            v_c_len=0,
            v_li_len=0,
            v_r_len=0,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

    def test_system_has_legal_basis_but_not_a_gvl_data_use(self, db, system):
        """Test system has Consent legal basis but data use is not in the GVL."""
        decl = system.privacy_declarations[0]
        decl.data_use = "analytics"
        decl.legal_basis_for_processing = "Consent"
        decl.save(db)
        db.refresh(decl)

        tcf_contents = get_tcf_contents(db)
        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=0,
            p_li_len=0,
            f_len=0,
            sp_len=0,
            sf_len=0,
            v_c_len=0,
            v_li_len=0,
            v_r_len=0,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

    def test_feature_that_is_not_in_the_gvl(self, db, system):
        """Test system has relevant data use and legal basis, but feature is not in the gvl"""
        decl = system.privacy_declarations[0]
        decl.data_use = "analytics.reporting.content_performance"
        decl.legal_basis_for_processing = "Consent"
        decl.features = ["non_gvl_feature"]
        decl.save(db)

        db.refresh(decl)
        assert decl.features == ["non_gvl_feature"]

        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=1,
            p_li_len=0,
            f_len=0,
            sp_len=0,
            sf_len=0,
            v_c_len=0,
            v_li_len=0,
            v_r_len=0,
            s_c_len=1,
            s_li_len=0,
            s_r_len=1,
        )

    def test_system_has_feature_on_different_declaration_than_relevant_use(
        self, tcf_system, db
    ):
        """Assert that a feature has to be paired up with a relevant GVL use to show up. If it's on the system,
        but on a different declaration, it is excluded
        """
        PrivacyDeclaration.create(
            db=db,
            data={
                "name": "Store and access info on a device",
                "system_id": tcf_system.id,
                "data_categories": ["user"],
                "data_use": "analytics",
                "features": [
                    "Receive and use automatically-sent device characteristics for identification"
                ],
                "data_qualifier": "aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
                "data_subjects": ["customer"],
                "dataset_references": None,
                "legal_basis_for_processing": "Consent",
                "egress": None,
                "ingress": None,
            },
        )

        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=1,
            p_li_len=0,
            f_len=0,
            sp_len=1,
            sf_len=0,
            v_c_len=1,
            v_li_len=0,
            v_r_len=1,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

    def test_system_has_declaration_no_features_special_features_special_purposes(
        self, tcf_system, db
    ):
        """Assert that a VendorRelationship record is created even if no features, special features or special purposes are present.
        VendorRelationship is still used to store basic Vendor attributes.
        """
        decl = tcf_system.privacy_declarations[0]
        decl.features = []
        decl.save(db)

        decl_2 = tcf_system.privacy_declarations[1]
        decl_2.delete(db)

        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=1,
            p_li_len=0,
            f_len=0,
            sp_len=0,
            sf_len=0,
            v_c_len=1,
            v_li_len=0,
            v_r_len=1,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

        vendor_relationship = tcf_contents.tcf_vendor_relationships[0]
        assert vendor_relationship.features == []
        assert vendor_relationship.special_purposes == []
        assert vendor_relationship.special_features == []
        assert vendor_relationship.id == "gvl.42"
        assert vendor_relationship.cookie_max_age_seconds is None
        assert vendor_relationship.uses_cookies is False
        assert vendor_relationship.uses_non_cookie_access is False
        assert vendor_relationship.cookie_refresh is False
        assert vendor_relationship.legitimate_interest_disclosure_url is None
        assert vendor_relationship.privacy_policy_url is None

    @pytest.mark.usefixtures("tcf_system")
    def test_system_exists_with_tcf_purpose_and_vendor(self, db):
        """System has vendor id so we return preferences against a "vendor" instead of the system"""
        tcf_contents = get_tcf_contents(db)
        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=1,
            p_li_len=0,
            f_len=0,
            sp_len=1,
            sf_len=0,
            v_c_len=1,
            v_li_len=0,
            v_r_len=1,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

        assert tcf_contents.tcf_purpose_consents[0].id == 8
        assert tcf_contents.tcf_purpose_consents[0].data_uses == [
            "analytics.reporting.content_performance"
        ]
        assert tcf_contents.tcf_purpose_consents[0].vendors == [
            EmbeddedVendor(id="gvl.42", name="TCF System Test")
        ]

        assert tcf_contents.tcf_vendor_consents[0].id == "gvl.42"
        assert tcf_contents.tcf_vendor_consents[0].name == "TCF System Test"
        assert (
            tcf_contents.tcf_vendor_consents[0].description
            == "My TCF System Description"
        )

        # assert some additional TCF attributes are NOT set on the consents object - only on VendorRelationships
        assert not hasattr(
            tcf_contents.tcf_vendor_consents[0], "cookie_max_age_seconds"
        )
        assert not hasattr(tcf_contents.tcf_vendor_consents[0], "uses_cookies")
        assert not hasattr(
            tcf_contents.tcf_vendor_consents[0], "legitimate_interest_disclosure_url"
        )
        assert not hasattr(tcf_contents.tcf_vendor_consents[0], "privacy_policy_url")

        assert len(tcf_contents.tcf_vendor_consents[0].purpose_consents) == 1
        assert tcf_contents.tcf_vendor_consents[0].purpose_consents[0].id == 8

        assert tcf_contents.tcf_vendor_relationships[0].id == "gvl.42"
        assert tcf_contents.tcf_vendor_relationships[0].name == "TCF System Test"
        assert (
            tcf_contents.tcf_vendor_relationships[0].description
            == "My TCF System Description"
        )

        # assert some additional TCF attributes are set to their defaults here - this is where they belong!
        assert tcf_contents.tcf_vendor_relationships[0].cookie_max_age_seconds is None
        assert tcf_contents.tcf_vendor_relationships[0].uses_cookies is False
        assert tcf_contents.tcf_vendor_relationships[0].uses_non_cookie_access is False
        assert tcf_contents.tcf_vendor_relationships[0].cookie_refresh is False
        assert (
            tcf_contents.tcf_vendor_relationships[0].legitimate_interest_disclosure_url
            is None
        )
        assert tcf_contents.tcf_vendor_relationships[0].privacy_policy_url is None
        assert len(tcf_contents.tcf_vendor_relationships[0].special_purposes) == 1
        assert tcf_contents.tcf_vendor_relationships[0].special_purposes[0].id == 1
        assert (
            tcf_contents.tcf_vendor_relationships[0]
            .special_purposes[0]
            .retention_period
            == "1"
        )

    def test_system_exists_with_tcf_purpose_and_vendor_including_tcf_fields_set(
        self, db, tcf_system
    ):
        """System has vendor id so we return preferences against a "vendor" instead of the system

        Vendor has some TCF-specific attributes set, ensure they are being surfaced properly in the overlay.
        """
        tcf_system.cookie_max_age_seconds = 31536000
        tcf_system.uses_cookies = True
        tcf_system.cookie_refresh = True
        tcf_system.uses_non_cookie_access = True
        tcf_system.legitimate_interest_disclosure_url = "http://test.com/disclosure_url"
        tcf_system.privacy_policy = "http://test.com/privacy_url"
        tcf_system.save(db)

        tcf_contents = get_tcf_contents(db)
        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=1,
            p_li_len=0,
            f_len=0,
            sp_len=1,
            sf_len=0,
            v_c_len=1,
            v_li_len=0,
            v_r_len=1,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

        assert tcf_contents.tcf_purpose_consents[0].id == 8
        assert tcf_contents.tcf_purpose_consents[0].data_uses == [
            "analytics.reporting.content_performance"
        ]
        assert tcf_contents.tcf_purpose_consents[0].vendors == [
            EmbeddedVendor(id="gvl.42", name="TCF System Test")
        ]

        assert tcf_contents.tcf_vendor_consents[0].id == "gvl.42"
        assert tcf_contents.tcf_vendor_consents[0].name == "TCF System Test"
        assert (
            tcf_contents.tcf_vendor_consents[0].description
            == "My TCF System Description"
        )

        # assert some additional TCF attributes are NOT set on the consents object - only on VendorRelationships
        assert not hasattr(
            tcf_contents.tcf_vendor_consents[0], "cookie_max_age_seconds"
        )
        assert not hasattr(tcf_contents.tcf_vendor_consents[0], "uses_cookies")
        assert not hasattr(
            tcf_contents.tcf_vendor_consents[0], "legitimate_interest_disclosure_url"
        )
        assert not hasattr(tcf_contents.tcf_vendor_consents[0], "privacy_policy_url")

        assert len(tcf_contents.tcf_vendor_consents[0].purpose_consents) == 1
        assert tcf_contents.tcf_vendor_consents[0].purpose_consents[0].id == 8
        assert (
            tcf_contents.tcf_vendor_consents[0].purpose_consents[0].retention_period
            == "3"
        )

        assert tcf_contents.tcf_vendor_relationships[0].id == "gvl.42"
        assert tcf_contents.tcf_vendor_relationships[0].name == "TCF System Test"
        assert (
            tcf_contents.tcf_vendor_relationships[0].description
            == "My TCF System Description"
        )

        # assert some additional TCF attributes are being populated properly based on the System record
        assert (
            tcf_contents.tcf_vendor_relationships[0].cookie_max_age_seconds == 31536000
        )
        assert tcf_contents.tcf_vendor_relationships[0].uses_cookies is True
        assert tcf_contents.tcf_vendor_relationships[0].uses_non_cookie_access is True
        assert tcf_contents.tcf_vendor_relationships[0].cookie_refresh is True
        assert (
            tcf_contents.tcf_vendor_relationships[0].legitimate_interest_disclosure_url
            == "http://test.com/disclosure_url"
        )
        assert (
            tcf_contents.tcf_vendor_relationships[0].privacy_policy_url
            == "http://test.com/privacy_url"
        )

        assert len(tcf_contents.tcf_vendor_relationships[0].special_purposes) == 1
        assert tcf_contents.tcf_vendor_relationships[0].special_purposes[0].id == 1

    def test_system_exists_with_tcf_data_use_but_no_official_vendor_linked(
        self, db, tcf_system
    ):
        """System does not have an official vendor id so we return preferences against the system itself"""
        tcf_system.vendor_id = None
        tcf_system.save(db)

        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=1,
            p_li_len=0,
            f_len=0,
            sp_len=1,
            sf_len=0,
            v_c_len=0,
            v_li_len=0,
            v_r_len=0,
            s_c_len=1,
            s_li_len=0,
            s_r_len=1,
        )

        assert tcf_contents.tcf_purpose_consents[0].id == 8
        # No "vendors" because we don't have an official vendor id
        assert len(tcf_contents.tcf_purpose_consents[0].vendors) == 0
        # System returned instead
        assert len(tcf_contents.tcf_purpose_consents[0].systems) == 1

        assert tcf_contents.tcf_system_consents[0].id == tcf_system.id
        assert tcf_contents.tcf_system_consents[0].name == "TCF System Test"
        assert (
            tcf_contents.tcf_system_consents[0].description
            == "My TCF System Description"
        )
        assert len(tcf_contents.tcf_system_consents[0].purpose_consents) == 1
        assert tcf_contents.tcf_system_consents[0].purpose_consents[0].id == 8
        assert tcf_contents.tcf_system_consents[0].has_vendor_id is False

        assert tcf_contents.tcf_system_relationships[0].id == tcf_system.id
        assert tcf_contents.tcf_system_relationships[0].name == "TCF System Test"
        assert (
            tcf_contents.tcf_system_relationships[0].description
            == "My TCF System Description"
        )
        assert len(tcf_contents.tcf_system_relationships[0].special_purposes) == 1
        assert tcf_contents.tcf_system_relationships[0].special_purposes[0].id == 1

    @pytest.mark.usefixtures("tcf_system")
    def test_vendor_on_multiple_systems(self, db, system, tcf_system):
        """Vendor id shows up on multiple systems but it is collapsed in response"""
        # Add the same vendor id to the system that the tcf_system is using
        system.vendor_id = tcf_system.vendor_id
        system.name = tcf_system.name
        system.description = tcf_system.description
        system.save(db)
        # Add the same TCF-related data use to the system that the tcf system is using
        decl = system.privacy_declarations[0]
        decl.data_use = "analytics.reporting.content_performance"
        decl.legal_basis_for_processing = "Consent"
        decl.save(db)

        # Add a separate use to this system
        PrivacyDeclaration.create(
            db=db,
            data={
                "name": "Store and access info on a device",
                "system_id": system.id,
                "data_categories": ["user"],
                "data_use": "functional.storage",
                "data_qualifier": "aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
                "data_subjects": ["customer"],
                "dataset_references": None,
                "legal_basis_for_processing": "Consent",
                "egress": None,
                "ingress": None,
            },
        )

        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=2,
            p_li_len=0,
            f_len=0,
            sp_len=1,
            sf_len=0,
            v_c_len=1,
            v_li_len=0,
            v_r_len=1,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

        assert {purpose.id for purpose in tcf_contents.tcf_purpose_consents} == {1, 8}
        assert {
            use
            for purpose in tcf_contents.tcf_purpose_consents
            for use in purpose.data_uses
        } == {"functional.storage", "analytics.reporting.content_performance"}
        assert tcf_contents.tcf_purpose_consents[0].vendors == [
            EmbeddedVendor(id="gvl.42", name="TCF System Test")
        ]

        assert tcf_contents.tcf_vendor_consents[0].id == "gvl.42"
        assert tcf_contents.tcf_vendor_consents[0].name == "TCF System Test"
        assert (
            tcf_contents.tcf_vendor_consents[0].description
            == "My TCF System Description"
        )
        # Purposes also consolidated
        assert len(tcf_contents.tcf_vendor_consents[0].purpose_consents) == 2
        assert {
            purpose.id
            for purpose in tcf_contents.tcf_vendor_consents[0].purpose_consents
        } == {
            1,
            8,
        }

    @pytest.mark.usefixtures("tcf_system")
    def test_system_matches_subset_of_purpose_data_uses(self, db, tcf_system):
        """Test making sure you just need to match one data use to be able to surface the purpose,
        in the case where a purpose corresponds to multiple data uses"""
        for i, decl in enumerate(tcf_system.privacy_declarations):
            if i:
                decl.data_use = "marketing.advertising.first_party.contextual"
                decl.legal_basis_for_processing = "Consent"
                tcf_system.privacy_declarations[0].save(db)
            else:
                decl.delete(db)

        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=1,
            p_li_len=0,
            f_len=0,
            sp_len=0,
            sf_len=0,
            v_c_len=1,
            v_li_len=0,
            v_r_len=1,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

        assert tcf_contents.tcf_purpose_consents[0].id == 2
        assert tcf_contents.tcf_purpose_consents[0].data_uses == [
            "marketing.advertising.first_party.contextual",
            "marketing.advertising.frequency_capping",
            "marketing.advertising.negative_targeting",
        ]
        assert tcf_contents.tcf_purpose_consents[0].vendors == [
            EmbeddedVendor(id="gvl.42", name="TCF System Test")
        ]

        assert tcf_contents.tcf_vendor_consents[0].id == "gvl.42"
        assert len(tcf_contents.tcf_vendor_consents[0].purpose_consents) == 1
        assert tcf_contents.tcf_vendor_consents[0].purpose_consents[0].id == 2

    @pytest.mark.usefixtures("tcf_system")
    def test_two_vendors_same_purpose_different_retention_period(self, db, tcf_system):
        """Test making sure that two vendors that share the same purpose show up with
        different retention periods in their EmbeddedPurposes"""

        # Create a second system with the same privacy declaration as tcf_system
        # but with a different retention period
        second_system = System.create(
            db=db,
            data={
                "fides_key": f"tcf-system_key-f{uuid4()}",
                "vendor_id": "gvl.100",
                "name": f"TCF System Second Test",
                "description": "My Second TCF System Description",
                "organization_fides_key": "default_organization",
                "system_type": "Service",
                "data_responsibility_title": "Processor",
                "data_protection_impact_assessment": {
                    "is_required": False,
                    "progress": None,
                    "link": None,
                },
            },
        )

        PrivacyDeclaration.create(
            db=db,
            data={
                "name": "Collect data for content performance",
                "system_id": second_system.id,
                "data_categories": ["user.device.cookie_id"],
                "data_use": "analytics.reporting.content_performance",
                "data_qualifier": "aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
                "data_subjects": ["customer"],
                "dataset_references": None,
                "legal_basis_for_processing": "Consent",
                "egress": None,
                "ingress": None,
                "retention_period": "5",  # the fixture already has a retention_period of 3
            },
        )

        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=1,
            p_li_len=0,
            f_len=0,
            sp_len=1,
            sf_len=0,
            v_c_len=2,
            v_li_len=0,
            v_r_len=2,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

        assert tcf_contents.tcf_vendor_consents[0].id == "gvl.100"
        assert tcf_contents.tcf_vendor_consents[0].purpose_consents == [
            {"id": 8, "name": "Measure content performance", "retention_period": "5"}
        ]

        assert tcf_contents.tcf_vendor_consents[1].id == "gvl.42"
        assert tcf_contents.tcf_vendor_consents[1].purpose_consents == [
            {"id": 8, "name": "Measure content performance", "retention_period": "3"}
        ]

    @pytest.mark.usefixtures("tcf_system")
    def test_special_purposes(self, db):
        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=1,
            p_li_len=0,
            f_len=0,
            sp_len=1,
            sf_len=0,
            v_c_len=1,
            v_li_len=0,
            v_r_len=1,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

        assert len(tcf_contents.tcf_special_purposes) == 1
        assert tcf_contents.tcf_special_purposes[0].id == 1
        assert (
            tcf_contents.tcf_special_purposes[0].name
            == "Ensure security, prevent and detect fraud, and fix errors"
        )
        assert tcf_contents.tcf_special_purposes[0].vendors == [
            EmbeddedVendor(id="gvl.42", name="TCF System Test")
        ]

        assert tcf_contents.tcf_vendor_consents[0].id == "gvl.42"
        assert len(tcf_contents.tcf_vendor_consents[0].purpose_consents) == 1
        assert tcf_contents.tcf_vendor_consents[0].purpose_consents[0].id == 8

        assert tcf_contents.tcf_vendor_relationships[0].id == "gvl.42"
        assert len(tcf_contents.tcf_vendor_relationships[0].special_purposes) == 1
        assert tcf_contents.tcf_vendor_relationships[0].special_purposes[0].id == 1

    @pytest.mark.usefixtures("system")
    def test_features(self, db, system):
        system.vendor_id = "test_system"
        system.save(db)
        declaration = system.privacy_declarations[0]

        declaration.data_use = "functional.storage"  # needs a GVL data use for features to show up. Feature must be linked to a GVL data use.
        declaration.legal_basis_for_processing = "Consent"  # Needed to be applicable
        declaration.features = [
            "Identify devices based on information transmitted automatically",
            "unknown feature",
            "Identify devices based on information transmitted automatically",  # Ensuring this doesn't show up twice
        ]
        declaration.save(db)

        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=1,
            p_li_len=0,
            f_len=1,
            sp_len=0,
            sf_len=0,
            v_c_len=1,
            v_li_len=0,
            v_r_len=1,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

        assert len(tcf_contents.tcf_features) == 1
        assert tcf_contents.tcf_features[0].id == 3
        assert (
            tcf_contents.tcf_features[0].name
            == "Identify devices based on information transmitted automatically"
        )

        assert len(tcf_contents.tcf_vendor_relationships[0].features) == 1
        assert tcf_contents.tcf_vendor_relationships[0].features[0].id == 3

    @pytest.mark.usefixtures("system")
    def test_special_features(self, db, system):
        system.vendor_id = "test_system"
        system.save(db)
        declaration = system.privacy_declarations[0]

        declaration.data_use = "functional.storage"  # needs a GVL data use for features to show up. Feature must be linked to a GVL data use.
        declaration.legal_basis_for_processing = "Consent"  # Needed to be applicable
        declaration.features = [
            "Actively scan device characteristics for identification",
            "unknown special feature",
            "Actively scan device characteristics for identification",  # Ensuring this doesn't show up twice
        ]
        declaration.save(db)

        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=1,
            p_li_len=0,
            f_len=0,
            sp_len=0,
            sf_len=1,
            v_c_len=1,
            v_li_len=0,
            v_r_len=1,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

        assert tcf_contents.tcf_special_features[0].id == 2
        assert (
            tcf_contents.tcf_special_features[0].name
            == "Actively scan device characteristics for identification"
        )

        assert len(tcf_contents.tcf_vendor_relationships[0].special_features) == 1
        assert tcf_contents.tcf_vendor_relationships[0].special_features[0].id == 2
        assert len(tcf_contents.tcf_vendor_relationships[0].features) == 0

    def test_system_with_multiple_privacy_declarations(self, db, system):
        """Add a system with multiple privacy declarations, one for each legal basis for processing, with a different gvl data use
        Only the two privacy declarations with Consent and Legitimate Interests legal bases are relevant here.
        """
        legal_bases = [item.value for item in LegalBasisForProcessingEnum]

        for i, legal_basis in enumerate(legal_bases):
            gvl_purpose = list(MAPPED_PURPOSES.values())[i]

            PrivacyDeclaration.create(
                db=db,
                data={
                    "name": gvl_purpose.name,
                    "system_id": system.id,
                    "data_categories": ["user.device.cookie_id"],
                    "data_use": gvl_purpose.data_uses[0],
                    "data_qualifier": "aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
                    "data_subjects": ["customer"],
                    "legal_basis_for_processing": legal_basis,
                },
            )

        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=1,
            p_li_len=1,
            f_len=0,
            sp_len=0,
            sf_len=0,
            v_c_len=0,
            v_li_len=0,
            v_r_len=0,
            s_c_len=1,
            s_li_len=1,
            s_r_len=1,
        )

        first_purpose = tcf_contents.tcf_purpose_consents[0]
        assert first_purpose.id == 1

        second_purpose = tcf_contents.tcf_purpose_legitimate_interests[0]
        assert second_purpose.id == 6

        system_info = tcf_contents.tcf_system_consents[0]
        assert len(system_info.purpose_consents) == 1
        assert system_info.purpose_consents[0].id == 1

        system_info = tcf_contents.tcf_system_legitimate_interests[0]
        assert len(system_info.purpose_legitimate_interests) == 1
        assert system_info.purpose_legitimate_interests[0].id == 6

    def test_duplicate_data_uses_on_system(self, tcf_system, db):
        """Contrived test (since UI enforces unique data uses on systems), that adds the same data use to multiple privacy declarations.
        Since one has a legal basis of Consent, and the other has a legal basis of Legitimate interests, that purpose
        shows up twice, once under each section
        """
        for privacy_decl in tcf_system.privacy_declarations:
            privacy_decl.data_use = "marketing.advertising.profiling"
            privacy_decl.save(db)

        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=1,
            p_li_len=1,
            f_len=0,
            sp_len=0,
            sf_len=0,
            v_c_len=1,
            v_li_len=1,
            v_r_len=1,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

        assert tcf_contents.tcf_purpose_consents[0].id == 3
        assert len(tcf_contents.tcf_purpose_consents[0].vendors) == 1
        assert tcf_contents.tcf_purpose_consents[0].vendors[0].name == tcf_system.name
        assert len(tcf_contents.tcf_purpose_consents[0].systems) == 0

        assert tcf_contents.tcf_purpose_legitimate_interests[0].id == 3
        assert len(tcf_contents.tcf_purpose_legitimate_interests[0].vendors) == 1
        assert (
            tcf_contents.tcf_purpose_legitimate_interests[0].vendors[0].name
            == tcf_system.name
        )
        assert len(tcf_contents.tcf_purpose_legitimate_interests[0].systems) == 0

        assert tcf_contents.tcf_vendor_consents[0].name == tcf_system.name
        assert len(tcf_contents.tcf_vendor_consents[0].purpose_consents) == 1
        assert tcf_contents.tcf_vendor_consents[0].purpose_consents[0].id == 3

        assert (
            len(
                tcf_contents.tcf_vendor_legitimate_interests[
                    0
                ].purpose_legitimate_interests
            )
            == 1
        )
        assert (
            tcf_contents.tcf_vendor_legitimate_interests[0]
            .purpose_legitimate_interests[0]
            .id
            == 3
        )
        assert (
            tcf_contents.tcf_vendor_legitimate_interests[0]
            .purpose_legitimate_interests[0]
            .retention_period
            == "1"
        )

    def test_add_different_data_uses_that_correspond_to_same_purpose(
        self, tcf_system, db
    ):
        """Add different data uses to the same system that correspond to the same purpose
        Assert that this doesn't create duplicate purposes.  They are separated by their legal basis
        """
        new_uses = [
            "marketing.advertising.first_party.contextual",
            "marketing.advertising.frequency_capping",
        ]
        new_legal_bases = ["Consent", "Legitimate interests"]
        for i, privacy_decl in enumerate(tcf_system.privacy_declarations):
            privacy_decl.data_use = new_uses[i]
            privacy_decl.legal_basis_for_processing = new_legal_bases[i]
            privacy_decl.save(db)

        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=1,
            p_li_len=1,
            f_len=0,
            sp_len=0,
            sf_len=0,
            v_c_len=1,
            v_li_len=1,
            v_r_len=1,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

        assert tcf_contents.tcf_purpose_consents[0].id == 2
        assert tcf_contents.tcf_purpose_legitimate_interests[0].id == 2

        assert len(tcf_contents.tcf_purpose_consents[0].vendors) == 1
        assert tcf_contents.tcf_purpose_consents[0].vendors[0].name == tcf_system.name
        assert len(tcf_contents.tcf_purpose_consents[0].systems) == 0

        assert len(tcf_contents.tcf_purpose_legitimate_interests[0].vendors) == 1
        assert (
            tcf_contents.tcf_purpose_legitimate_interests[0].vendors[0].name
            == tcf_system.name
        )
        assert len(tcf_contents.tcf_purpose_legitimate_interests[0].systems) == 0

        assert tcf_contents.tcf_vendor_consents[0].name == tcf_system.name
        assert len(tcf_contents.tcf_vendor_consents[0].purpose_consents) == 1
        assert tcf_contents.tcf_vendor_consents[0].purpose_consents[0].id == 2
        assert (
            len(
                tcf_contents.tcf_vendor_legitimate_interests[
                    0
                ].purpose_legitimate_interests
            )
            == 1
        )
        assert (
            tcf_contents.tcf_vendor_legitimate_interests[0]
            .purpose_legitimate_interests[0]
            .id
            == 2
        )

    def test_add_same_data_use_to_different_systems(
        self, system_with_no_uses, system, db
    ):
        """Add same data uses to different systems. Assert this doesn't create duplicate purposes"""
        system.name = "System A"
        system.save(db)

        decl = system.privacy_declarations[0]
        decl.legal_basis_for_processing = "Legitimate interests"
        decl.data_use = "marketing.advertising.first_party.targeted"
        decl.save(db)

        system_with_no_uses.name = "System B"
        system_with_no_uses.save(db)

        PrivacyDeclaration.create(
            db=db,
            data={
                "name": "Collect data for content performance",
                "system_id": system_with_no_uses.id,
                "data_categories": ["user.device.cookie_id"],
                "data_use": "marketing.advertising.first_party.targeted",
                "data_qualifier": "aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
                "data_subjects": ["customer"],
                "dataset_references": None,
                "legal_basis_for_processing": "Consent",
                "egress": None,
                "ingress": None,
            },
        )

        # Contrived - same data use, different legal basis
        PrivacyDeclaration.create(
            db=db,
            data={
                "name": "Collect data for content performance",
                "system_id": system_with_no_uses.id,
                "data_categories": ["user.device.cookie_id"],
                "data_use": "marketing.advertising.first_party.targeted",
                "data_qualifier": "aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
                "data_subjects": ["customer"],
                "dataset_references": None,
                "legal_basis_for_processing": "Legitimate interests",
                "egress": None,
                "ingress": None,
            },
        )

        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=1,
            p_li_len=1,
            f_len=0,
            sp_len=0,
            sf_len=0,
            v_c_len=0,
            v_li_len=0,
            v_r_len=0,
            s_c_len=1,
            s_li_len=2,
            s_r_len=2,
        )
        assert len(tcf_contents.tcf_purpose_consents[0].vendors) == 0
        assert tcf_contents.tcf_purpose_consents[0].id == 4
        assert tcf_contents.tcf_purpose_legitimate_interests[0].id == 4

        assert tcf_contents.tcf_system_legitimate_interests[0].name == "System A"
        assert (
            len(
                tcf_contents.tcf_system_legitimate_interests[
                    0
                ].purpose_legitimate_interests
            )
            == 1
        )
        assert (
            tcf_contents.tcf_system_legitimate_interests[0]
            .purpose_legitimate_interests[0]
            .id
            == 4
        )

        assert tcf_contents.tcf_system_consents[0].name == "System B"
        assert len(tcf_contents.tcf_system_consents[0].purpose_consents) == 1
        assert tcf_contents.tcf_system_consents[0].purpose_consents[0].id == 4

        assert tcf_contents.tcf_system_legitimate_interests[1].name == "System B"
        assert (
            len(
                tcf_contents.tcf_system_legitimate_interests[
                    1
                ].purpose_legitimate_interests
            )
            == 1
        )
        assert (
            tcf_contents.tcf_system_legitimate_interests[1]
            .purpose_legitimate_interests[0]
            .id
            == 4
        )

    @pytest.mark.usefixtures("ac_system_with_privacy_declaration", "enable_ac")
    def test_ac_systems_with_consent_privacy_declarations(self, db):
        """This AC system won't show up under vendor consents, but because it has a
        valid declaration with a gvl data use, that shows up under purpose consents

        It incorrectly has a separate declaration with a LI legal basis but that isn't surfaced here
        """
        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=1,
            p_li_len=0,
            f_len=1,
            sp_len=0,
            sf_len=0,
            v_c_len=1,
            v_li_len=0,
            v_r_len=1,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

        vendor_consent = tcf_contents.tcf_vendor_consents[0]
        assert vendor_consent.id == "gacp.8"
        assert len(vendor_consent.purpose_consents) == 1
        assert vendor_consent.purpose_consents[0].id == 1

        vendor_relationship = tcf_contents.tcf_vendor_relationships[0]
        assert vendor_relationship.id == "gacp.8"
        assert vendor_relationship.features[0].id == 2
        assert vendor_relationship.special_purposes == []
        assert vendor_relationship.special_features == []
        assert vendor_relationship.cookie_max_age_seconds is None
        assert vendor_relationship.uses_cookies is False
        assert vendor_relationship.uses_non_cookie_access is False
        assert vendor_relationship.cookie_refresh is False
        assert vendor_relationship.legitimate_interest_disclosure_url is None

    @pytest.mark.usefixtures("ac_system_without_privacy_declaration", "enable_ac")
    def test_ac_systems_without_privacy_declarations(self, db):
        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=0,
            p_li_len=0,
            f_len=0,
            sp_len=0,
            sf_len=0,
            v_c_len=1,
            v_li_len=0,
            v_r_len=1,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

        vendor_consent = tcf_contents.tcf_vendor_consents[0]
        assert vendor_consent.id == "gacp.100"
        assert (
            vendor_consent.purpose_consents == []
        )  # AC Vendor showed up in this section even though it didn't have any purposes

        vendor_relationship = tcf_contents.tcf_vendor_relationships[0]
        assert vendor_relationship.id == "gacp.100"
        assert vendor_relationship.features == []
        assert vendor_relationship.special_purposes == []
        assert vendor_relationship.special_features == []
        assert vendor_relationship.cookie_max_age_seconds is None
        assert vendor_relationship.uses_cookies is False
        assert vendor_relationship.uses_non_cookie_access is False
        assert vendor_relationship.cookie_refresh is False
        assert vendor_relationship.legitimate_interest_disclosure_url is None

    @pytest.mark.usefixtures("ac_system_without_privacy_declaration")
    def test_ac_systems_with_ac_disabled(self, db):
        """Available AC systems are suppressed from the Experience"""
        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=0,
            p_li_len=0,
            f_len=0,
            sp_len=0,
            sf_len=0,
            v_c_len=0,
            v_li_len=0,
            v_r_len=0,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

    @pytest.mark.usefixtures("ac_system_with_invalid_li_declaration", "enable_ac")
    def test_ac_systems_with_li_privacy_declarations_only(self, db):
        """I suppress this AC system entirely - it was only defined with a purpose that had a legitimate interest legal
        basis which isn't permitted"""
        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=0,
            p_li_len=0,
            f_len=0,
            sp_len=0,
            sf_len=0,
            v_c_len=0,
            v_li_len=0,
            v_r_len=0,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )

    @pytest.mark.usefixtures("ac_system_with_invalid_vi_declaration", "enable_ac")
    def test_ac_systems_with_li_privacy_declarations_only(self, db):
        """I suppress this AC system entirely - it was only defined with a purpose that had a vital interests legal basis"""
        tcf_contents = get_tcf_contents(db)

        assert_length_of_tcf_sections(
            tcf_contents,
            p_c_len=0,
            p_li_len=0,
            f_len=0,
            sp_len=0,
            sf_len=0,
            v_c_len=0,
            v_li_len=0,
            v_r_len=0,
            s_c_len=0,
            s_li_len=0,
            s_r_len=0,
        )
