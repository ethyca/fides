import pytest
from fideslang.models import Dataset

from fides.api.graph.graph import DatasetGraph
from fides.api.models.connectionconfig import ActionType
from fides.api.models.datasetconfig import convert_dataset_to_graph
from fides.api.models.privacy_request import PrivacyRequest, PrivacyRequestStatus
from fides.api.task import graph_task
from fides.api.task.graph_task import get_cached_data_for_erasures
from tests.ops.integration_tests.saas.connector_runner import dataset_config
from tests.ops.service.privacy_request.test_request_runner_service import (
    get_privacy_request_results,
)


@pytest.mark.integration
class TestEnabledActions:
    @pytest.fixture(scope="function")
    def mongo_postgres_dataset_graph(
        self,
        db,
        example_datasets,
        integration_postgres_config,
        integration_mongodb_config,
    ):
        dataset_postgres = Dataset(**example_datasets[0])
        dataset_config(db, integration_postgres_config, dataset_postgres.dict())

        graph = convert_dataset_to_graph(
            dataset_postgres, integration_postgres_config.key
        )
        dataset_mongo = Dataset(**example_datasets[1])
        dataset_config(db, integration_mongodb_config, dataset_mongo.dict())

        mongo_graph = convert_dataset_to_graph(
            dataset_mongo, integration_mongodb_config.key
        )
        dataset_graph = DatasetGraph(*[graph, mongo_graph])
        return dataset_graph

    @pytest.mark.asyncio
    async def test_access_disabled(
        self,
        db,
        policy,
        integration_postgres_config,
        integration_mongodb_config,
        mongo_postgres_dataset_graph,
    ) -> None:
        """Disable the access request for one connection config and verify the access results"""

        # disable the access action type for Postgres
        integration_postgres_config.enabled_actions = [ActionType.erasure]
        integration_postgres_config.save(db)
        privacy_request = PrivacyRequest(id="test_disable_postgres_access")

        access_results = await graph_task.run_access_request(
            privacy_request,
            policy,
            mongo_postgres_dataset_graph,
            [integration_postgres_config, integration_mongodb_config],
            {"email": "customer-1@example.com"},
            db,
        )

        # assert that only mongodb results are returned
        mongo_dataset = integration_mongodb_config.datasets[0].fides_key
        assert {key.split(":")[0] for key in access_results} == {mongo_dataset}

    @pytest.mark.asyncio
    async def test_erasure_disabled(
        self,
        db,
        policy,
        erasure_policy,
        integration_postgres_config,
        integration_mongodb_config,
        mongo_postgres_dataset_graph,
    ) -> None:
        """Disable the erasure request for one connection config and verify the erasure results"""

        # disable the erasure action type for Postgres
        integration_postgres_config.enabled_actions = [ActionType.access]
        integration_postgres_config.save(db)
        privacy_request = PrivacyRequest(id="test_disable_postgres_erasure")

        access_results = await graph_task.run_access_request(
            privacy_request,
            policy,
            mongo_postgres_dataset_graph,
            [integration_postgres_config, integration_mongodb_config],
            {"email": "customer-1@example.com"},
            db,
        )

        # the access results should contain results from both connections
        postgres_dataset = integration_postgres_config.datasets[0].fides_key
        mongo_dataset = integration_mongodb_config.datasets[0].fides_key
        assert {key.split(":")[0] for key in access_results} == {
            postgres_dataset,
            mongo_dataset,
        }

        erasure_results = await graph_task.run_erasure(
            privacy_request,
            erasure_policy,
            mongo_postgres_dataset_graph,
            [integration_postgres_config, integration_mongodb_config],
            {"email": "customer-1@example.com"},
            get_cached_data_for_erasures(privacy_request.id),
            db,
        )

        # the erasure results should only contain results from mongodb
        mongo_dataset = integration_mongodb_config.datasets[0].fides_key
        assert {key.split(":")[0] for key in erasure_results} == {
            mongo_dataset,
        }

    @pytest.mark.asyncio
    async def test_access_disabled_for_manual_webhook_integrations(
        self,
        db,
        policy,
        integration_postgres_config,
        integration_manual_webhook_config,
        access_manual_webhook,
        run_privacy_request_task,
    ) -> None:
        pr = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "customer-1@example.com"},
            },
        )
        db.refresh(pr)

        # verify the request is paused if the manual webhook has the access action enabled
        assert pr.status == PrivacyRequestStatus.requires_input

        integration_manual_webhook_config.enabled_actions = [ActionType.erasure]
        integration_manual_webhook_config.save(db)

        pr = get_privacy_request_results(
            db,
            policy,
            run_privacy_request_task,
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "customer-1@example.com"},
            },
        )
        db.refresh(pr)

        # verify the request completes if the manual webhook has the access action disabled
        assert pr.status == PrivacyRequestStatus.complete

    @pytest.mark.asyncio
    async def test_erasure_disabled_for_manual_webhook_integrations(
        self,
        db,
        policy,
        erasure_policy,
        integration_postgres_config,
        integration_manual_webhook_config,
        access_manual_webhook,
        run_privacy_request_task,
    ) -> None:
        pr = get_privacy_request_results(
            db,
            erasure_policy,
            run_privacy_request_task,
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "customer-1@example.com"},
            },
        )
        db.refresh(pr)

        # verify the request is paused if the manual webhook has the erasure action enabled
        assert pr.status == PrivacyRequestStatus.requires_input

        integration_manual_webhook_config.enabled_actions = [ActionType.access]
        integration_manual_webhook_config.save(db)

        pr = get_privacy_request_results(
            db,
            erasure_policy,
            run_privacy_request_task,
            {
                "requested_at": "2021-08-30T16:09:37.359Z",
                "policy_key": policy.key,
                "identity": {"email": "customer-1@example.com"},
            },
        )
        db.refresh(pr)

        # verify the request completes if the manual webhook has the erasure action disabled
        assert pr.status == PrivacyRequestStatus.complete
