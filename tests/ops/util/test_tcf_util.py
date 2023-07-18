import pytest
from sqlalchemy.orm import Session

from fides.api.models.sql_models import PrivacyDeclaration
from fides.api.util.tcf_util import load_tcf_data_uses
from tests.fixtures.saas.connection_template_fixtures import instantiate_connector


class TestLoadTCFDataUses:
    def test_load_tcf_data_uses_no_applicable_systems(self, db):
        load_tcf_data_uses.cache_clear()

        data_uses, systems = load_tcf_data_uses(db)
        assert data_uses == []
        assert systems == []

    @pytest.mark.usefixtures("system")
    def test_load_tcf_data_uses_systems_but_no_overlapping_use(self, db):
        load_tcf_data_uses.cache_clear()

        data_uses, systems = load_tcf_data_uses(db)
        assert data_uses == []
        assert systems == []

    @pytest.mark.usefixtures("tcf_system")
    def test_system_exists_with_tcf_data_use_but_no_official_vendor_linked(self, db):
        load_tcf_data_uses.cache_clear()

        data_uses, systems = load_tcf_data_uses(db)
        assert len(data_uses) == 1
        assert data_uses[0].id == "analytics.reporting.content_performance"
        assert systems == []

    @pytest.mark.usefixtures("tcf_system")
    def test_system_exists_with_tcf_data_use_and_vendor(self, db, tcf_system):
        load_tcf_data_uses.cache_clear()

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

        data_uses, systems = load_tcf_data_uses(db)
        assert len(data_uses) == 1
        assert data_uses[0].id == "analytics.reporting.content_performance"

        assert len(systems) == 1
        assert systems[0].id == "sendgrid"
        assert len(systems[0].data_uses) == 1
        assert systems[0].data_uses[0].id == "analytics.reporting.content_performance"

    def test_system_data_use_is_parent_of_tcf_data_use(self, db, system):
        """Add an 'essential' data use to the system.  This is a parent of one of the TCF data uses,
        but that relationship is not applicable here"""
        load_tcf_data_uses.cache_clear()

        privacy_declaration = PrivacyDeclaration.create(
            db=db,
            data={
                "name": "Collect data for content performance",
                "system_id": system.id,
                "data_categories": ["user.device.cookie_id"],
                "data_use": "essential",
                "data_qualifier": "aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
                "data_subjects": ["customer"],
                "dataset_references": None,
                "egress": None,
                "ingress": None,
            },
        )
        data_uses, systems = load_tcf_data_uses(db)
        assert data_uses == []
        assert systems == []

        privacy_declaration.delete(db)

    def test_tcf_data_use_is_parent_of_system_data_use(self, db, system):
        """Add a fictitious 'personalize.profiling.operations' data use to the system.  This is a child of one of the TCF data uses,
        which makes it applicable here."""
        load_tcf_data_uses.cache_clear()

        privacy_declaration = PrivacyDeclaration.create(
            db=db,
            data={
                "name": "Collect data for content performance",
                "system_id": system.id,
                "data_categories": ["user.device.cookie_id"],
                "data_use": "analytics.reporting.content_performance.more_detailed_use",
                "data_qualifier": "aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
                "data_subjects": ["customer"],
                "dataset_references": None,
                "egress": None,
                "ingress": None,
            },
        )

        privacy_declaration_two = PrivacyDeclaration.create(
            db=db,
            data={
                "name": "Collect data for content performance",
                "system_id": system.id,
                "data_categories": ["user.device.cookie_id"],
                "data_use": "analytics.reporting.content_performance.other_breakdown",
                "data_qualifier": "aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
                "data_subjects": ["customer"],
                "dataset_references": None,
                "egress": None,
                "ingress": None,
            },
        )

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
        connection_config.system_id = system.id
        connection_config.save(db)

        data_uses, systems = load_tcf_data_uses(db)
        assert len(data_uses) == 1
        assert data_uses[0].id == "analytics.reporting.content_performance"

        assert len(systems) == 1
        assert systems[0].id == "sendgrid"
        assert len(systems[0].data_uses) == 1
        assert systems[0].data_uses[0].id == "analytics.reporting.content_performance"

        privacy_declaration.delete(db)
        privacy_declaration_two.delete(db)
