import json
from unittest import mock
from unittest.mock import Mock

import pytest

from fidesops.common_exceptions import ClientUnsuccessfulException
from fidesops.models.connectionconfig import (
    ConnectionConfig,
    AccessLevel,
    ConnectionType,
)
from fidesops.service.client_data_strategies.client_data_dataset_strategy import (
    ClientDataDatasetStrategy,
)


url = "url.com"
auth = "lemme in"
config = ConnectionConfig(
    name="name",
    key="Awesome API",
    connection_type="https",
    access=AccessLevel.write,
    secrets={"url": url, "authorization": auth},
)


@mock.patch(
    "fidesops.service.client_data_strategies.client_data_dataset_strategy.requests"
)
def test__execute__happy_path(mock_requests: Mock):
    identity = "test@mail.com"

    response = Mock()
    response.status_code = 200
    response_obj = {"data": {"key": "value"}}
    response.text = json.dumps(response_obj)

    mock_requests.get.return_value = response

    service_resp = ClientDataDatasetStrategy(config).execute(identity)

    kwargs = mock_requests.get.call_args_list[0].kwargs
    assert service_resp.data["key"] == "value"
    assert kwargs["url"] == url
    assert kwargs["headers"]["Authorization"] == auth
    assert kwargs["params"]["identity"] == identity


@mock.patch(
    "fidesops.service.client_data_strategies.client_data_dataset_strategy.requests"
)
def test__execute__client_fails(mock_requests: Mock):
    identity = "pig"

    response = Mock()
    response.status_code = 400
    response.text = "No"
    response.ok = False
    mock_requests.get.return_value = response

    config = ConnectionConfig(
        name="name",
        key="Awesome API",
        connection_type=ConnectionType.https,
        access=AccessLevel.write,
        secrets={"url": url, "authorization": auth},
    )

    with pytest.raises(ClientUnsuccessfulException) as exc:
        ClientDataDatasetStrategy(config).execute(identity)
        assert exc.status_code == response.status_code
        assert exc.message == response.text
