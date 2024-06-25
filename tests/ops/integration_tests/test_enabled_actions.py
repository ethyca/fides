import pytest
from fideslang.models import Dataset

from fides.api.graph.graph import DatasetGraph
from fides.api.models.connectionconfig import ActionType
from fides.api.models.datasetconfig import convert_dataset_to_graph
from fides.api.models.privacy_request import PrivacyRequestStatus
from fides.api.task.graph_runners import access_runner, erasure_runner
from fides.api.task.graph_task import (
    filter_by_enabled_actions,
    get_cached_data_for_erasures,
)
from tests.ops.integration_tests.saas.connector_runner import dataset_config
from tests.ops.service.privacy_request.test_request_runner_service import (
    get_privacy_request_results,
)


@pytest.mark.integration
class TestEnabledActions:
    @pytest.fixture(scope="function")
    def dataset_graph(
        self,
        db,
        example_datasets,
        integration_postgres_config,
    ) -> DatasetGraph:
        dataset_postgres = Dataset(**example_datasets[0])
        dataset_config(
            db, integration_postgres_config, dataset_postgres.model_dump(mode="json")
        )
        graph = convert_dataset_to_graph(
            dataset_postgres, integration_postgres_config.key
        )
        return DatasetGraph(graph)

    @pytest.mark.asyncio
    async def test_access_disabled(
        self, db, policy, integration_postgres_config, dataset_graph, privacy_request
    ) -> None:
        """Disable the access request for one connection config and verify the access results"""
        # Not testing this with both the DSR 2.0 and DSR 3.0 schedules because filtered_by_enabled_actions
        # happens after the access section now
        # disable the access action type for Postgres
        integration_postgres_config.enabled_actions = [ActionType.erasure]
        integration_postgres_config.save(db)

        access_runner(
            privacy_request,
            policy,
            dataset_graph,
            [integration_postgres_config],
            {"email": "customer-1@example.com"},
            db,
        )
        raw_access_results = privacy_request.get_raw_access_results()
        filtered_access_results = filter_by_enabled_actions(
            raw_access_results, [integration_postgres_config]
        )

        assert filtered_access_results == {}

    @pytest.mark.asyncio
    async def test_erasure_disabled(
        self,
        db,
        policy,
        erasure_policy,
        integration_postgres_config,
        dataset_graph,
        privacy_request_with_erasure_policy,
    ) -> None:
        """Disable the erasure request for one connection config and verify the erasure results"""

        # disable the erasure action type for Postgres
        integration_postgres_config.enabled_actions = [ActionType.access]
        integration_postgres_config.save(db)

        access_results = access_runner(
            privacy_request_with_erasure_policy,
            policy,
            dataset_graph,
            [integration_postgres_config],
            {"email": "customer-1@example.com"},
            db,
        )

        # the access results should contain results from postgres
        postgres_dataset = integration_postgres_config.datasets[0].fides_key
        assert {key.split(":")[0] for key in access_results} == {
            postgres_dataset,
        }

        erasure_results = erasure_runner(
            privacy_request_with_erasure_policy,
            erasure_policy,
            dataset_graph,
            [integration_postgres_config],
            {"email": "customer-1@example.com"},
            get_cached_data_for_erasures(privacy_request_with_erasure_policy.id),
            db,
        )

        # the erasure results should be empty
        assert erasure_results == {}

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_access_disabled_for_manual_webhook_integrations(
        self,
        db,
        dsr_version,
        request,
        policy,
        integration_postgres_config,
        integration_manual_webhook_config,
        access_manual_webhook,
        run_privacy_request_task,
    ) -> None:
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

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
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0", "use_dsr_2_0"],
    )
    async def test_erasure_disabled_for_manual_webhook_integrations(
        self,
        db,
        dsr_version,
        request,
        policy,
        erasure_policy,
        integration_postgres_config,
        integration_manual_webhook_config,
        access_manual_webhook,
        run_privacy_request_task,
    ) -> None:
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

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
