from unittest import mock
from unittest.mock import Mock

import pytest

from fidesops.common_exceptions import ClientUnsuccessfulException
from fidesops.models.connectionconfig import (
    ConnectionConfig,
    AccessLevel,
    ConnectionType,
)
from fidesops.service.client_data_strategies.client_data_event_strategy import (
    ClientDataEventStrategy,
)

url = "url.com"
auth = "lemme in"
config = ConnectionConfig(
    name="name",
    key="Awesome API",
    connection_type=ConnectionType.https,
    access=AccessLevel.write,
    secrets={"url": url, "authorization": auth},
)


@mock.patch(
    "fidesops.service.client_data_strategies.client_data_event_strategy.requests"
)
def test_execute_happy_path(mock_requests: Mock):
    identity = "test@mail.com"

    response = Mock()
    response.status_code = 200
    mock_requests.get.return_value = response

    ClientDataEventStrategy(config).execute(identity)

    kwargs = mock_requests.get.call_args_list[0].kwargs
    assert kwargs["url"] == url
    assert kwargs["headers"]["Authorization"] == auth
    assert kwargs["params"]["identity"] == identity


@mock.patch(
    "fidesops.service.client_data_strategies.client_data_event_strategy.requests"
)
def test_execute_client_error(mock_requests: Mock):
    identity = "test@mail.com"

    response = Mock()
    response.status_code = 403
    response.ok = False
    mock_requests.get.return_value = response

    with pytest.raises(ClientUnsuccessfulException) as exc:
        ClientDataEventStrategy(config).execute(identity)
        assert exc.status_code == response.status_code
