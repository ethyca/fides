from unittest import mock

import pytest
from starlette.testclient import TestClient

from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import ActionType
from fides.api.schemas.connection_configuration.enums.system_type import SystemType
from fides.api.service.connectors.saas.connector_registry_service import (
    ConnectorRegistry,
)
from fides.common.api.scope_registry import (
    CONNECTION_READ,
    CONNECTION_TYPE_READ,
    SAAS_CONNECTION_INSTANTIATE,
)
from fides.common.api.v1.urn_registry import (
    CONNECTION_TYPE_SECRETS,
    CONNECTION_TYPES,
    SAAS_CONNECTOR_FROM_TEMPLATE,
    V1_URL_PREFIX,
)


@pytest.mark.skip(reason="move to plus in progress")
class TestGetConnections:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy) -> str:
        return V1_URL_PREFIX + CONNECTION_TYPES + "?"

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
            "authorization_required": False,
            "user_guide": None,
            "supported_actions": [ActionType.access.value, ActionType.erasure.value],
        } in data
        first_saas_type = ConnectorRegistry.connector_types().pop()
        first_saas_template = ConnectorRegistry.get_connector_template(first_saas_type)
        assert {
            "identifier": first_saas_type,
            "type": SystemType.saas.value,
            "human_readable": first_saas_template.human_readable,
            "encoded_icon": first_saas_template.icon,
            "authorization_required": first_saas_template.authorization_required,
            "user_guide": first_saas_template.user_guide,
            "supported_actions": [
                action.value for action in first_saas_template.supported_actions
            ],
        } in data
        assert "saas" not in [item["identifier"] for item in data]
        assert "https" not in [item["identifier"] for item in data]
        assert "custom" not in [item["identifier"] for item in data]
        assert "manual" not in [item["identifier"] for item in data]

    def test_get_connection_types_size_param(
        self,
        api_client: TestClient,
        generate_auth_header,
        url,
    ) -> None:
        """Test to ensure size param works as expected since it overrides default value"""

        # ensure default size is 100 (effectively testing that here since we have > 50 connectors)
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(url, headers=auth_header)
        data = resp.json()["items"]
        assert resp.status_code == 200
        assert (
            len(data)
            == len(ConnectionType) + len(ConnectorRegistry.connector_types()) - 4
        )  # there are 4 connection types that are not returned by the endpoint
        # this value is > 50, so we've efectively tested our "default" size is
        # > than the default of 50 (it's 100!)

        # ensure specifying size works as expected
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(url + "size=50", headers=auth_header)
        data = resp.json()["items"]
        assert resp.status_code == 200
        assert (
            len(data) == 50
        )  # should be 50 items in response since we explicitly set size=50

        # ensure specifying size and page works as expected
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(url + "size=2", headers=auth_header)
        data = resp.json()["items"]
        assert resp.status_code == 200
        assert (
            len(data) == 2
        )  # should be 2 items in response since we explicitly set size=2
        page_1_response = data  # save this response for comparison below
        # now get second page
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(url + "size=2&page=2", headers=auth_header)
        data = resp.json()["items"]
        assert resp.status_code == 200
        assert len(data) == 2  # should be 2 items on second page too
        # second page should be different than first page!
        assert data != page_1_response

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
                "authorization_required": saas_template[1].authorization_required,
                "user_guide": saas_template[1].user_guide,
                "supported_actions": [
                    action.value for action in saas_template[1].supported_actions
                ],
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
                "authorization_required": saas_template[1].authorization_required,
                "user_guide": saas_template[1].user_guide,
                "supported_actions": [
                    action.value for action in saas_template[1].supported_actions
                ],
            }
            for saas_template in expected_saas_templates
        ]

        resp = api_client.get(url + f"search={search}", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()["items"]

        # 5 constant non-saas connection types match the search string
        assert len(data) == len(expected_saas_templates) + 6

        assert {
            "identifier": ConnectionType.postgres.value,
            "type": SystemType.database.value,
            "human_readable": "PostgreSQL",
            "encoded_icon": None,
            "authorization_required": False,
            "user_guide": None,
            "supported_actions": [ActionType.access.value, ActionType.erasure.value],
        } in data
        assert {
            "identifier": ConnectionType.redshift.value,
            "type": SystemType.database.value,
            "human_readable": "Amazon Redshift",
            "encoded_icon": None,
            "authorization_required": False,
            "user_guide": None,
            "supported_actions": [ActionType.access.value, ActionType.erasure.value],
        } in data
        assert {
            "identifier": ConnectionType.dynamic_erasure_email.value,
            "type": SystemType.email.value,
            "human_readable": "Dynamic Erasure Email",
            "encoded_icon": None,
            "authorization_required": False,
            "user_guide": None,
            "supported_actions": [ActionType.erasure.value],
        } in data
        for expected_data in expected_saas_data:
            assert expected_data in data, f"{expected_data} not in"

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
                "authorization_required": saas_template[1].authorization_required,
                "user_guide": saas_template[1].user_guide,
                "supported_actions": [
                    action.value for action in saas_template[1].supported_actions
                ],
            }
            for saas_template in expected_saas_types
        ]

        resp = api_client.get(url + f"search={search}", headers=auth_header)

        assert resp.status_code == 200
        data = resp.json()["items"]
        # 2 constant non-saas connection types match the search string
        assert len(data) == len(expected_saas_types) + 3
        assert {
            "identifier": ConnectionType.postgres.value,
            "type": SystemType.database.value,
            "human_readable": "PostgreSQL",
            "encoded_icon": None,
            "authorization_required": False,
            "user_guide": None,
            "supported_actions": [ActionType.access.value, ActionType.erasure.value],
        } in data

        for expected_data in expected_saas_data:
            assert expected_data in data, f"{expected_data} not in"

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
                "authorization_required": saas_template[1].authorization_required,
                "user_guide": saas_template[1].user_guide,
                "supported_actions": [
                    action.value for action in saas_template[1].supported_actions
                ],
            }
            for saas_template in expected_saas_types
        ]

        resp = api_client.get(url + f"search={search}", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()["items"]
        # 5 constant non-saas connection types match the search string
        assert len(data) == len(expected_saas_types) + 6
        assert {
            "identifier": ConnectionType.postgres.value,
            "type": SystemType.database.value,
            "human_readable": "PostgreSQL",
            "encoded_icon": None,
            "authorization_required": False,
            "user_guide": None,
            "supported_actions": [ActionType.access, ActionType.erasure],
        } in data
        assert {
            "identifier": ConnectionType.redshift.value,
            "type": SystemType.database.value,
            "human_readable": "Amazon Redshift",
            "encoded_icon": None,
            "authorization_required": False,
            "user_guide": None,
            "supported_actions": [ActionType.access, ActionType.erasure],
        } in data
        assert {
            "identifier": ConnectionType.dynamic_erasure_email.value,
            "type": SystemType.email.value,
            "human_readable": "Dynamic Erasure Email",
            "encoded_icon": None,
            "authorization_required": False,
            "user_guide": None,
            "supported_actions": [ActionType.erasure.value],
        } in data

        for expected_data in expected_saas_data:
            assert expected_data in data, f"{expected_data} not in"

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
        assert len(data) == 16

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
        assert len(data) == 4

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
                "authorization_required": False,
                "user_guide": None,
                "supported_actions": [
                    ActionType.access.value,
                    ActionType.erasure.value,
                ],
            }
        ]

    def test_search_email_type(self, api_client, generate_auth_header, url):
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])

        resp = api_client.get(url + "system_type=email", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()["items"]
        assert len(data) == 5
        assert data == [
            {
                "encoded_icon": None,
                "human_readable": "Attentive Email",
                "identifier": "attentive_email",
                "type": "email",
                "authorization_required": False,
                "user_guide": None,
                "supported_actions": [ActionType.erasure.value],
            },
            {
                "encoded_icon": None,
                "human_readable": "Dynamic Erasure Email",
                "identifier": "dynamic_erasure_email",
                "type": "email",
                "authorization_required": False,
                "user_guide": None,
                "supported_actions": [ActionType.erasure.value],
            },
            {
                "encoded_icon": None,
                "human_readable": "Generic Consent Email",
                "identifier": "generic_consent_email",
                "type": "email",
                "authorization_required": False,
                "user_guide": None,
                "supported_actions": [ActionType.consent.value],
            },
            {
                "encoded_icon": None,
                "human_readable": "Generic Erasure Email",
                "identifier": "generic_erasure_email",
                "type": "email",
                "authorization_required": False,
                "user_guide": None,
                "supported_actions": [ActionType.erasure.value],
            },
            {
                "encoded_icon": None,
                "human_readable": "Sovrn",
                "identifier": "sovrn",
                "type": "email",
                "authorization_required": False,
                "user_guide": None,
                "supported_actions": [ActionType.consent.value],
            },
        ]


DOORDASH = "doordash"
GOOGLE_ANALYTICS = "google_analytics"
MAILCHIMP_TRANSACTIONAL = "mailchimp_transactional"
SEGMENT = "segment"
STRIPE = "stripe"
ZENDESK = "zendesk"


@pytest.mark.skip(reason="move to plus in progress")
class TestGetConnectionsActionTypeParams:
    """
    Class specifically for testing the "action type" query params for the get connection types endpoint.

    This testing approach (and the fixtures) mimic what's done within `test_connection_type.py` to evaluate
    the `action_type` filtering logic.

    That test specifically tests the underlying utility that is leveraged by this endpoint.
    """

    @pytest.fixture(scope="function")
    def url(self) -> str:
        return V1_URL_PREFIX + CONNECTION_TYPES + "?"

    @pytest.fixture(scope="function")
    def url_with_params(self) -> str:
        return (
            V1_URL_PREFIX
            + CONNECTION_TYPES
            + "?consent={consent}"
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
                "authorization_required": False,
                "user_guide": None,
                "supported_actions": [
                    ActionType.access.value,
                    ActionType.erasure.value,
                ],
            },
            ConnectionType.manual_webhook.value: {
                "identifier": ConnectionType.manual_webhook.value,
                "type": SystemType.manual.value,
                "human_readable": "Manual Process",
                "encoded_icon": None,
                "authorization_required": False,
                "user_guide": None,
                "supported_actions": [
                    ActionType.access.value,
                    ActionType.erasure.value,
                ],
            },
            GOOGLE_ANALYTICS: {
                "identifier": GOOGLE_ANALYTICS,
                "type": SystemType.saas.value,
                "human_readable": google_analytics_template.human_readable,
                "encoded_icon": google_analytics_template.icon,
                "authorization_required": True,
                "user_guide": google_analytics_template.user_guide,
                "supported_actions": [
                    action.value
                    for action in google_analytics_template.supported_actions
                ],
            },
            MAILCHIMP_TRANSACTIONAL: {
                "identifier": MAILCHIMP_TRANSACTIONAL,
                "type": SystemType.saas.value,
                "human_readable": mailchimp_transactional_template.human_readable,
                "encoded_icon": mailchimp_transactional_template.icon,
                "authorization_required": False,
                "user_guide": mailchimp_transactional_template.user_guide,
                "supported_actions": [
                    action.value
                    for action in mailchimp_transactional_template.supported_actions
                ],
            },
            SEGMENT: {
                "identifier": SEGMENT,
                "type": SystemType.saas.value,
                "human_readable": segment_template.human_readable,
                "encoded_icon": segment_template.icon,
                "authorization_required": False,
                "user_guide": segment_template.user_guide,
                "supported_actions": [
                    action.value for action in segment_template.supported_actions
                ],
            },
            STRIPE: {
                "identifier": STRIPE,
                "type": SystemType.saas.value,
                "human_readable": stripe_template.human_readable,
                "encoded_icon": stripe_template.icon,
                "authorization_required": False,
                "user_guide": stripe_template.user_guide,
                "supported_actions": [
                    action.value for action in stripe_template.supported_actions
                ],
            },
            ZENDESK: {
                "identifier": ZENDESK,
                "type": SystemType.saas.value,
                "human_readable": zendesk_template.human_readable,
                "encoded_icon": zendesk_template.icon,
                "authorization_required": False,
                "user_guide": zendesk_template.user_guide,
                "supported_actions": [
                    action.value for action in zendesk_template.supported_actions
                ],
            },
            DOORDASH: {
                "identifier": DOORDASH,
                "type": SystemType.saas.value,
                "human_readable": doordash_template.human_readable,
                "encoded_icon": doordash_template.icon,
                "authorization_required": False,
                "user_guide": doordash_template.user_guide,
                "supported_actions": [
                    action.value for action in doordash_template.supported_actions
                ],
            },
            ConnectionType.sovrn.value: {
                "identifier": ConnectionType.sovrn.value,
                "type": SystemType.email.value,
                "human_readable": "Sovrn",
                "encoded_icon": None,
                "authorization_required": False,
                "user_guide": None,
                "supported_actions": [ActionType.consent.value],
            },
            ConnectionType.attentive_email.value: {
                "identifier": ConnectionType.attentive_email.value,
                "type": SystemType.email.value,
                "human_readable": "Attentive Email",
                "encoded_icon": None,
                "authorization_required": False,
                "user_guide": None,
                "supported_actions": [ActionType.erasure.value],
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
                    ConnectionType.attentive_email.value,
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
                    ConnectionType.attentive_email.value,
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
                    ConnectionType.attentive_email.value,
                ],
            ),
            (
                [ActionType.erasure],
                [
                    ConnectionType.postgres.value,
                    SEGMENT,  # segment has DPR so it is an erasure
                    STRIPE,
                    ZENDESK,
                    ConnectionType.attentive_email.value,
                    ConnectionType.manual_webhook.value,
                ],
                [
                    GOOGLE_ANALYTICS,
                    MAILCHIMP_TRANSACTIONAL,
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
                    ConnectionType.attentive_email.value,
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
                    ConnectionType.attentive_email.value,
                    ConnectionType.manual_webhook.value,
                ],
                [
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
                    ConnectionType.attentive_email.value,
                ],
                [
                    GOOGLE_ANALYTICS,
                    MAILCHIMP_TRANSACTIONAL,
                    ConnectionType.sovrn.value,
                ],
            ),
        ],
    )
    @pytest.mark.skip(reason="move to plus in progress")
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

    def test_get_connection_secret_schema_bigquery(
        self, api_client: TestClient, generate_auth_header, base_url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="bigquery"), headers=auth_header
        )
        assert resp.json() == {
            "title": "BigQuerySchema",
            "description": "Schema to validate the secrets needed to connect to BigQuery",
            "type": "object",
            "properties": {
                "keyfile_creds": {
                    "title": "Keyfile creds",
                    "description": "The contents of the key file that contains authentication credentials for a service account in GCP.",
                    "sensitive": True,
                    "allOf": [{"$ref": "#/definitions/KeyfileCreds"}],
                },
                "dataset": {
                    "title": "Default dataset",
                    "description": "The default BigQuery dataset that will be used if one isn't provided in the associated Fides datasets.",
                    "type": "string",
                },
            },
            "required": ["keyfile_creds"],
            "definitions": {
                "KeyfileCreds": {
                    "title": "KeyfileCreds",
                    "description": "Schema that holds BigQuery keyfile key/vals",
                    "type": "object",
                    "properties": {
                        "type": {"title": "Type", "type": "string"},
                        "project_id": {"title": "Project ID", "type": "string"},
                        "private_key_id": {
                            "title": "Private Key ID",
                            "type": "string",
                        },
                        "private_key": {
                            "title": "Private Key",
                            "sensitive": True,
                            "type": "string",
                        },
                        "client_email": {
                            "title": "Client Email",
                            "type": "string",
                            "format": "email",
                        },
                        "client_id": {"title": "Client ID", "type": "string"},
                        "auth_uri": {"title": "Auth URI", "type": "string"},
                        "token_uri": {"title": "Token URI", "type": "string"},
                        "auth_provider_x509_cert_url": {
                            "title": "Auth Provider X509 Cert URL",
                            "type": "string",
                        },
                        "client_x509_cert_url": {
                            "title": "Client X509 Cert URL",
                            "type": "string",
                        },
                    },
                    "required": ["project_id"],
                }
            },
        }

    def test_get_connection_secret_schema_dynamodb(
        self, api_client: TestClient, generate_auth_header, base_url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="dynamodb"), headers=auth_header
        )
        assert resp.json() == {
            "definitions": {
                "AWSAuthMethod": {
                    "enum": ["automatic", "secret_keys"],
                    "title": "AWSAuthMethod",
                    "type": "string",
                }
            },
            "description": "Schema to validate the secrets needed to connect to an Amazon "
            "DynamoDB cluster",
            "properties": {
                "auth_method": {
                    "allOf": [{"$ref": "#/definitions/AWSAuthMethod"}],
                    "description": "Determines which type of "
                    "authentication method to use "
                    "for connecting to Amazon Web "
                    "Services. Currently accepted "
                    "values are: `secret_keys` or "
                    "`automatic`.",
                    "title": "Authentication Method",
                },
                "aws_access_key_id": {
                    "description": "Part of the credentials "
                    "that provide access to "
                    "your AWS account.",
                    "title": "Access Key ID",
                    "type": "string",
                },
                "aws_assume_role_arn": {
                    "description": "If provided, the ARN "
                    "of the role that "
                    "should be assumed to "
                    "connect to AWS.",
                    "title": "Assume Role ARN",
                    "type": "string",
                },
                "aws_secret_access_key": {
                    "description": "Part of the "
                    "credentials that "
                    "provide access to "
                    "your AWS account.",
                    "sensitive": True,
                    "title": "Secret Access Key",
                    "type": "string",
                },
                "region_name": {
                    "description": "The AWS region where your "
                    "DynamoDB table is located (ex. "
                    "us-west-2).",
                    "title": "Region",
                    "type": "string",
                },
            },
            "required": ["auth_method", "region_name"],
            "title": "DynamoDBSchema",
            "type": "object",
        }

    def test_get_connection_secret_schema_mariadb(
        self, api_client: TestClient, generate_auth_header, base_url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="mariadb"), headers=auth_header
        )
        assert resp.json() == {
            "title": "MariaDBSchema",
            "description": "Schema to validate the secrets needed to connect to a MariaDB Database",
            "type": "object",
            "properties": {
                "host": {
                    "title": "Host",
                    "description": "The hostname or IP address of the server where the database is running.",
                    "type": "string",
                },
                "port": {
                    "default": 3306,
                    "title": "Port",
                    "description": "The network port number on which the server is listening for incoming connections (default: 3306).",
                    "type": "integer",
                },
                "username": {
                    "title": "Username",
                    "description": "The user account used to authenticate and access the database.",
                    "type": "string",
                },
                "password": {
                    "title": "Password",
                    "description": "The password used to authenticate and access the database.",
                    "sensitive": True,
                    "type": "string",
                },
                "dbname": {
                    "title": "Database",
                    "description": "The name of the specific database within the database server that you want to connect to.",
                    "type": "string",
                },
            },
            "required": ["host", "dbname"],
        }

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
                "host": {
                    "title": "Host",
                    "description": "The hostname or IP address of the server where the database is running.",
                    "type": "string",
                },
                "port": {
                    "default": 27017,
                    "title": "Port",
                    "description": "The network port number on which the server is listening for incoming connections (default: 27017).",
                    "type": "integer",
                },
                "username": {
                    "title": "Username",
                    "description": "The user account used to authenticate and access the database.",
                    "type": "string",
                },
                "password": {
                    "title": "Password",
                    "description": "The password used to authenticate and access the database.",
                    "sensitive": True,
                    "type": "string",
                },
                "defaultauthdb": {
                    "title": "Default Auth DB",
                    "description": "Used to specify the default authentication database.",
                    "type": "string",
                },
            },
            "required": ["host", "username", "password", "defaultauthdb"],
        }

    def test_get_connection_secret_schema_mssql(
        self, api_client: TestClient, generate_auth_header, base_url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="mssql"), headers=auth_header
        )
        assert resp.json() == {
            "title": "MicrosoftSQLServerSchema",
            "description": "Schema to validate the secrets needed to connect to a MS SQL Database\n\nconnection string takes the format:\nmssql+pymssql://[username]:[password]@[host]:[port]/[dbname]",
            "type": "object",
            "properties": {
                "host": {
                    "title": "Host",
                    "description": "The hostname or IP address of the server where the database is running.",
                    "type": "string",
                },
                "port": {
                    "default": 1433,
                    "title": "Port",
                    "description": "The network port number on which the server is listening for incoming connections (default: 1433).",
                    "type": "integer",
                },
                "username": {
                    "title": "Username",
                    "description": "The user account used to authenticate and access the database.",
                    "type": "string",
                },
                "password": {
                    "title": "Password",
                    "description": "The password used to authenticate and access the database.",
                    "sensitive": True,
                    "type": "string",
                },
                "dbname": {
                    "title": "Database",
                    "description": "The name of the specific database within the database server that you want to connect to.",
                    "type": "string",
                },
            },
            "required": ["host", "username", "password", "dbname"],
        }

    def test_get_connection_secret_schema_mysql(
        self, api_client: TestClient, generate_auth_header, base_url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="mysql"), headers=auth_header
        )
        assert resp.json() == {
            "title": "MySQLSchema",
            "description": "Schema to validate the secrets needed to connect to a MySQL Database",
            "type": "object",
            "properties": {
                "host": {
                    "title": "Host",
                    "description": "The hostname or IP address of the server where the database is running.",
                    "type": "string",
                },
                "port": {
                    "default": 3306,
                    "title": "Port",
                    "description": "The network port number on which the server is listening for incoming connections (default: 3306).",
                    "type": "integer",
                },
                "username": {
                    "title": "Username",
                    "description": "The user account used to authenticate and access the database.",
                    "type": "string",
                },
                "password": {
                    "title": "Password",
                    "description": "The password used to authenticate and access the database.",
                    "sensitive": True,
                    "type": "string",
                },
                "dbname": {
                    "title": "Database",
                    "description": "The name of the specific database within the database server that you want to connect to.",
                    "type": "string",
                },
                "ssh_required": {
                    "title": "SSH required",
                    "description": "Indicates whether an SSH tunnel is required for the connection. Enable this option if your MySQL server is behind a firewall and requires SSH tunneling for remote connections.",
                    "default": False,
                    "type": "boolean",
                },
            },
            "required": ["host", "dbname"],
        }

    def test_get_connection_secret_schema_postgres(
        self, api_client: TestClient, generate_auth_header, base_url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="postgres"), headers=auth_header
        )
        assert resp.json() == {
            "title": "PostgreSQLSchema",
            "description": "Schema to validate the secrets needed to connect to a PostgreSQL Database",
            "type": "object",
            "properties": {
                "host": {
                    "title": "Host",
                    "description": "The hostname or IP address of the server where the database is running.",
                    "type": "string",
                },
                "port": {
                    "default": 5432,
                    "title": "Port",
                    "description": "The network port number on which the server is listening for incoming connections (default: 5432).",
                    "type": "integer",
                },
                "username": {
                    "title": "Username",
                    "description": "The user account used to authenticate and access the database.",
                    "type": "string",
                },
                "password": {
                    "title": "Password",
                    "description": "The password used to authenticate and access the database.",
                    "sensitive": True,
                    "type": "string",
                },
                "dbname": {
                    "title": "Database",
                    "description": "The name of the specific database within the database server that you want to connect to.",
                    "type": "string",
                },
                "db_schema": {
                    "title": "Schema",
                    "description": "The default schema to be used for the database connection (defaults to public).",
                    "type": "string",
                },
                "ssh_required": {
                    "title": "SSH required",
                    "description": "Indicates whether an SSH tunnel is required for the connection. Enable this option if your PostgreSQL server is behind a firewall and requires SSH tunneling for remote connections.",
                    "default": False,
                    "type": "boolean",
                },
            },
            "required": ["host", "dbname"],
        }

    def test_get_connection_secret_schema_google_cloud_sql_postgres(
        self, api_client: TestClient, generate_auth_header, base_url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="google_cloud_sql_postgres"),
            headers=auth_header,
        )

        assert resp.json() == {
            "definitions": {
                "KeyfileCreds": {
                    "description": "Schema that holds Google "
                    "Cloud SQL for Postgres "
                    "keyfile key/vals",
                    "properties": {
                        "auth_provider_x509_cert_url": {
                            "title": "Auth provider X509 cert URL",
                            "type": "string",
                        },
                        "auth_uri": {"title": "Auth URI", "type": "string"},
                        "client_email": {
                            "format": "email",
                            "title": "Client Email",
                            "type": "string",
                        },
                        "client_id": {"title": "Client ID", "type": "string"},
                        "client_x509_cert_url": {
                            "title": "Client X509 cert URL",
                            "type": "string",
                        },
                        "private_key": {
                            "sensitive": True,
                            "title": "Private Key",
                            "type": "string",
                        },
                        "private_key_id": {
                            "title": "Private key ID",
                            "type": "string",
                        },
                        "project_id": {"title": "Project ID", "type": "string"},
                        "token_uri": {"title": "Token URI", "type": "string"},
                        "type": {"title": "Type", "type": "string"},
                        "universe_domain": {
                            "title": "Universe domain",
                            "type": "string",
                        },
                    },
                    "required": ["project_id", "universe_domain"],
                    "title": "KeyfileCreds",
                    "type": "object",
                }
            },
            "description": "Schema to validate the secrets needed to connect to Google "
            "Cloud SQL for Postgres",
            "properties": {
                "db_iam_user": {
                    "description": "example: "
                    "service-account@test.iam.gserviceaccount.com",
                    "title": "DB IAM user",
                    "type": "string",
                },
                "db_schema": {
                    "description": "The default schema to be used "
                    "for the database connection "
                    "(defaults to public).",
                    "title": "Schema",
                    "type": "string",
                },
                "dbname": {"title": "Database name", "type": "string"},
                "instance_connection_name": {
                    "description": "example: "
                    "friendly-tower-424214-n8:us-central1:test-ethyca",
                    "title": "Instance connection name",
                    "type": "string",
                },
                "keyfile_creds": {
                    "allOf": [{"$ref": "#/definitions/KeyfileCreds"}],
                    "description": "The contents of the key file "
                    "that contains authentication "
                    "credentials for a service "
                    "account in GCP.",
                    "sensitive": True,
                    "title": "Keyfile creds",
                },
            },
            "required": ["db_iam_user", "instance_connection_name", "keyfile_creds"],
            "title": "GoogleCloudSQLPostgresSchema",
            "type": "object",
        }

    def test_get_connection_secret_schema_redshift(
        self, api_client: TestClient, generate_auth_header, base_url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="redshift"), headers=auth_header
        )
        assert resp.json() == {
            "title": "RedshiftSchema",
            "description": "Schema to validate the secrets needed to connect to an Amazon Redshift cluster",
            "type": "object",
            "properties": {
                "host": {
                    "title": "Host",
                    "description": "The hostname or IP address of the server where the database is running.",
                    "type": "string",
                },
                "port": {
                    "default": 5439,
                    "title": "Port",
                    "description": "The network port number on which the server is listening for incoming connections (default: 5439).",
                    "type": "integer",
                },
                "user": {
                    "title": "Username",
                    "description": "The user account used to authenticate and access the database.",
                    "type": "string",
                },
                "password": {
                    "title": "Password",
                    "description": "The password used to authenticate and access the database.",
                    "sensitive": True,
                    "type": "string",
                },
                "database": {
                    "title": "Database",
                    "description": "The name of the specific database within the database server that you want to connect to.",
                    "type": "string",
                },
                "db_schema": {
                    "title": "Schema",
                    "description": "The default schema to be used for the database connection (defaults to public).",
                    "type": "string",
                },
                "ssh_required": {
                    "title": "SSH required",
                    "description": "Indicates whether an SSH tunnel is required for the connection. Enable this option if your Redshift database is behind a firewall and requires SSH tunneling for remote connections.",
                    "default": False,
                    "type": "boolean",
                },
            },
            "required": ["host", "user", "password", "database"],
        }

    def test_get_connection_secret_schema_s3(
        self, api_client: TestClient, generate_auth_header, base_url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="s3"), headers=auth_header
        )
        assert resp.json() == {
            "definitions": {
                "AWSAuthMethod": {
                    "enum": ["automatic", "secret_keys"],
                    "title": "AWSAuthMethod",
                    "type": "string",
                }
            },
            "description": "Schema to validate the secrets needed to connect to Amazon S3",
            "properties": {
                "auth_method": {
                    "allOf": [{"$ref": "#/definitions/AWSAuthMethod"}],
                    "description": "Determines which type of "
                    "authentication method to use "
                    "for connecting to Amazon Web "
                    "Services. Currently accepted "
                    "values are: `secret_keys` or "
                    "`automatic`.",
                    "title": "Authentication Method",
                },
                "aws_access_key_id": {
                    "description": "Part of the credentials "
                    "that provide access to "
                    "your AWS account.",
                    "title": "Access Key ID",
                    "type": "string",
                },
                "aws_assume_role_arn": {
                    "description": "If provided, the ARN "
                    "of the role that "
                    "should be assumed to "
                    "connect to AWS.",
                    "title": "Assume Role ARN",
                    "type": "string",
                },
                "aws_secret_access_key": {
                    "description": "Part of the "
                    "credentials that "
                    "provide access to "
                    "your AWS account.",
                    "sensitive": True,
                    "title": "Secret Access Key",
                    "type": "string",
                },
            },
            "required": ["auth_method"],
            "title": "S3Schema",
            "type": "object",
        }

    def test_get_connection_secret_schema_rds_mysql(
        self, api_client: TestClient, generate_auth_header, base_url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="rds_mysql"), headers=auth_header
        )
        assert resp.json() == {
            "definitions": {
                "AWSAuthMethod": {
                    "enum": ["automatic", "secret_keys"],
                    "title": "AWSAuthMethod",
                    "type": "string",
                }
            },
            "description": "Schema to validate the secrets needed to connect to a RDS "
            "MySQL Database",
            "properties": {
                "auth_method": {
                    "allOf": [{"$ref": "#/definitions/AWSAuthMethod"}],
                    "description": "Determines which type of "
                    "authentication method to use "
                    "for connecting to Amazon Web "
                    "Services. Currently accepted "
                    "values are: `secret_keys` or "
                    "`automatic`.",
                    "title": "Authentication Method",
                },
                "aws_access_key_id": {
                    "description": "Part of the credentials "
                    "that provide access to "
                    "your AWS account.",
                    "title": "Access Key ID",
                    "type": "string",
                },
                "aws_assume_role_arn": {
                    "description": "If provided, the ARN "
                    "of the role that "
                    "should be assumed to "
                    "connect to AWS.",
                    "title": "Assume Role ARN",
                    "type": "string",
                },
                "aws_secret_access_key": {
                    "description": "Part of the "
                    "credentials that "
                    "provide access to "
                    "your AWS account.",
                    "sensitive": True,
                    "title": "Secret Access Key",
                    "type": "string",
                },
                "region": {
                    "description": "The AWS region where the RDS "
                    "instances are located.",
                    "title": "Region",
                    "type": "string",
                },
                "db_username": {
                    "default": "fides_service_user",
                    "description": "The user account used to "
                    "authenticate and access the "
                    "databases.",
                    "title": "DB Username",
                    "type": "string",
                },
            },
            "required": ["auth_method", "region"],
            "title": "RDSMySQLSchema",
            "type": "object",
        }

    def test_get_connection_secret_schema_rds_postgres(
        self, api_client: TestClient, generate_auth_header, base_url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="rds_postgres"), headers=auth_header
        )
        assert resp.json() == {
            "definitions": {
                "AWSAuthMethod": {
                    "enum": ["automatic", "secret_keys"],
                    "title": "AWSAuthMethod",
                    "type": "string",
                }
            },
            "description": "Schema to validate the secrets needed to connect to a RDS "
            "Postgres Database",
            "properties": {
                "auth_method": {
                    "allOf": [{"$ref": "#/definitions/AWSAuthMethod"}],
                    "description": "Determines which type of "
                    "authentication method to use "
                    "for connecting to Amazon Web "
                    "Services. Currently accepted "
                    "values are: `secret_keys` or "
                    "`automatic`.",
                    "title": "Authentication Method",
                },
                "aws_access_key_id": {
                    "description": "Part of the credentials "
                    "that provide access to "
                    "your AWS account.",
                    "title": "Access Key ID",
                    "type": "string",
                },
                "aws_assume_role_arn": {
                    "description": "If provided, the ARN "
                    "of the role that "
                    "should be assumed to "
                    "connect to AWS.",
                    "title": "Assume Role ARN",
                    "type": "string",
                },
                "aws_secret_access_key": {
                    "description": "Part of the "
                    "credentials that "
                    "provide access to "
                    "your AWS account.",
                    "sensitive": True,
                    "title": "Secret Access Key",
                    "type": "string",
                },
                "region": {
                    "description": "The AWS region where the RDS "
                    "instances are located.",
                    "title": "Region",
                    "type": "string",
                },
                "db_username": {
                    "default": "fides_service_user",
                    "description": "The user account used to "
                    "authenticate and access the "
                    "databases.",
                    "title": "DB Username",
                    "type": "string",
                },
            },
            "required": ["auth_method", "region"],
            "title": "RDSPostgresSchema",
            "type": "object",
        }

    def test_get_connection_secret_schema_snowflake(
        self, api_client: TestClient, generate_auth_header, base_url
    ) -> None:
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="snowflake"), headers=auth_header
        )
        assert resp.json() == {
            "title": "SnowflakeSchema",
            "description": "Schema to validate the secrets needed to connect to Snowflake",
            "type": "object",
            "properties": {
                "account_identifier": {
                    "title": "Account Name",
                    "description": "The unique identifier for your Snowflake account.",
                    "type": "string",
                },
                "user_login_name": {
                    "title": "Username",
                    "description": "The user account used to authenticate and access the database.",
                    "type": "string",
                },
                "password": {
                    "title": "Password",
                    "description": "The password used to authenticate and access the database. You can use a password or a private key, but not both.",
                    "sensitive": True,
                    "type": "string",
                },
                "private_key": {
                    "description": "The private key used to authenticate and access the database. If a `private_key_passphrase` is also provided, it is assumed to be encrypted; otherwise, it is assumed to be unencrypted.",
                    "sensitive": True,
                    "title": "Private key",
                    "type": "string",
                },
                "private_key_passphrase": {
                    "description": "The passphrase used for the encrypted private key.",
                    "sensitive": True,
                    "title": "Passphrase",
                    "type": "string",
                },
                "warehouse_name": {
                    "title": "Warehouse",
                    "description": "The name of the Snowflake warehouse where your queries will be executed.",
                    "type": "string",
                },
                "database_name": {
                    "title": "Database",
                    "description": "The name of the Snowflake database you want to connect to.",
                    "type": "string",
                },
                "schema_name": {
                    "title": "Schema",
                    "description": "The name of the Snowflake schema within the selected database.",
                    "type": "string",
                },
                "role_name": {
                    "title": "Role",
                    "description": "The Snowflake role to assume for the session, if different than Username.",
                    "type": "string",
                },
            },
            "required": [
                "account_identifier",
                "user_login_name",
                "warehouse_name",
                "database_name",
                "schema_name",
            ],
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
            "type": "object",
            "properties": {
                "domain": {
                    "title": "Domain",
                    "description": "Your HubSpot domain",
                    "default": "api.hubapi.com",
                    "sensitive": False,
                    "type": "string",
                },
                "private_app_token": {
                    "title": "Private app token",
                    "description": "Your HubSpot Private Apps access token",
                    "sensitive": True,
                    "type": "string",
                },
            },
            "required": ["private_app_token"],
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

    def test_get_connection_secrets_attentive(
        self, api_client: TestClient, generate_auth_header, base_url
    ):
        auth_header = generate_auth_header(scopes=[CONNECTION_TYPE_READ])
        resp = api_client.get(
            base_url.format(connection_type="attentive_email"), headers=auth_header
        )
        assert resp.status_code == 200

        assert resp.json() == {
            "additionalProperties": False,
            "properties": {
                "third_party_vendor_name": {
                    "default": "Attentive Email",
                    "title": "Third Party Vendor Name",
                    "type": "string",
                },
                "recipient_email_address": {
                    "default": "privacy@attentive.com",
                    "format": "email",
                    "title": "Recipient Email Address",
                    "type": "string",
                },
                "test_email_address": {
                    "title": "Test Email Address",
                    "format": "email",
                    "type": "string",
                },
                "advanced_settings": {
                    "default": {
                        "identity_types": {"email": True, "phone_number": False}
                    },
                    "allOf": [{"$ref": "#/definitions/AdvancedSettings"}],
                },
            },
            "title": "AttentiveSchema",
            "type": "object",
            "definitions": {
                "AdvancedSettings": {
                    "properties": {
                        "identity_types": {"$ref": "#/definitions/IdentityTypes"}
                    },
                    "required": ["identity_types"],
                    "title": "AdvancedSettings",
                    "type": "object",
                },
                "IdentityTypes": {
                    "properties": {
                        "email": {"title": "Email", "type": "boolean"},
                        "phone_number": {"title": "Phone Number", "type": "boolean"},
                    },
                    "required": ["email", "phone_number"],
                    "title": "IdentityTypes",
                    "type": "object",
                },
            },
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
        # extra values should be permitted, but the system should return an error if there are missing fields.
        assert (
            resp.json()["detail"][0]["msg"]
            == "Value error, mailchimp_schema must be supplied all of: [domain, username, api_key]."
        )
        assert resp.json()["detail"][0]["type"] == "value_error"

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
        # names don't have to be unique
        assert resp.status_code == 200

    def test_create_connection_from_template_without_supplying_connection_key(
        self, db, generate_auth_header, api_client, base_url
    ):
        auth_header = generate_auth_header(scopes=[SAAS_CONNECTION_INSTANTIATE])
        instance_key = "secondary_mailchimp_instance"
        request_body = {
            "instance_key": instance_key,
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

        assert connection_config.key == instance_key
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
        assert resp.json()["detail"][0]["loc"] == ["body", "instance_key"]
        assert (
            resp.json()["detail"][0]["msg"]
            == "Value error, FidesKeys must only contain alphanumeric characters, '.', '_', '<', '>' or '-'. Value provided: < this is an invalid key! >"
        )
        assert resp.json()["detail"][0]["type"] == "value_error"

    @mock.patch(
        "fides.api.api.v1.endpoints.saas_config_endpoints.upsert_dataset_config_from_template"
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
        assert connection_data["secrets"]["api_key"] == "**********"

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
