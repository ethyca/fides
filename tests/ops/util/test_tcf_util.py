import pytest

from fides.api.schemas.tcf import EmbeddedVendor
from fides.api.util.tcf_util import get_tcf_contents
from tests.fixtures.saas.connection_template_fixtures import instantiate_connector


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

        assert tcf_contents.tcf_systems[0].id == tcf_system.fides_key
        assert tcf_contents.tcf_systems[0].name == "TCF System Test"
        assert tcf_contents.tcf_systems[0].description == "My TCF System Description"

        assert len(tcf_contents.tcf_systems[0].purposes) == 1
        assert tcf_contents.tcf_systems[0].purposes[0].id == 8
        assert tcf_contents.tcf_systems[0].has_vendor_id is False

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
        # Purposes also consolidated
        assert len(tcf_contents.tcf_vendors[0].purposes) == 1
        assert tcf_contents.tcf_vendors[0].purposes[0].id == 8
        assert tcf_contents.tcf_features == []
        assert tcf_contents.tcf_special_features == []

    @pytest.mark.usefixtures("tcf_system")
    def test_system_matches_subset_of_purpose_data_uses(self, db, tcf_system):
        get_tcf_contents.cache_clear()

        for i, decl in enumerate(tcf_system.privacy_declarations):
            if i:
                decl.data_use = "marketing.advertising.first_party.contextual"
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
        assert tcf_contents.tcf_purposes[0].vendors == [
            EmbeddedVendor(id="sendgrid", name="TCF System Test")
        ]

        assert len(tcf_contents.tcf_vendors) == 1
        assert tcf_contents.tcf_vendors[0].id == "sendgrid"
        assert len(tcf_contents.tcf_vendors[0].purposes) == 1
        assert tcf_contents.tcf_vendors[0].purposes[0].id == 2
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
        assert tcf_contents.tcf_special_purposes[0].vendors == [
            EmbeddedVendor(id="sendgrid", name="TCF System Test")
        ]

        assert len(tcf_contents.tcf_purposes) == 1

        assert len(tcf_contents.tcf_vendors) == 1
        assert tcf_contents.tcf_vendors[0].id == "sendgrid"
        assert len(tcf_contents.tcf_vendors[0].purposes) == 1
        assert tcf_contents.tcf_vendors[0].purposes[0].id == 8
        assert len(tcf_contents.tcf_vendors[0].special_purposes) == 1
        assert tcf_contents.tcf_vendors[0].special_purposes[0].id == 1
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
