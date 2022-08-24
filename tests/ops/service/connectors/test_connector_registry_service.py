from fidesops.ops.service.connectors.saas.connector_registry_service import (
    ConnectorTemplate,
    load_registry,
    registry_file,
)


class TestConnectionRegistry:
    def test_get_connector_template(self):
        registry = load_registry(registry_file)

        assert "mailchimp" in registry.connector_types()

        assert registry.get_connector_template("bad_key") is None
        mailchimp_registry = registry.get_connector_template("mailchimp")

        assert mailchimp_registry == ConnectorTemplate(
            config="data/saas/config/mailchimp_config.yml",
            dataset="data/saas/dataset/mailchimp_dataset.yml",
            icon="data/saas/icon/mailchimp.svg",
        )
