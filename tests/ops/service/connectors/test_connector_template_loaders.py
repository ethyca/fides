from fides.api.ops.service.connectors.saas.connector_registry_service import (
    FileConnectorTemplateLoader,
)
from fides.api.ops.util.saas_util import encode_file_contents, load_yaml_as_string


class TestFileConnectorTemplateLoader:
    def test_file_connector_template_loader(self):
        loader = FileConnectorTemplateLoader()
        connector_templates = loader.get_connector_templates()

        assert connector_templates

        mailchimp_connector = connector_templates.get("mailchimp")
        assert mailchimp_connector

        assert mailchimp_connector.config == load_yaml_as_string(
            "data/saas/config/mailchimp_config.yml"
        )
        assert mailchimp_connector.dataset == load_yaml_as_string(
            "data/saas/dataset/mailchimp_dataset.yml"
        )
        assert mailchimp_connector.icon == encode_file_contents(
            "data/saas/icon/mailchimp.svg"
        )
        assert mailchimp_connector.human_readable == "Mailchimp"

    def test_file_connector_template_loader_connector_not_found(self):
        loader = FileConnectorTemplateLoader()
        connector_templates = loader.get_connector_templates()

        assert connector_templates.get("not_found") is None
