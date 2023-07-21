import pytest

from fides.api.util.tcf_util import get_tcf_purposes_and_vendors
from tests.fixtures.saas.connection_template_fixtures import instantiate_connector


class TestGetTCFPurposesAndVendors:
    def test_load_tcf_data_uses_no_applicable_systems(self, db):
        get_tcf_purposes_and_vendors.cache_clear()

        purposes, vendors = get_tcf_purposes_and_vendors(db)
        assert purposes == []
        assert vendors == []

    @pytest.mark.usefixtures("system")
    def test_load_tcf_data_uses_systems_but_no_overlapping_use(self, db):
        get_tcf_purposes_and_vendors.cache_clear()

        purposes, vendors = get_tcf_purposes_and_vendors(db)
        assert purposes == []
        assert vendors == []

    @pytest.mark.usefixtures("tcf_system")
    def test_system_exists_with_tcf_data_use_but_no_official_vendor_linked(self, db):
        get_tcf_purposes_and_vendors.cache_clear()

        purposes, vendors = get_tcf_purposes_and_vendors(db)
        assert len(purposes) == 1
        assert purposes[0].id == 8
        assert vendors == []

    @pytest.mark.usefixtures("tcf_system")
    def test_system_exists_with_tcf_purpose_and_vendor(self, db, tcf_system):
        get_tcf_purposes_and_vendors.cache_clear()

        secrets = {
            "domain": "test_sendgrid_domain",
            "api_key": "test_sendgrid_api_key",
        }
        connection_config, dataset_config = instantiate_connector(
            db,
            "sendgrid",
            "secondary_sendgrid_instance",
            "Sendgrid ConnectionConfig description",
            secrets,
        )
        connection_config.system_id = tcf_system.id
        connection_config.save(db)

        purposes, systems = get_tcf_purposes_and_vendors(db)
        assert len(purposes) == 1
        assert purposes[0].id == 8
        assert purposes[0].data_uses == ["analytics.reporting.content_performance"]
        assert purposes[0].vendors == ["sendgrid"]

        assert len(systems) == 1
        assert systems[0].id == "sendgrid"
        assert len(systems[0].purposes) == 1
        assert systems[0].purposes[0].id == 8

    @pytest.mark.usefixtures("tcf_system")
    def test_system_matches_subset_of_purpose_data_uses(self, db, tcf_system):
        get_tcf_purposes_and_vendors.cache_clear()

        secrets = {
            "domain": "test_sendgrid_domain",
            "api_key": "test_sendgrid_api_key",
        }
        connection_config, dataset_config = instantiate_connector(
            db,
            "sendgrid",
            "secondary_sendgrid_instance",
            "Sendgrid ConnectionConfig description",
            secrets,
        )
        connection_config.system_id = tcf_system.id
        connection_config.save(db)

        tcf_system.privacy_declarations[
            0
        ].data_use = "marketing.advertising.first_party.contextual"
        tcf_system.privacy_declarations[0].save(db)

        purposes, systems = get_tcf_purposes_and_vendors(db)
        assert len(purposes) == 1
        assert purposes[0].id == 2
        assert purposes[0].data_uses == [
            "marketing.advertising.first_party.contextual",
            "marketing.advertising.frequency_capping",
            "marketing.advertising.negative_targeting",
        ]
        assert purposes[0].vendors == ["sendgrid"]

        assert len(systems) == 1
        assert systems[0].id == "sendgrid"
        assert len(systems[0].purposes) == 1
        assert systems[0].purposes[0].id == 2
