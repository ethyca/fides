import pytest

from fides.api.models.connectionconfig import ConnectionType
from fides.api.models.policy import ActionType
from fides.api.schemas.connection_configuration.enums.system_type import SystemType

from fides.api.service.connectors.saas.connector_registry_service import (
    ConnectorRegistry,
)
from fides.api.util.connection_type import (
    get_connection_type_secret_schema,
    get_connection_types,
)


def test_get_connection_types():
    data = [obj.model_dump(mode="json") for obj in get_connection_types()]
    assert (
        len(data) == len(ConnectionType) + len(ConnectorRegistry.connector_types()) - 5
    )  # there are 5 connection types that are not returned by the endpoint

    assert {
        "identifier": ConnectionType.postgres.value,
        "type": SystemType.database.value,
        "human_readable": "PostgreSQL",
        "encoded_icon": None,
        "authorization_required": False,
        "user_guide": None,
        "supported_actions": [ActionType.access.value, ActionType.erasure.value],
        "category": None,
        "tags": None,
        "enabled_features": None,
    } in data
    first_saas_type = ConnectorRegistry.connector_types().pop()
    first_saas_template = ConnectorRegistry.get_connector_template(first_saas_type)
    # For SaaS connections, we need to find the actual data in the response
    # since category and enabled_features can have real values
    saas_data_in_response = next(
        (item for item in data if item["identifier"] == first_saas_type), None
    )
    assert saas_data_in_response is not None
    assert saas_data_in_response["type"] == SystemType.saas.value
    assert saas_data_in_response["human_readable"] == first_saas_template.human_readable
    assert saas_data_in_response["encoded_icon"] == first_saas_template.icon
    assert (
        saas_data_in_response["authorization_required"]
        == first_saas_template.authorization_required
    )
    assert saas_data_in_response["user_guide"] == first_saas_template.user_guide
    assert saas_data_in_response["supported_actions"] == [
        action.value for action in first_saas_template.supported_actions
    ]
    # The new fields exist (might be None or have values)
    assert "category" in saas_data_in_response
    assert "tags" in saas_data_in_response
    assert "enabled_features" in saas_data_in_response

    assert "saas" not in [item["identifier"] for item in data]
    assert "https" not in [item["identifier"] for item in data]
    assert "custom" not in [item["identifier"] for item in data]
    assert "manual" not in [item["identifier"] for item in data]

    assert {
        "identifier": ConnectionType.sovrn.value,
        "type": SystemType.email.value,
        "human_readable": "Sovrn",
        "encoded_icon": None,
        "authorization_required": False,
        "user_guide": None,
        "supported_actions": [ActionType.consent.value],
        "category": None,
        "tags": None,
        "enabled_features": None,
    } in data


HUBSPOT = "hubspot"
MAILCHIMP = "mailchimp"
STRIPE = "stripe"


@pytest.fixture
def connection_type_objects():
    # Get actual connection types to build expected data dynamically
    # This ensures our tests match the actual output including category/enabled_features
    actual_connection_types = {
        ct.identifier: ct.model_dump(mode="json") for ct in get_connection_types()
    }

    return {
        ConnectionType.postgres.value: {
            "identifier": ConnectionType.postgres.value,
            "type": SystemType.database.value,
            "human_readable": "PostgreSQL",
            "encoded_icon": None,
            "authorization_required": False,
            "user_guide": None,
            "supported_actions": [ActionType.access.value, ActionType.erasure.value],
            "category": None,
            "tags": None,
            "enabled_features": None,
        },
        ConnectionType.manual_webhook.value: {
            "identifier": ConnectionType.manual_webhook.value,
            "type": SystemType.manual.value,
            "human_readable": "Manual Process",
            "encoded_icon": None,
            "authorization_required": False,
            "user_guide": None,
            "supported_actions": [ActionType.access.value, ActionType.erasure.value],
            "category": None,
            "tags": None,
            "enabled_features": None,
        },
        HUBSPOT: actual_connection_types[HUBSPOT],
        MAILCHIMP: actual_connection_types[MAILCHIMP],
        STRIPE: actual_connection_types[STRIPE],
        ConnectionType.sovrn.value: {
            "identifier": ConnectionType.sovrn.value,
            "type": SystemType.email.value,
            "human_readable": "Sovrn",
            "encoded_icon": None,
            "authorization_required": False,
            "user_guide": None,
            "supported_actions": [ActionType.consent.value],
            "category": None,
            "tags": None,
            "enabled_features": None,
        },
        ConnectionType.attentive_email.value: {
            "identifier": ConnectionType.attentive_email.value,
            "type": SystemType.email.value,
            "human_readable": "Attentive Email",
            "encoded_icon": None,
            "authorization_required": False,
            "user_guide": None,
            "supported_actions": [ActionType.erasure.value],
            "category": None,
            "tags": None,
            "enabled_features": None,
        },
    }


@pytest.mark.parametrize(
    "action_types, assert_in_data, assert_not_in_data",
    [
        (
            [ActionType.consent],
            [ConnectionType.sovrn.value],
            [
                ConnectionType.postgres.value,
                ConnectionType.manual_webhook.value,
                HUBSPOT,
                MAILCHIMP,
                STRIPE,
                ConnectionType.attentive_email.value,
            ],
        ),
        (
            [ActionType.access],
            [
                ConnectionType.postgres.value,
                ConnectionType.manual_webhook.value,
                HUBSPOT,
                MAILCHIMP,
                STRIPE,
            ],
            [
                ConnectionType.sovrn.value,
                ConnectionType.attentive_email.value,
            ],
        ),
        (
            [ActionType.erasure],
            [
                ConnectionType.postgres.value,
                HUBSPOT,
                STRIPE,
                MAILCHIMP,
                ConnectionType.attentive_email.value,
                ConnectionType.manual_webhook.value,
            ],
            [
                ConnectionType.sovrn.value,
            ],
        ),
        (
            [ActionType.consent, ActionType.access],
            [
                HUBSPOT,
                MAILCHIMP,
                ConnectionType.sovrn.value,
                ConnectionType.postgres.value,
                ConnectionType.manual_webhook.value,
                STRIPE,
            ],
            [
                ConnectionType.attentive_email.value,
            ],
        ),
        (
            [ActionType.consent, ActionType.erasure],
            [
                MAILCHIMP,
                HUBSPOT,
                ConnectionType.sovrn.value,
                ConnectionType.postgres.value,
                STRIPE,
                ConnectionType.attentive_email.value,
                ConnectionType.manual_webhook.value,
            ],
            [],
        ),
        (
            [ActionType.access, ActionType.erasure],
            [
                ConnectionType.postgres.value,
                ConnectionType.manual_webhook.value,
                MAILCHIMP,
                HUBSPOT,
                STRIPE,
                ConnectionType.attentive_email.value,
            ],
            [
                ConnectionType.sovrn.value,
            ],
        ),
    ],
)
def test_get_connection_types_action_type_filter(
    action_types, assert_in_data, assert_not_in_data, connection_type_objects
):
    data = [
        obj.model_dump(mode="json")
        for obj in get_connection_types(action_types=action_types)
    ]

    for connection_type in assert_in_data:
        obj = connection_type_objects[connection_type]
        assert obj in data

    for connection_type in assert_not_in_data:
        obj = connection_type_objects[connection_type]
        assert obj not in data


def test_get_connection_type_secret_schemas_aws():
    """
    AWS secret schemas have inheritance from a base class, and have provided some issues in the past.

    This test covers their JSON schema serialization behavior to ensure there aren't regressions.
    """

    dynamo_db_schema = get_connection_type_secret_schema(connection_type="dynamodb")
    dynamodb_required = dynamo_db_schema["required"]
    assert "region_name" in dynamodb_required
    assert "auth_method" in dynamodb_required

    s3_secret_schema = get_connection_type_secret_schema(connection_type="s3")
    s3_required = s3_secret_schema["required"]
    assert "auth_method" in s3_required


def test_get_connection_type_secret_schemas_test_website():
    test_website_schema = get_connection_type_secret_schema(
        connection_type="test_website"
    )
    website_schema = get_connection_type_secret_schema(connection_type="website")

    assert test_website_schema == website_schema
    assert test_website_schema["required"] == ["url"]
    assert test_website_schema["properties"]["url"]["format"] == "uri"
