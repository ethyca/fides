import factory

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from tests.factories.base import BaseFactory


class ConnectionConfigFactory(BaseFactory):
    class Meta:
        model = ConnectionConfig

    key = factory.Sequence(lambda n: f"test_connection_{n}")
    name = factory.Sequence(lambda n: f"Test Connection {n}")
    connection_type = ConnectionType.postgres
    access = AccessLevel.read
