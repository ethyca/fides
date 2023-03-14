from unittest import mock


class TestErasureEmailConnectorMethods:
    pass


class TestAttentiveConnector:
    @mock.patch(
        "fides.api.ops.service.connectors.erasure_email_connector.send_single_erasure_email"
    )
    def test_test_connection_call(
        self, mock_send_email, db, test_attentive_erasure_connector
    ):
        test_attentive_erasure_connector.test_connection()
        assert mock_send_email.called
