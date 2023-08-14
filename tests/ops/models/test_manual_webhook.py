import pytest

from fides.api.models.manual_webhook import AccessManualWebhook


class TestManualWebhook:
    def test_manual_webhook(
        self, integration_manual_webhook_config, access_manual_webhook
    ):
        assert (
            integration_manual_webhook_config.access_manual_webhook
            == access_manual_webhook
        )
        assert (
            access_manual_webhook.connection_config == integration_manual_webhook_config
        )

    def test_get_enabled_no_enabled_webhooks(self, db):
        assert AccessManualWebhook.get_enabled(db) == []

    def test_get_enabled_webhooks(self, db, access_manual_webhook):
        assert AccessManualWebhook.get_enabled(db) == [access_manual_webhook]

    @pytest.mark.usefixtures("access_manual_webhook")
    def test_get_enabled_webhooks_connection_config_disabled(
        self, db, integration_manual_webhook_config
    ):
        integration_manual_webhook_config.disabled = True
        integration_manual_webhook_config.save(db)
        assert AccessManualWebhook.get_enabled(db) == []

    def test_get_enabled_webhooks_connection_config_fields_is_none(
        self, db, access_manual_webhook
    ):
        access_manual_webhook.fields = None
        access_manual_webhook.save(db)
        assert AccessManualWebhook.get_enabled(db) == []

    def test_get_enabled_webhooks_connection_config_fields_is_empty(
        self, db, access_manual_webhook
    ):
        access_manual_webhook.fields = []
        access_manual_webhook.save(db)
        assert AccessManualWebhook.get_enabled(db) == []
