import pytest
from fideslang import MAPPED_PURPOSES
from fideslang.models import LegalBasisForProcessingEnum

from fides.api.models.sql_models import PrivacyDeclaration
from fides.api.schemas.tcf import EmbeddedVendor
from fides.api.util.tcf_util import get_tcf_contents


class TestTCFContents:
    def test_load_tcf_data_uses_no_applicable_systems(self, db):
        get_tcf_contents.cache_clear()

        tcf_contents = get_tcf_contents(db)
        assert tcf_contents.tcf_purposes == []
        assert tcf_contents.tcf_vendors == []
        assert tcf_contents.tcf_special_purposes == []
        assert tcf_contents.tcf_features == []
        assert tcf_contents.tcf_special_features == []
        assert tcf_contents.tcf_systems == []

    @pytest.mark.usefixtures("system")
    def test_load_tcf_data_uses_systems_but_no_overlapping_use_or_feature(self, db):
        get_tcf_contents.cache_clear()

        tcf_contents = get_tcf_contents(db)
        assert tcf_contents.tcf_purposes == []
        assert tcf_contents.tcf_vendors == []
        assert tcf_contents.tcf_special_purposes == []
        assert tcf_contents.tcf_features == []
        assert tcf_contents.tcf_special_features == []
        assert tcf_contents.tcf_systems == []

    def test_feature_that_is_not_in_the_gvl(self, db, system):
        get_tcf_contents.cache_clear()

        decl = system.privacy_declarations[0]
        decl.features = ["non_gvl_feature"]
        decl.save(db)

        db.refresh(decl)
        assert decl.features == ["non_gvl_feature"]

        tcf_contents = get_tcf_contents(db)
        assert tcf_contents.tcf_purposes == []
        assert tcf_contents.tcf_vendors == []
        assert tcf_contents.tcf_special_purposes == []
        assert tcf_contents.tcf_features == []
        assert tcf_contents.tcf_special_features == []
        assert tcf_contents.tcf_systems == []

    @pytest.mark.usefixtures("tcf_system")
    def test_system_exists_with_tcf_purpose_and_vendor(self, db):
        """System has vendor id so we return preferences against a "vendor" instead of the system"""
        get_tcf_contents.cache_clear()

        tcf_contents = get_tcf_contents(db)
        assert len(tcf_contents.tcf_purposes) == 1
        assert tcf_contents.tcf_purposes[0].id == 8
        assert tcf_contents.tcf_purposes[0].data_uses == [
            "analytics.reporting.content_performance"
        ]
        assert tcf_contents.tcf_purposes[0].vendors == [
            EmbeddedVendor(id="sendgrid", name="TCF System Test")
        ]

        assert tcf_contents.tcf_systems == []
        assert len(tcf_contents.tcf_vendors) == 1
        assert tcf_contents.tcf_vendors[0].id == "sendgrid"
        assert tcf_contents.tcf_vendors[0].name == "TCF System Test"
        assert tcf_contents.tcf_vendors[0].description == "My TCF System Description"
        assert len(tcf_contents.tcf_vendors[0].purposes) == 1
        assert tcf_contents.tcf_vendors[0].purposes[0].id == 8
        assert tcf_contents.tcf_features == []
        assert tcf_contents.tcf_special_features == []

    def test_system_exists_with_tcf_data_use_but_no_official_vendor_linked(
        self, db, tcf_system
    ):
        """System does not have an official vendor id so we return preferences against the system itself"""
        get_tcf_contents.cache_clear()

        tcf_system.vendor_id = None
        tcf_system.save(db)

        tcf_contents = get_tcf_contents(db)
        assert len(tcf_contents.tcf_purposes) == 1
        assert tcf_contents.tcf_purposes[0].id == 8

        # No "vendors" because we don't have an official vendor id
        assert len(tcf_contents.tcf_purposes[0].vendors) == 0
        # System returned instead
        assert len(tcf_contents.tcf_purposes[0].systems) == 1

        assert tcf_contents.tcf_vendors == []
        assert tcf_contents.tcf_features == []
        assert tcf_contents.tcf_special_features == []
        assert len(tcf_contents.tcf_systems) == 1

        assert tcf_contents.tcf_systems[0].id == tcf_system.id
        assert tcf_contents.tcf_systems[0].name == "TCF System Test"
        assert tcf_contents.tcf_systems[0].description == "My TCF System Description"

        assert len(tcf_contents.tcf_systems[0].purposes) == 1
        assert tcf_contents.tcf_systems[0].purposes[0].id == 8
        assert tcf_contents.tcf_systems[0].has_vendor_id is False

    @pytest.mark.usefixtures("tcf_system")
    def test_vendor_on_multiple_systems(self, db, system, tcf_system):
        """Vendor id shows up on multiple systems but it is collapsed in response"""
        get_tcf_contents.cache_clear()

        # Add the same vendor id to the system that the tcf_system is using
        system.vendor_id = tcf_system.vendor_id
        system.name = tcf_system.name
        system.description = tcf_system.description
        system.save(db)
        # Add the same TCF-related data use to the system that the tcf system is using
        decl = system.privacy_declarations[0]
        decl.data_use = "analytics.reporting.content_performance"
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
                "egress": None,
                "ingress": None,
            },
        )

        tcf_contents = get_tcf_contents(db)

        assert len(tcf_contents.tcf_purposes) == 2
        assert {purpose.id for purpose in tcf_contents.tcf_purposes} == {1, 8}
        assert {
            use for purpose in tcf_contents.tcf_purposes for use in purpose.data_uses
        } == {"functional.storage", "analytics.reporting.content_performance"}
        assert tcf_contents.tcf_purposes[0].vendors == [
            EmbeddedVendor(id="sendgrid", name="TCF System Test")
        ]

        assert tcf_contents.tcf_systems == []
        assert len(tcf_contents.tcf_vendors) == 1
        assert tcf_contents.tcf_vendors[0].id == "sendgrid"
        assert tcf_contents.tcf_vendors[0].name == "TCF System Test"
        assert tcf_contents.tcf_vendors[0].description == "My TCF System Description"
        # Purposes also consolidated
        assert len(tcf_contents.tcf_vendors[0].purposes) == 2
        assert {purpose.id for purpose in tcf_contents.tcf_vendors[0].purposes} == {
            1,
            8,
        }
        assert tcf_contents.tcf_features == []
        assert tcf_contents.tcf_special_features == []

    @pytest.mark.usefixtures("tcf_system")
    def test_system_matches_subset_of_purpose_data_uses(self, db, tcf_system):
        get_tcf_contents.cache_clear()

        for i, decl in enumerate(tcf_system.privacy_declarations):
            if i:
                decl.data_use = "marketing.advertising.first_party.contextual"
                decl.legal_basis_for_processing = "Consent"
                tcf_system.privacy_declarations[0].save(db)
            else:
                decl.delete(db)

        tcf_contents = get_tcf_contents(db)

        assert len(tcf_contents.tcf_purposes) == 1
        assert tcf_contents.tcf_purposes[0].id == 2
        assert tcf_contents.tcf_purposes[0].data_uses == [
            "marketing.advertising.first_party.contextual",
            "marketing.advertising.frequency_capping",
            "marketing.advertising.negative_targeting",
        ]
        assert tcf_contents.tcf_purposes[0].legal_bases == ["Consent"]
        assert tcf_contents.tcf_purposes[0].vendors == [
            EmbeddedVendor(id="sendgrid", name="TCF System Test")
        ]

        assert len(tcf_contents.tcf_vendors) == 1
        assert tcf_contents.tcf_vendors[0].id == "sendgrid"
        assert len(tcf_contents.tcf_vendors[0].purposes) == 1
        assert tcf_contents.tcf_vendors[0].purposes[0].id == 2
        assert tcf_contents.tcf_vendors[0].purposes[0].legal_bases == ["Consent"]
        assert tcf_contents.tcf_features == []
        assert tcf_contents.tcf_special_features == []

    @pytest.mark.usefixtures("tcf_system")
    def test_special_purposes(self, db):
        get_tcf_contents.cache_clear()

        tcf_contents = get_tcf_contents(db)
        assert len(tcf_contents.tcf_special_purposes) == 1
        assert tcf_contents.tcf_special_purposes[0].id == 1
        assert (
            tcf_contents.tcf_special_purposes[0].name
            == "Ensure security, prevent and detect fraud, and fix errors\n"
        )
        assert tcf_contents.tcf_special_purposes[0].legal_bases == ["Legal obligations"]
        assert tcf_contents.tcf_special_purposes[0].vendors == [
            EmbeddedVendor(id="sendgrid", name="TCF System Test")
        ]

        assert len(tcf_contents.tcf_purposes) == 1

        assert len(tcf_contents.tcf_vendors) == 1
        assert tcf_contents.tcf_vendors[0].id == "sendgrid"
        assert len(tcf_contents.tcf_vendors[0].purposes) == 1
        assert tcf_contents.tcf_vendors[0].purposes[0].id == 8
        assert tcf_contents.tcf_vendors[0].purposes[0].legal_bases == ["Consent"]

        assert len(tcf_contents.tcf_vendors[0].special_purposes) == 1
        assert tcf_contents.tcf_vendors[0].special_purposes[0].id == 1
        assert tcf_contents.tcf_vendors[0].special_purposes[0].legal_bases == [
            "Legal obligations"
        ]
        assert tcf_contents.tcf_features == []
        assert tcf_contents.tcf_special_features == []

    @pytest.mark.usefixtures("system")
    def test_features(self, db, system):
        get_tcf_contents.cache_clear()

        system.vendor_id = "test_system"
        system.save(db)
        declaration = system.privacy_declarations[0]

        declaration.features = [
            "Receive and use automatically-sent device characteristics for identification",
            "unknown feature",
            "Receive and use automatically-sent device characteristics for identification",  # Ensuring this doesn't show up twice
        ]
        declaration.save(db)

        tcf_contents = get_tcf_contents(db)
        assert len(tcf_contents.tcf_features) == 1
        assert tcf_contents.tcf_features[0].id == 3
        assert (
            tcf_contents.tcf_features[0].name
            == "Receive and use automatically-sent device characteristics for identification"
        )
        assert tcf_contents.tcf_special_features == []

        assert len(tcf_contents.tcf_vendors) == 1
        assert len(tcf_contents.tcf_vendors[0].features) == 1
        assert tcf_contents.tcf_vendors[0].features[0].id == 3

    @pytest.mark.usefixtures("system")
    def test_special_features(self, db, system):
        get_tcf_contents.cache_clear()

        system.vendor_id = "test_system"
        system.save(db)
        declaration = system.privacy_declarations[0]

        declaration.features = [
            "Actively scan device characteristics for identification",
            "unknown special feature",
            "Actively scan device characteristics for identification",  # Ensuring this doesn't show up twice
        ]
        declaration.save(db)

        tcf_contents = get_tcf_contents(db)
        assert len(tcf_contents.tcf_features) == 0
        assert len(tcf_contents.tcf_special_features) == 1
        assert tcf_contents.tcf_special_features[0].id == 2
        assert (
            tcf_contents.tcf_special_features[0].name
            == "Actively scan device characteristics for identification"
        )

        assert len(tcf_contents.tcf_vendors) == 1
        assert len(tcf_contents.tcf_vendors[0].special_features) == 1
        assert tcf_contents.tcf_vendors[0].special_features[0].id == 2
        assert len(tcf_contents.tcf_vendors[0].features) == 0

    def test_system_with_multiple_privacy_declarations(self, db, system):
        get_tcf_contents.cache_clear()

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
        assert len(tcf_contents.tcf_purposes) == 6
        for i, purpose in enumerate(tcf_contents.tcf_purposes):
            assert purpose.legal_bases == [legal_bases[i]]
            assert purpose.id == list(MAPPED_PURPOSES.values())[i].id
        assert (
            len(tcf_contents.tcf_vendors) == 0
        )  # No official vendor id on this system

        assert len(tcf_contents.tcf_systems) == 1
        system_info = tcf_contents.tcf_systems[0]

        assert len(system_info.special_purposes) == 0
        assert len(system_info.features) == 0
        assert len(system_info.special_features) == 0
        assert len(tcf_contents.tcf_systems[0].purposes) == 6
        for i, embedded_purpose in enumerate(tcf_contents.tcf_systems[0].purposes):
            assert embedded_purpose.legal_bases == [legal_bases[i]]
            assert embedded_purpose.id == list(MAPPED_PURPOSES.values())[i].id

    def test_duplicate_data_uses_on_system(self, tcf_system, db):
        """Contrived test (since UI enforces unique data uses on systems), that adds the same data use to multiple privacy declarations.
        Assert that this doesn't create duplicate purposes
        """
        get_tcf_contents.cache_clear()

        for privacy_decl in tcf_system.privacy_declarations:
            privacy_decl.data_use = "marketing.advertising.profiling"
            privacy_decl.save(db)

        tcf_contents = get_tcf_contents(db)
        assert len(tcf_contents.tcf_purposes) == 1
        assert tcf_contents.tcf_purposes[0].id == 3
        assert len(tcf_contents.tcf_purposes[0].vendors) == 1
        assert tcf_contents.tcf_purposes[0].vendors[0].name == tcf_system.name
        assert len(tcf_contents.tcf_purposes[0].systems) == 0

        assert len(tcf_contents.tcf_vendors) == 1
        assert tcf_contents.tcf_vendors[0].name == tcf_system.name
        assert len(tcf_contents.tcf_vendors[0].purposes) == 1
        assert tcf_contents.tcf_vendors[0].purposes[0].id == 3
        assert tcf_contents.tcf_special_purposes == []
        assert tcf_contents.tcf_features == []
        assert tcf_contents.tcf_special_features == []
        assert tcf_contents.tcf_systems == []

    def test_add_different_data_uses_that_correspond_to_same_purpose(
        self, tcf_system, db
    ):
        """Add different data uses to the same system that correspond to the same purpose
        Assert that this doesn't create duplicate purposes
        """
        get_tcf_contents.cache_clear()

        new_uses = [
            "marketing.advertising.first_party.contextual",
            "marketing.advertising.frequency_capping",
        ]
        new_legal_bases = ["Consent", "Public interest"]
        for i, privacy_decl in enumerate(tcf_system.privacy_declarations):
            privacy_decl.data_use = new_uses[i]
            privacy_decl.legal_basis_for_processing = new_legal_bases[i]
            privacy_decl.save(db)

        tcf_contents = get_tcf_contents(db)
        assert len(tcf_contents.tcf_purposes) == 1
        assert tcf_contents.tcf_purposes[0].id == 2
        assert tcf_contents.tcf_purposes[0].legal_bases == [
            "Consent",
            "Public interest",
        ]
        assert len(tcf_contents.tcf_purposes[0].vendors) == 1
        assert tcf_contents.tcf_purposes[0].vendors[0].name == tcf_system.name
        assert len(tcf_contents.tcf_purposes[0].systems) == 0

        assert len(tcf_contents.tcf_vendors) == 1
        assert tcf_contents.tcf_vendors[0].name == tcf_system.name
        assert len(tcf_contents.tcf_vendors[0].purposes) == 1
        assert tcf_contents.tcf_vendors[0].purposes[0].id == 2
        assert tcf_contents.tcf_vendors[0].purposes[0].legal_bases == [
            "Consent",
            "Public interest",
        ]

        assert tcf_contents.tcf_special_purposes == []
        assert tcf_contents.tcf_features == []
        assert tcf_contents.tcf_special_features == []
        assert tcf_contents.tcf_systems == []

    def test_add_same_data_use_to_different_systems(
        self, system_with_no_uses, system, db
    ):
        """Add same data uses to different systems. Assert this doesn't create duplicate purposes
        One system has a legal basis, the other doesn't.  assert that the legal basis shows up on high level purposes record,
        but only shows up under the matching system > purposes record
        """
        get_tcf_contents.cache_clear()

        system.name = "System A"
        system.save(db)

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

        decl = system.privacy_declarations[0]
        decl.data_use = "marketing.advertising.first_party.targeted"
        decl.save(db)

        tcf_contents = get_tcf_contents(db)
        assert len(tcf_contents.tcf_purposes) == 1
        assert tcf_contents.tcf_purposes[0].id == 4
        assert tcf_contents.tcf_purposes[0].legal_bases == [
            "Consent",
        ]
        assert len(tcf_contents.tcf_purposes[0].vendors) == 0

        assert len(tcf_contents.tcf_purposes[0].systems) == 2
        assert tcf_contents.tcf_purposes[0].systems[0].name == "System A"
        assert tcf_contents.tcf_purposes[0].systems[1].name == "System B"

        assert len(tcf_contents.tcf_purposes) == 1
        assert tcf_contents.tcf_purposes[0].legal_bases == ["Consent"]
        assert tcf_contents.tcf_purposes[0].id == 4

        assert tcf_contents.tcf_special_purposes == []
        assert tcf_contents.tcf_features == []
        assert tcf_contents.tcf_special_features == []
        assert len(tcf_contents.tcf_vendors) == 0

        assert len(tcf_contents.tcf_systems) == 2
        assert tcf_contents.tcf_systems[0].name == "System A"
        assert len(tcf_contents.tcf_systems[0].purposes) == 1
        assert tcf_contents.tcf_systems[0].purposes[0].id == 4
        assert (
            tcf_contents.tcf_systems[0].purposes[0].legal_bases == []
        )  # System A has no legal basis

        assert tcf_contents.tcf_systems[1].name == "System B"
        assert len(tcf_contents.tcf_systems[1].purposes) == 1
        assert tcf_contents.tcf_systems[1].purposes[0].id == 4
        assert tcf_contents.tcf_systems[1].purposes[0].legal_bases == ["Consent"]
