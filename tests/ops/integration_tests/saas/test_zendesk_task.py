import logging
from time import sleep
from typing import Any, Dict

import pydash
import pytest
import requests

from fides.api.ops.models.connectionconfig import ConnectionConfig
from fides.api.ops.models.policy import Policy
from tests.ops.integration_tests.saas.connector_runner import (
    ConnectorRunner,
    generate_random_email,
)
from tests.ops.test_helpers.vault_client import get_secrets

logger = logging.getLogger(__name__)


@pytest.mark.integration_saas
@pytest.mark.integration_zendesk
class TestZendeskConnector:
    @pytest.fixture(scope="session")
    def zendesk_secrets(self, saas_config) -> Dict[str, Any]:
        secrets = get_secrets("zendesk")
        return {
            "domain": pydash.get(saas_config, "zendesk.domain") or secrets["domain"],
            "username": pydash.get(saas_config, "zendesk.username")
            or secrets["username"],
            "api_key": pydash.get(saas_config, "zendesk.api_key") or secrets["api_key"],
            "page_size": pydash.get(saas_config, "zendesk.page_size")
            or secrets["page_size"],
        }

    @pytest.fixture(scope="session")
    def zendesk_identity_email(self, saas_config) -> str:
        secrets = get_secrets("zendesk")
        return (
            pydash.get(saas_config, "zendesk.identity_email")
            or secrets["identity_email"]
        )

    @pytest.fixture
    def zendesk_erasure_identity_email(self) -> str:
        return generate_random_email()

    @pytest.fixture
    def zendesk_erasure_data(
        self,
        zendesk_connection_config: ConnectionConfig,
        zendesk_erasure_identity_email: str,
    ) -> None:

        sleep(60)

        secrets = zendesk_connection_config.secrets
        auth = secrets["username"], secrets["api_key"]
        base_url = f"https://{secrets['domain']}"

        # user
        body = {
            "user": {
                "name": "Ethyca Test Erasure",
                "email": zendesk_erasure_identity_email,
                "verified": "true",
            }
        }

        users_response = requests.post(
            url=f"{base_url}/api/v2/users", auth=auth, json=body
        )
        user = users_response.json()["user"]
        user_id = user["id"]

        # ticket
        ticket_data = {
            "ticket": {
                "comment": {"body": "Test Comment"},
                "priority": "urgent",
                "subject": "Test Ticket",
                "requester_id": user_id,
                "submitter_id": user_id,
                "description": "Test Description",
            }
        }
        response = requests.post(
            url=f"{base_url}/api/v2/tickets", auth=auth, json=ticket_data
        )
        ticket = response.json()["ticket"]
        yield ticket, user

    @pytest.fixture
    def zendesk_runner(
        self,
        db,
        zendesk_secrets,
    ) -> ConnectorRunner:
        return ConnectorRunner(db, zendesk_secrets, "zendesk")

    def test_connection(self, zendesk_runner: ConnectorRunner):
        zendesk_runner.test_connection()

    async def test_access_request(
        self, zendesk_runner: ConnectorRunner, policy, zendesk_identity_email: str
    ):
        access_results = await zendesk_runner.access_request(
            access_policy=policy, identities={"email": zendesk_identity_email}
        )

    async def test_non_strict_erasure_request(
        self,
        zendesk_runner: ConnectorRunner,
        policy: Policy,
        erasure_policy_string_rewrite: Policy,
        zendesk_erasure_identity_email: str,
        zendesk_erasure_data,
    ):
        erasure_results = await zendesk_runner.non_strict_erasure_request(
            access_policy=policy,
            erasure_policy=erasure_policy_string_rewrite,
            identities={"email": zendesk_erasure_identity_email},
        )
