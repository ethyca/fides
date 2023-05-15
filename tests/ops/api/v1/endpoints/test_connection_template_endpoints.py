from typing import List, Set
from unittest import mock

import pytest
from starlette.testclient import TestClient

from fides.api.ops.api.v1.scope_registry import (
    CONNECTION_READ,
    CONNECTION_TYPE_READ,
    SAAS_CONNECTION_INSTANTIATE,
)
from fides.api.ops.api.v1.urn_registry import (
    CONNECTION_TYPE_SECRETS,
    CONNECTION_TYPES,
    SAAS_CONNECTOR_FROM_TEMPLATE,
    V1_URL_PREFIX,
)
from fides.api.ops.models.client import ClientDetail
from fides.api.ops.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.ops.models.datasetconfig import DatasetConfig
from fides.api.ops.models.policy import ActionType
from fides.api.ops.schemas.connection_configuration.connection_config import SystemType
from fides.api.ops.service.connectors.saas.connector_registry_service import (
    ConnectorRegistry,
)


class TestGetConnections:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy) -> str:
        return V1_URL_PREFIX + CONNECTION_TYPES + "?size=100&"

    def test_get_connection_types_not_authenticated(self, api_client, url):
        resp = api_client.get(url, headers={})
        assert resp.status_code == 401

    def test_get_connection_types_forbidden(
        self, api_client, url, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(url, headers=auth_header)
        assert resp.status_code == 403

    def test_get_connection_types(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(url, headers=auth_header)
        data = resp.json()["items"]
        assert resp.status_code == 200
        assert (
            len(data)
            == len(ConnectionType) + len(ConnectorRegistry.connector_types()) - 4
        )  # there are 4 connection types that are not returned by the endpoint

        assert {
            "identifier": ConnectionType.postgres.value,
            "type": SystemType.database.value,
            "human_readable": "PostgreSQL",
            "encoded_icon": None,
        } in data
        first_saas_type = ConnectorRegistry.connector_types().pop()
        first_saas_template = ConnectorRegistry.get_connector_template(first_saas_type)
        assert {
            "identifier": first_saas_type,
            "type": SystemType.saas.value,
            "human_readable": first_saas_template.human_readable,
            "encoded_icon": first_saas_template.icon,
        } in data

        assert "saas" not in [item["identifier"] for item in data]
        assert "https" not in [item["identifier"] for item in data]
        assert "custom" not in [item["identifier"] for item in data]
        assert "manual" not in [item["identifier"] for item in data]

    def test_search_connection_types(
        self,
        api_client,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])

        search = "str"
        expected_saas_templates = [
            (
                connector_type,
                ConnectorRegistry.get_connector_template(connector_type),
            )
            for connector_type in ConnectorRegistry.connector_types()
            if search.lower() in connector_type.lower()
        ]
        expected_saas_data = [
            {
                "identifier": saas_template[0],
                "type": SystemType.saas.value,
                "human_readable": saas_template[1].human_readable,
                "encoded_icon": saas_template[1].icon,
            }
            for saas_template in expected_saas_templates
        ]

        resp = api_client.get(url + f"search={search}", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()["items"]

        assert len(data) == len(expected_saas_templates)
        assert data[0] in expected_saas_data

        search = "re"
        expected_saas_templates = [
            (
                connector_type,
                ConnectorRegistry.get_connector_template(connector_type),
            )
            for connector_type in ConnectorRegistry.connector_types()
            if search.lower() in connector_type.lower()
        ]
        expected_saas_data = [
            {
                "identifier": saas_template[0],
                "type": SystemType.saas.value,
                "human_readable": saas_template[1].human_readable,
                "encoded_icon": saas_template[1].icon,
            }
            for saas_template in expected_saas_templates
        ]

        resp = api_client.get(url + f"search={search}", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()["items"]

        # 2 constant non-saas connection types match the search string
        assert len(data) == len(expected_saas_templates) + 2

        assert {
            "identifier": ConnectionType.postgres.value,
            "type": SystemType.database.value,
            "human_readable": "PostgreSQL",
            "encoded_icon": None,
        } in data
        assert {
            "identifier": ConnectionType.redshift.value,
            "type": SystemType.database.value,
            "human_readable": "Amazon Redshift",
            "encoded_icon": None,
        } in data
        for expected_data in expected_saas_data:
            assert expected_data in data

    def test_search_connection_types_case_insensitive(
        self, api_client, generate_auth_header, url
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])

        search = "St"
        expected_saas_types = [
            (
                connector_type,
                ConnectorRegistry.get_connector_template(connector_type),
            )
            for connector_type in ConnectorRegistry.connector_types()
            if search.lower() in connector_type.lower()
        ]
        expected_saas_data = [
            {
                "identifier": saas_template[0],
                "type": SystemType.saas.value,
                "human_readable": saas_template[1].human_readable,
                "encoded_icon": saas_template[1].icon,
            }
            for saas_template in expected_saas_types
        ]

        resp = api_client.get(url + f"search={search}", headers=auth_header)

        assert resp.status_code == 200
        data = resp.json()["items"]
        # 1 constant non-saas connection types match the search string
        assert len(data) == len(expected_saas_types) + 1
        assert {
            "identifier": ConnectionType.postgres.value,
            "type": SystemType.database.value,
            "human_readable": "PostgreSQL",
            "encoded_icon": None,
        } in data

        for expected_data in expected_saas_data:
            assert expected_data in data

        search = "Re"
        expected_saas_types = [
            (
                connector_type,
                ConnectorRegistry.get_connector_template(connector_type),
            )
            for connector_type in ConnectorRegistry.connector_types()
            if search.lower() in connector_type.lower()
        ]
        expected_saas_data = [
            {
                "identifier": saas_template[0],
                "type": SystemType.saas.value,
                "human_readable": saas_template[1].human_readable,
                "encoded_icon": saas_template[1].icon,
            }
            for saas_template in expected_saas_types
        ]

        resp = api_client.get(url + f"search={search}", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()["items"]
        # 2 constant non-saas connection types match the search string
        assert len(data) == len(expected_saas_types) + 2
        assert {
            "identifier": ConnectionType.postgres.value,
            "type": SystemType.database.value,
            "human_readable": "PostgreSQL",
            "encoded_icon": None,
        } in data
        assert {
            "identifier": ConnectionType.redshift.value,
            "type": SystemType.database.value,
            "human_readable": "Amazon Redshift",
            "encoded_icon": None,
        } in data

        for expected_data in expected_saas_data:
            assert expected_data in data

    def test_search_system_type(self, api_client, generate_auth_header, url):
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])

        resp = api_client.get(url + "system_type=nothing", headers=auth_header)
        assert resp.status_code == 422

        resp = api_client.get(url + "system_type=saas", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()["items"]
        assert len(data) == len(ConnectorRegistry.connector_types())

        resp = api_client.get(url + "system_type=database", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()["items"]
        assert len(data) == 10

    def test_search_system_type_and_connection_type(
        self,
        api_client,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])

        search = "str"
        resp = api_client.get(
            url + f"search={search}&system_type=saas", headers=auth_header
        )
        assert resp.status_code == 200
        data = resp.json()["items"]
        expected_saas_types = [
            connector_type
            for connector_type in ConnectorRegistry.connector_types()
            if search.lower() in connector_type.lower()
        ]
        assert len(data) == len(expected_saas_types)

        resp = api_client.get(
            url + "search=re&system_type=database", headers=auth_header
        )
        assert resp.status_code == 200
        data = resp.json()["items"]
        assert len(data) == 2

    def test_search_manual_system_type(self, api_client, generate_auth_header, url):
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])

        resp = api_client.get(url + "system_type=manual", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()["items"]
        assert len(data) == 1
        assert data == [
            {
                "identifier": "manual_webhook",
                "type": "manual",
                "human_readable": "Manual Process",
                "encoded_icon": None,
            }
        ]

    def test_search_email_type(self, api_client, generate_auth_header, url):
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])

        resp = api_client.get(url + "system_type=email", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()["items"]
        assert len(data) == 2
        assert data == [
            {
                "identifier": "attentive",
                "type": "email",
                "human_readable": "Attentive",
                "encoded_icon": None,
            },
            {
                "identifier": "sovrn",
                "type": "email",
                "human_readable": "Sovrn",
                "encoded_icon": None,
            },
        ]


DOORDASH = "doordash"
GOOGLE_ANALYTICS = "google_analytics"
MAILCHIMP_TRANSACTIONAL = "mailchimp_transactional"
SEGMENT = "segment"
STRIPE = "stripe"
ZENDESK = "zendesk"


class TestGetConnectionsActionTypeParams:
    """
    Class specifically for testing the "action type" query params for the get connection types endpoint.

    This testing approach (and the fixtures) mimic what's done within `test_connection_type.py` to evaluate
    the `action_type` filtering logic.

    That test specifically tests the underlying utility that is leveraged by this endpoint.
    """

    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + CONNECTION_TYPES + "?size=100&"

    @pytest.fixture(scope="function")
    def url_with_params(self) -> str:
        return (
            V1_URL_PREFIX
            + CONNECTION_TYPES
            + "?size=100"
            + "&consent={consent}"
            + "&access={access}"
            + "&erasure={erasure}"
        )

    @pytest.fixture
    def connection_type_objects(self):
        google_analytics_template = ConnectorRegistry.get_connector_template(
            GOOGLE_ANALYTICS
        )
        mailchimp_transactional_template = ConnectorRegistry.get_connector_template(
            MAILCHIMP_TRANSACTIONAL
        )
        stripe_template = ConnectorRegistry.get_connector_template("stripe")
        zendesk_template = ConnectorRegistry.get_connector_template("zendesk")
        doordash_template = ConnectorRegistry.get_connector_template(DOORDASH)
        segment_template = ConnectorRegistry.get_connector_template(SEGMENT)

        return {
            ConnectionType.postgres.value: {
                "identifier": ConnectionType.postgres.value,
                "type": SystemType.database.value,
                "human_readable": "PostgreSQL",
                "encoded_icon": None,
            },
            ConnectionType.manual_webhook.value: {
                "identifier": ConnectionType.manual_webhook.value,
                "type": SystemType.manual.value,
                "human_readable": "Manual Process",
                "encoded_icon": None,
            },
            GOOGLE_ANALYTICS: {
                "identifier": GOOGLE_ANALYTICS,
                "type": SystemType.saas.value,
                "human_readable": google_analytics_template.human_readable,
                "encoded_icon": google_analytics_template.icon,
            },
            MAILCHIMP_TRANSACTIONAL: {
                "identifier": MAILCHIMP_TRANSACTIONAL,
                "type": SystemType.saas.value,
                "human_readable": mailchimp_transactional_template.human_readable,
                "encoded_icon": mailchimp_transactional_template.icon,
            },
            SEGMENT: {
                "identifier": SEGMENT,
                "type": SystemType.saas.value,
                "human_readable": segment_template.human_readable,
                "encoded_icon": segment_template.icon,
            },
            STRIPE: {
                "identifier": STRIPE,
                "type": SystemType.saas.value,
                "human_readable": stripe_template.human_readable,
                "encoded_icon": stripe_template.icon,
            },
            ZENDESK: {
                "identifier": ZENDESK,
                "type": SystemType.saas.value,
                "human_readable": zendesk_template.human_readable,
                "encoded_icon": zendesk_template.icon,
            },
            DOORDASH: {
                "identifier": DOORDASH,
                "type": SystemType.saas.value,
                "human_readable": doordash_template.human_readable,
                "encoded_icon": doordash_template.icon,
            },
            ConnectionType.sovrn.value: {
                "identifier": ConnectionType.sovrn.value,
                "type": SystemType.email.value,
                "human_readable": "Sovrn",
                "encoded_icon": None,
            },
            ConnectionType.attentive.value: {
                "identifier": ConnectionType.attentive.value,
                "type": SystemType.email.value,
                "human_readable": "Attentive",
                "encoded_icon": None,
            },
        }

    @pytest.mark.parametrize(
        "action_types, assert_in_data, assert_not_in_data",
        [
            (
                [],  # no filters should give us all connectors
                [
                    ConnectionType.postgres.value,
                    ConnectionType.manual_webhook.value,
                    DOORDASH,
                    STRIPE,
                    ZENDESK,
                    SEGMENT,
                    ConnectionType.attentive.value,
                    GOOGLE_ANALYTICS,
                    MAILCHIMP_TRANSACTIONAL,
                    ConnectionType.sovrn.value,
                ],
                [],
            ),
            (
                [ActionType.consent],
                [GOOGLE_ANALYTICS, MAILCHIMP_TRANSACTIONAL, ConnectionType.sovrn.value],
                [
                    ConnectionType.postgres.value,
                    ConnectionType.manual_webhook.value,
                    DOORDASH,
                    STRIPE,
                    ZENDESK,
                    SEGMENT,
                    ConnectionType.attentive.value,
                ],
            ),
            (
                [ActionType.access],
                [
                    ConnectionType.postgres.value,
                    ConnectionType.manual_webhook.value,
                    DOORDASH,
                    SEGMENT,
                    STRIPE,
                    ZENDESK,
                ],
                [
                    GOOGLE_ANALYTICS,
                    MAILCHIMP_TRANSACTIONAL,
                    ConnectionType.sovrn.value,
                    ConnectionType.attentive.value,
                ],
            ),
            (
                [ActionType.erasure],
                [
                    ConnectionType.postgres.value,
                    SEGMENT,  # segment has DPR so it is an erasure
                    STRIPE,
                    ZENDESK,
                    ConnectionType.attentive.value,
                ],
                [
                    GOOGLE_ANALYTICS,
                    MAILCHIMP_TRANSACTIONAL,
                    ConnectionType.manual_webhook.value,  # manual webhook is not erasure
                    DOORDASH,  # doordash does not have erasures
                    ConnectionType.sovrn.value,
                ],
            ),
            (
                [ActionType.consent, ActionType.access],
                [
                    GOOGLE_ANALYTICS,
                    MAILCHIMP_TRANSACTIONAL,
                    ConnectionType.sovrn.value,
                    ConnectionType.postgres.value,
                    ConnectionType.manual_webhook.value,
                    DOORDASH,
                    SEGMENT,
                    STRIPE,
                    ZENDESK,
                ],
                [
                    ConnectionType.attentive.value,
                ],
            ),
            (
                [ActionType.consent, ActionType.erasure],
                [
                    GOOGLE_ANALYTICS,
                    MAILCHIMP_TRANSACTIONAL,
                    ConnectionType.sovrn.value,
                    ConnectionType.postgres.value,
                    SEGMENT,  # segment has DPR so it is an erasure
                    STRIPE,
                    ZENDESK,
                    ConnectionType.attentive.value,
                ],
                [
                    ConnectionType.manual_webhook.value,  # manual webhook is not erasure
                    DOORDASH,  # doordash does not have erasures
                ],
            ),
            (
                [ActionType.access, ActionType.erasure],
                [
                    ConnectionType.postgres.value,
                    ConnectionType.manual_webhook.value,
                    DOORDASH,
                    SEGMENT,
                    STRIPE,
                    ZENDESK,
                    ConnectionType.attentive.value,
                ],
                [
                    GOOGLE_ANALYTICS,
                    MAILCHIMP_TRANSACTIONAL,
                    ConnectionType.sovrn.value,
                ],
            ),
        ],
    )
    def test_get_connection_types_action_type_filter(
        self,
        action_types,
        assert_in_data,
        assert_not_in_data,
        connection_type_objects,
        generate_auth_header,
        api_client,
        url,
        url_with_params,
    ):
        the_url = url
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        if action_types:
            the_url = url_with_params.format(
                consent=ActionType.consent in action_types,
                access=ActionType.access in action_types,
                erasure=ActionType.erasure in action_types,
            )
        resp = api_client.get(the_url, headers=auth_header)
        data = resp.json()["items"]
        assert resp.status_code == 200

        for connection_type in assert_in_data:
            obj = connection_type_objects[connection_type]
            assert obj in data

        for connection_type in assert_not_in_data:
            obj = connection_type_objects[connection_type]
            assert obj not in data

        # now run another request, this time omitting non-specified filter params
        # rather than setting them to false explicitly. we should get identical results.
        if action_types:
            the_url = url
            if ActionType.consent in action_types:
                the_url += "consent=true&"
            if ActionType.access in action_types:
                the_url += "access=true&"
            if ActionType.erasure in action_types:
                the_url += "erasure=true&"

        resp = api_client.get(the_url, headers=auth_header)
        data = resp.json()["items"]
        assert resp.status_code == 200

        for connection_type in assert_in_data:
            obj = connection_type_objects[connection_type]
            assert obj in data

        for connection_type in assert_not_in_data:
            obj = connection_type_objects[connection_type]
            assert obj not in data


class TestGetConnectionSecretSchema:
    @pytest.fixture(scope="function")
    def base_url(self, oauth_client: ClientDetail, policy) -> str:
        return V1_URL_PREFIX + CONNECTION_TYPE_SECRETS

    def test_get_connection_secret_schema_not_authenticated(self, api_client, base_url):
        resp = api_client.get(base_url.format(connection_type="sentry"), headers={})
        assert resp.status_code == 401

    def test_get_connection_secret_schema_forbidden(
        self, api_client, base_url, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.get(
            base_url.format(connection_type="sentry"), headers=auth_header
        )
        assert resp.status_code == 403

    def test_get_connection_secret_schema_not_found(
        self, api_client: TestClient, generate_auth_header, base_url
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="connection_type_we_do_not_support"),
            headers=auth_header,
        )
        assert resp.status_code == 404
        assert (
            resp.json()["detail"]
            == "No connection type found with name 'connection_type_we_do_not_support'."
        )

    def test_get_connection_secret_schema_mongodb(
        self, api_client: TestClient, generate_auth_header, base_url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="mongodb"), headers=auth_header
        )
        assert resp.json() == {
            "title": "MongoDBSchema",
            "description": "Schema to validate the secrets needed to connect to a MongoDB Database",
            "type": "object",
            "properties": {
                "url": {"title": "Url", "type": "string"},
                "username": {"title": "Username", "type": "string"},
                "password": {"title": "Password", "type": "string"},
                "host": {"title": "Host", "type": "string"},
                "port": {"title": "Port", "type": "integer"},
                "defaultauthdb": {"title": "Defaultauthdb", "type": "string"},
            },
            "additionalProperties": False,
        }

    def test_get_connection_secret_schema_hubspot(
        self, api_client: TestClient, generate_auth_header, base_url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="hubspot"), headers=auth_header
        )

        assert resp.json() == {
            "title": "hubspot_schema",
            "description": "Hubspot secrets schema",
            "type": "object",
            "properties": {
                "private_app_token": {"title": "Private App Token", "type": "string"},
                "domain": {
                    "title": "Domain",
                    "default": "api.hubapi.com",
                    "type": "string",
                },
            },
            "required": ["private_app_token"],
            "additionalProperties": False,
        }

    def test_get_connection_secrets_manual_webhook(
        self, api_client: TestClient, generate_auth_header, base_url
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="manual_webhook"), headers=auth_header
        )
        assert resp.status_code == 200
        assert resp.json() == {
            "title": "ManualWebhookSchema",
            "description": "Secrets for manual webhooks. No secrets needed at this time.",
            "type": "object",
            "properties": {},
        }


class TestInstantiateConnectionFromTemplate:
    @pytest.fixture(scope="function")
    def base_url(self) -> str:
        return V1_URL_PREFIX + SAAS_CONNECTOR_FROM_TEMPLATE

    def test_instantiate_connection_not_authenticated(self, api_client, base_url):
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"), headers={}
        )
        assert resp.status_code == 401

    def test_instantiate_connection_wrong_scope(
        self, generate_auth_header, api_client, base_url
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_READ])
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"), headers=auth_header
        )
        assert resp.status_code == 403

    def test_instantiate_nonexistent_template(
        self, generate_auth_header, api_client, base_url
    ):
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": "test_instance_key",
            "secrets": {},
            "name": "Unsupported Connector",
            "description": "Unsupported connector description",
            "key": "unsupported_connector",
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="does_not_exist"),
            headers=auth_header,
            json=request_body,
        )
        assert resp.status_code == 404
        assert (
            resp.json()["detail"]
            == f"SaaS connector type 'does_not_exist' is not yet available in Fidesops. For a list of available SaaS connectors, refer to /connection_type."
        )

    def test_instance_key_already_exists(
        self, generate_auth_header, api_client, base_url, dataset_config
    ):
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": dataset_config.fides_key,
            "secrets": {
                "domain": "test_mailchimp_domain",
                "username": "test_mailchimp_username",
                "api_key": "test_mailchimp_api_key",
            },
            "name": "Mailchimp Connector",
            "description": "Mailchimp ConnectionConfig description",
            "key": "mailchimp_connection_config",
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"),
            headers=auth_header,
            json=request_body,
        )
        assert resp.status_code == 400
        assert (
            resp.json()["detail"]
            == f"SaaS connector instance key '{dataset_config.fides_key}' already exists."
        )

    def test_template_secrets_validation(
        self, generate_auth_header, api_client, base_url, db
    ):
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        # Secrets have one field missing, one field extra
        request_body = {
            "instance_key": "secondary_mailchimp_instance",
            "secrets": {
                "bad_mailchimp_secret_key": "bad_key",
                "username": "test_mailchimp_username",
                "api_key": "test_mailchimp_api_key",
            },
            "name": "Mailchimp Connector",
            "description": "Mailchimp ConnectionConfig description",
            "key": "mailchimp_connection_config",
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"),
            headers=auth_header,
            json=request_body,
        )

        assert resp.status_code == 422
        assert resp.json()["detail"][0] == {
            "loc": ["domain"],
            "msg": "field required",
            "type": "value_error.missing",
        }
        assert resp.json()["detail"][1] == {
            "loc": ["bad_mailchimp_secret_key"],
            "msg": "extra fields not permitted",
            "type": "value_error.extra",
        }

        connection_config = ConnectionConfig.filter(
            db=db, conditions=(ConnectionConfig.key == "mailchimp_connection_config")
        ).first()
        assert connection_config is None, "ConnectionConfig not persisted"

    def test_connection_config_key_already_exists(
        self, db, generate_auth_header, api_client, base_url, connection_config
    ):
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": "secondary_mailchimp_instance",
            "secrets": {
                "domain": "test_mailchimp_domain",
                "username": "test_mailchimp_username",
                "api_key": "test_mailchimp_api_key",
            },
            "name": connection_config.name,
            "description": "Mailchimp ConnectionConfig description",
            "key": connection_config.key,
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"),
            headers=auth_header,
            json=request_body,
        )
        assert resp.status_code == 400
        assert (
            f"Key {connection_config.key} already exists in ConnectionConfig"
            in resp.json()["detail"]
        )

    def test_connection_config_name_already_exists(
        self, db, generate_auth_header, api_client, base_url, connection_config
    ):
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": "secondary_mailchimp_instance",
            "secrets": {
                "domain": "test_mailchimp_domain",
                "username": "test_mailchimp_username",
                "api_key": "test_mailchimp_api_key",
            },
            "name": connection_config.name,
            "description": "Mailchimp ConnectionConfig description",
            "key": "brand_new_key",
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"),
            headers=auth_header,
            json=request_body,
        )
        assert resp.status_code == 400
        assert (
            f"Name {connection_config.name} already exists in ConnectionConfig"
            in resp.json()["detail"]
        )

    def test_create_connection_from_template_without_supplying_connection_key(
        self, db, generate_auth_header, api_client, base_url
    ):
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": "secondary_mailchimp_instance",
            "secrets": {
                "domain": "test_mailchimp_domain",
                "username": "test_mailchimp_username",
                "api_key": "test_mailchimp_api_key",
            },
            "name": "Mailchimp Connector",
            "description": "Mailchimp ConnectionConfig description",
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"),
            headers=auth_header,
            json=request_body,
        )
        assert resp.status_code == 200

        connection_config = ConnectionConfig.filter(
            db=db, conditions=(ConnectionConfig.name == "Mailchimp Connector")
        ).first()
        dataset_config = DatasetConfig.filter(
            db=db,
            conditions=(DatasetConfig.fides_key == "secondary_mailchimp_instance"),
        ).first()

        assert connection_config is not None
        assert dataset_config is not None

        assert connection_config.key == "mailchimp_connector"
        dataset_config.delete(db)
        connection_config.delete(db)

    def test_invalid_instance_key(self, db, generate_auth_header, api_client, base_url):
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": "< this is an invalid key! >",
            "secrets": {
                "domain": "test_mailchimp_domain",
                "username": "test_mailchimp_username",
                "api_key": "test_mailchimp_api_key",
            },
            "name": "Mailchimp Connector",
            "description": "Mailchimp ConnectionConfig description",
            "key": "mailchimp_connection_config",
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"),
            headers=auth_header,
            json=request_body,
        )
        assert resp.json()["detail"][0] == {
            "loc": ["body", "instance_key"],
            "msg": "FidesKeys must only contain alphanumeric characters, '.', '_', '<', '>' or '-'. Value provided: < this is an invalid key! >",
            "type": "value_error.fidesvalidation",
        }

    @mock.patch(
        "fides.api.ops.api.v1.endpoints.saas_config_endpoints.upsert_dataset_config_from_template"
    )
    def test_dataset_config_saving_fails(
        self, mock_create_dataset, db, generate_auth_header, api_client, base_url
    ):
        mock_create_dataset.side_effect = Exception("KeyError")

        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": "secondary_mailchimp_instance",
            "secrets": {
                "domain": "test_mailchimp_domain",
                "username": "test_mailchimp_username",
                "api_key": "test_mailchimp_api_key",
            },
            "name": "Mailchimp Connector",
            "description": "Mailchimp ConnectionConfig description",
            "key": "mailchimp_connection_config",
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"),
            headers=auth_header,
            json=request_body,
        )
        assert resp.status_code == 500
        assert (
            resp.json()["detail"]
            == "SaaS Connector could not be created from the 'mailchimp' template at this time."
        )

        connection_config = ConnectionConfig.filter(
            db=db, conditions=(ConnectionConfig.key == "mailchimp_connection_config")
        ).first()
        assert connection_config is None

        dataset_config = DatasetConfig.filter(
            db=db,
            conditions=(DatasetConfig.fides_key == "secondary_mailchimp_instance"),
        ).first()
        assert dataset_config is None

    def test_instantiate_connection_from_template(
        self, db, generate_auth_header, api_client, base_url
    ):
        connection_config = ConnectionConfig.filter(
            db=db, conditions=(ConnectionConfig.key == "mailchimp_connection_config")
        ).first()
        assert connection_config is None

        dataset_config = DatasetConfig.filter(
            db=db,
            conditions=(DatasetConfig.fides_key == "secondary_mailchimp_instance"),
        ).first()
        assert dataset_config is None

        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        request_body = {
            "instance_key": "secondary_mailchimp_instance",
            "secrets": {
                "domain": "test_mailchimp_domain",
                "username": "test_mailchimp_username",
                "api_key": "test_mailchimp_api_key",
            },
            "name": "Mailchimp Connector",
            "description": "Mailchimp ConnectionConfig description",
            "key": "mailchimp_connection_config",
        }
        resp = api_client.post(
            base_url.format(saas_connector_type="mailchimp"),
            headers=auth_header,
            json=request_body,
        )

        assert resp.status_code == 200
        assert set(resp.json().keys()) == {"connection", "dataset"}
        connection_data = resp.json()["connection"]
        assert connection_data["key"] == "mailchimp_connection_config"
        assert connection_data["name"] == "Mailchimp Connector"
        assert "secrets" not in connection_data

        dataset_data = resp.json()["dataset"]
        assert dataset_data["fides_key"] == "secondary_mailchimp_instance"

        connection_config = ConnectionConfig.filter(
            db=db, conditions=(ConnectionConfig.key == "mailchimp_connection_config")
        ).first()
        dataset_config = DatasetConfig.filter(
            db=db,
            conditions=(DatasetConfig.fides_key == "secondary_mailchimp_instance"),
        ).first()

        assert connection_config is not None
        assert dataset_config is not None
        assert connection_config.name == "Mailchimp Connector"
        assert connection_config.description == "Mailchimp ConnectionConfig description"

        assert connection_config.access == AccessLevel.write
        assert connection_config.connection_type == ConnectionType.saas
        assert connection_config.saas_config is not None
        assert connection_config.disabled is False
        assert connection_config.disabled_at is None
        assert connection_config.last_test_timestamp is None
        assert connection_config.last_test_succeeded is None

        assert dataset_config.connection_config_id == connection_config.id
        assert dataset_config.ctl_dataset_id is not None

        dataset_config.delete(db)
        connection_config.delete(db)
        dataset_config.ctl_dataset.delete(db=db)
