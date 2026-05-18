from unittest import mock
from unittest.mock import Mock, create_autospec

import pytest
from sqlalchemy.orm import Session

from fides.api.common_exceptions import MessageDispatchException
from fides.api.models.messaging import MessagingConfig
from fides.api.schemas.messaging.messaging import (
    MessagingActionType,
    MessagingServiceType,
)
from fides.api.schemas.redis_cache import Identity
from fides.api.service.messaging.messaging_providers.base import (
    BaseMessageProviderService,
)
from fides.config import FidesConfig
from fides.config.config_proxy import ConfigProxy
from fides.service.messaging.messaging_service import MessagingService


@pytest.fixture
def mock_db() -> Session:
    return create_autospec(Session)


@pytest.fixture
def mock_config() -> FidesConfig:
    return create_autospec(FidesConfig)


@pytest.fixture
def mock_config_proxy() -> ConfigProxy:
    return create_autospec(ConfigProxy)


@pytest.fixture
def messaging_service(
    mock_db: Session, mock_config: FidesConfig, mock_config_proxy: ConfigProxy
) -> MessagingService:
    return MessagingService(mock_db, mock_config, mock_config_proxy)


class TestSendTestMessage:
    @mock.patch(
        "fides.service.messaging.messaging_service.dispatch_message",
    )
    def test_delegates_to_dispatch_message(
        self, mock_dispatch, messaging_service: MessagingService
    ):
        identity = Identity(email="test@example.com")
        messaging_service.send_test_message(
            service_type=MessagingServiceType.mailgun,
            to_identity=identity,
        )
        mock_dispatch.assert_called_once_with(
            messaging_service.db,
            action_type=MessagingActionType.TEST_MESSAGE,
            to_identity=identity,
            service_type="mailgun",
        )

    @mock.patch(
        "fides.service.messaging.messaging_service.dispatch_message",
        side_effect=MessageDispatchException("Send failed"),
    )
    def test_propagates_dispatch_exception(
        self, mock_dispatch, messaging_service: MessagingService
    ):
        with pytest.raises(MessageDispatchException, match="Send failed"):
            messaging_service.send_test_message(
                service_type=MessagingServiceType.mailgun,
                to_identity=Identity(email="test@example.com"),
            )


class TestValidateProviderOnSave:
    def _make_config(self, service_type: str) -> MessagingConfig:
        config = Mock(spec=MessagingConfig)
        config.service_type = service_type
        return config

    @mock.patch("fides.service.messaging.messaging_service.get_provider_class")
    def test_returns_none_when_no_provider(
        self, mock_get_provider, messaging_service: MessagingService
    ):
        mock_get_provider.return_value = None
        result = messaging_service.validate_provider_on_save(
            self._make_config("mailgun")
        )
        assert result is None

    @mock.patch("fides.service.messaging.messaging_service.get_provider_class")
    def test_returns_none_on_successful_validation(
        self, mock_get_provider, messaging_service: MessagingService
    ):
        mock_provider_cls = Mock(spec=type)
        mock_provider_instance = Mock(spec=BaseMessageProviderService)
        mock_provider_cls.return_value = mock_provider_instance
        mock_get_provider.return_value = mock_provider_cls

        config = self._make_config("mailgun")
        result = messaging_service.validate_provider_on_save(config)

        assert result is None
        mock_provider_cls.assert_called_once_with(config)
        mock_provider_instance.validate_on_save.assert_called_once()

    @mock.patch("fides.service.messaging.messaging_service.get_provider_class")
    def test_returns_failure_reason_on_exception(
        self, mock_get_provider, messaging_service: MessagingService
    ):
        mock_provider_cls = Mock(spec=type)
        mock_provider_instance = Mock(spec=BaseMessageProviderService)
        mock_provider_instance.validate_on_save.side_effect = MessageDispatchException(
            "Bad credentials"
        )
        mock_provider_cls.return_value = mock_provider_instance
        mock_get_provider.return_value = mock_provider_cls

        result = messaging_service.validate_provider_on_save(
            self._make_config("aws_ses")
        )
        assert result == "Bad credentials"
