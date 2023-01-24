import random
import time

import pytest
import requests

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from fides.api.ops.task.graph_task import get_cached_data_for_erasures
from fides.core.config import get_config
from tests.ops.graph.graph_test_util import assert_rows_match

CONFIG = get_config()


@pytest.mark.integration_saas
@pytest.mark.integration_kustomer
def test_kustomer_connection_test(kustomer_connection_config) -> None:
    get_connector(kustomer_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_kustomer
@pytest.mark.asyncio
async def test_kustomer_access_request_task(
    db,
    policy,
    kustomer_connection_config,
    kustomer_dataset_config,
    kustomer_identity_email,
) -> None:
    """Full access request based on the kustomer SaaS config"""

    privacy_request = PrivacyRequest(
        id=f"test_kustomer_access_request_task_{random.randint(0, 1000)}"
    )
    identity = Identity(**{"email": kustomer_identity_email})
    privacy_request.cache_identity(identity)

    dataset_name = kustomer_connection_config.get_saas_config().fides_key
    merged_graph = kustomer_dataset_config.get_graph()
    graph = DatasetGraph(merged_graph)

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [kustomer_connection_config],
        {"email": kustomer_identity_email},
        db,
    )


    assert_rows_match(
        v[f"{dataset_name}:customers"],
        min_size=1,
        keys=[
            "name",
            "company",
            "externalId",
            "username",
            "signedUpAt",
            "lastActivityAt",
            "lastCustomerActivityAt",
            "lastSeenAt",
            "avatarUrl",
            "externalIds",
            "sharedExternalIds",
            "emails",
            "sharedEmails",
            "phones",
            "sharedPhones",
            "whatsapps",
            "facebookIds",
            "instagramIds",
            "socials",
            "sharedSocials",
            "urls",
            "locations",
            "locale",
            "timeZone",
            "tags",
            "sentiment",
            "custom",
            "birthdayAt",
            "gender",
            "createdAt",
            "importedAt",
            "rev",
            "defaultLang",
        ],
    )

        # verify we only returned data for our identity email
    assert v[f"{dataset_name}:customers"][0]["email"] == kustomer_identity_email

