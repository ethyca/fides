import json
from typing import Optional

import requests

from fidesops.common_exceptions import ClientUnsuccessfulException
from fidesops.models.connectionconfig import ConnectionConfig
from fidesops.schemas.connection_configuration.connections_secrets_https import (
    HttpsSchema,
)

from fidesops.service.client_data_strategies.abstract_client_data_strategy import (
    ClientDataStrategyResponse,
)
from fidesops.service.client_data_strategies.https_helper import (
    create_identity_parameters,
    create_authorization_headers,
)


class ClientDataDatasetStrategy:
    def __init__(self, configuration: ConnectionConfig):
        self.configuration = configuration

    def execute(self, identity: str) -> Optional[ClientDataStrategyResponse]:
        """Calls a client-defined endpoint and returns the data that it responds with"""
        config = HttpsSchema(**self.configuration.secrets or {})
        headers = create_authorization_headers(config.authorization)
        params = create_identity_parameters(identity)

        response = requests.get(url=config.url, headers=headers, params=params)
        if not response.ok:
            raise ClientUnsuccessfulException(
                status_code=response.status_code, message=response.text
            )

        return ClientDataStrategyResponse(data=json.loads(response.text)["data"])
