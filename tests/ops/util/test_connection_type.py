import pytest

from fides.api.ops.models.connectionconfig import ConnectionType
from fides.api.ops.schemas.connection_configuration.connection_config import SystemType
from fides.api.ops.service.connectors.saas.connector_registry_service import (
    load_registry,
    registry_file,
)
from fides.api.ops.util.connection_type import get_connection_types
from fides.api.ops.util.saas_util import encode_file_contents


def test_get_connection_types():
    saas_template_registry = load_registry(registry_file)
    data = get_connection_types()
    assert (
        len(data)
        == len(ConnectionType) + len(saas_template_registry.connector_types()) - 4
    )  # there are 4 connection types that are not returned by the endpoint

    assert {
        "identifier": ConnectionType.postgres.value,
        "type": SystemType.database.value,
        "human_readable": "PostgreSQL",
        "encoded_icon": None,
    } in data
    first_saas_type = saas_template_registry.connector_types().pop()
    first_saas_template = saas_template_registry.get_connector_template(first_saas_type)
    assert {
        "identifier": first_saas_type,
        "type": SystemType.saas.value,
        "human_readable": first_saas_template.human_readable,
        "encoded_icon": encode_file_contents(first_saas_template.icon),
    } in data

    assert "saas" not in [item.identifier for item in data]
    assert "https" not in [item.identifier for item in data]
    assert "custom" not in [item.identifier for item in data]
    assert "manual" not in [item.identifier for item in data]

    assert {
        "identifier": ConnectionType.sovrn.value,
        "type": SystemType.email.value,
        "human_readable": "Sovrn",
        "encoded_icon": None,
    } in data
