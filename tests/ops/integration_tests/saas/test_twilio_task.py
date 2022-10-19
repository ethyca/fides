import logging
import random

import pytest

from fides.api.ops.graph.graph import DatasetGraph
from fides.api.ops.models.privacy_request import PrivacyRequest
from fides.api.ops.schemas.redis_cache import Identity
from fides.api.ops.service.connectors import get_connector
from fides.api.ops.task import graph_task
from tests.ops.graph.graph_test_util import assert_rows_match

logger = logging.getLogger(__name__)


@pytest.mark.integration_saas
@pytest.mark.integration_twilio
def test_twilio_connection_test(twilio_connection_config) -> None:
    get_connector(twilio_connection_config).test_connection()


@pytest.mark.integration_saas
@pytest.mark.integration_twilio
@pytest.mark.asyncio
async def test_twilio_access_request_task(
    db,
    policy,
    twilio_connection_config,	
    twilio_dataset_config,	
    twilio_identity_email,	
    connection_config,	
    twilio_postgres_dataset_config,	
    twilio_postgres_db,
) -> None:
    """Full access request based on the Twilio SaaS config"""
    privacy_request = PrivacyRequest(
        id=f"test_twilio_access_request_task_{random.randint(0, 1000)}"
    )
    identity_attribute = "email"
    identity_value = twilio_identity_email
    identity_kwargs = {identity_attribute: identity_value}
    identity = Identity(**identity_kwargs)
    privacy_request.cache_identity(identity)

    dataset_name = twilio_connection_config.get_saas_config().fides_key
    merged_graph = twilio_dataset_config.get_graph()
    graph = DatasetGraph(*[merged_graph, twilio_postgres_dataset_config.get_graph()])

    v = await graph_task.run_access_request(
        privacy_request,
        policy,
        graph,
        [twilio_connection_config, connection_config],
        {"email": twilio_identity_email},
        db,
    )