import pytest
from sqlalchemy.orm import Session

from fides.api.models.privacy_request import ExecutionLogStatus, PrivacyRequest
from fides.api.service.connectors.scylla_connector import ScyllaConnectorMissingKeyspace
from fides.api.task.graph_task import get_cached_data_for_erasures

from ...conftest import access_runner_tester, erasure_runner_tester
from ..graph.graph_test_util import assert_rows_match, erasure_policy
from ..task.traversal_data import integration_scylladb_graph


@pytest.mark.integration
@pytest.mark.integration_scylladb
@pytest.mark.asyncio
class TestScyllaDSRs:
    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_2_0"],
    )
    async def test_scylladb_access_request_task_no_keyspace_dsr2(
        self,
        db: Session,
        policy,
        integration_scylladb_config,
        scylladb_integration_no_keyspace,
        privacy_request,
        dsr_version,
        request,
    ) -> None:
        request.getfixturevalue(dsr_version)

        with pytest.raises(ScyllaConnectorMissingKeyspace) as err:
            v = access_runner_tester(
                privacy_request,
                policy,
                integration_scylladb_graph("scylla_example"),
                [integration_scylladb_config],
                {"email": "customer-1@example.com"},
                db,
            )

        assert (
            "No keyspace provided in the ScyllaDB configuration for connector scylla_example"
            in str(err.value)
        )

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_3_0"],
    )
    async def test_scylladb_access_request_task_no_keyspace_dsr3(
        self,
        db,
        policy,
        integration_scylladb_config,
        scylladb_integration_no_keyspace,
        privacy_request: PrivacyRequest,
        dsr_version,
        request,
    ) -> None:
        request.getfixturevalue(dsr_version)
        v = access_runner_tester(
            privacy_request,
            policy,
            integration_scylladb_graph("scylla_example"),
            [integration_scylladb_config],
            {"email": "customer-1@example.com"},
            db,
        )

        assert v == {}
        assert (
            privacy_request.access_tasks.count() == 6
        )  # There's 4 tables plus the root and terminal "dummy" tasks

        # Root task should be completed
        assert privacy_request.access_tasks.first().collection_name == "__ROOT__"
        assert (
            privacy_request.access_tasks.first().status == ExecutionLogStatus.complete
        )

        # All other tasks should be error
        for access_task in privacy_request.access_tasks.offset(1):
            assert access_task.status == ExecutionLogStatus.error

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_2_0", "use_dsr_3_0"],
    )
    async def test_scylladb_access_request_task(
        self,
        db,
        policy,
        integration_scylladb_config_with_keyspace,
        scylla_reset_db,
        scylladb_integration_with_keyspace,
        privacy_request,
        dsr_version,
        request,
    ) -> None:
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        results = access_runner_tester(
            privacy_request,
            policy,
            integration_scylladb_graph("scylla_example_with_keyspace"),
            [integration_scylladb_config_with_keyspace],
            {"email": "customer-1@example.com"},
            db,
        )

        assert_rows_match(
            results["scylla_example_with_keyspace:users"],
            min_size=1,
            keys=[
                "age",
                "alternative_contacts",
                "do_not_contact",
                "email",
                "name",
                "last_contacted",
                "logins",
                "states_lived",
            ],
        )
        assert_rows_match(
            results["scylla_example_with_keyspace:user_activity"],
            min_size=3,
            keys=["timestamp", "user_agent", "activity_type"],
        )
        assert_rows_match(
            results["scylla_example_with_keyspace:payment_methods"],
            min_size=2,
            keys=["card_number", "expiration_date"],
        )
        assert_rows_match(
            results["scylla_example_with_keyspace:orders"],
            min_size=2,
            keys=["order_amount", "order_date", "order_description"],
        )

    @pytest.mark.parametrize(
        "dsr_version",
        ["use_dsr_2_0", "use_dsr_3_0"],
    )
    async def test_scylladb_erasure_task(
        self,
        db,
        integration_scylladb_config_with_keyspace,
        scylladb_integration_with_keyspace,
        scylla_reset_db,
        privacy_request,
        dsr_version,
        request,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        seed_email = "customer-1@example.com"

        policy = erasure_policy(
            db, "user.name", "user.behavior", "user.device", "user.payment"
        )
        privacy_request.policy_id = policy.id
        privacy_request.save(db)

        graph = integration_scylladb_graph("scylla_example_with_keyspace")
        access_runner_tester(
            privacy_request,
            policy,
            integration_scylladb_graph("scylla_example_with_keyspace"),
            [integration_scylladb_config_with_keyspace],
            {"email": seed_email},
            db,
        )
        results = erasure_runner_tester(
            privacy_request,
            policy,
            graph,
            [integration_scylladb_config_with_keyspace],
            {"email": seed_email},
            get_cached_data_for_erasures(privacy_request.id),
            db,
        )
        assert results == {
            "scylla_example_with_keyspace:user_activity": 3,
            "scylla_example_with_keyspace:users": 1,
            "scylla_example_with_keyspace:payment_methods": 2,
            "scylla_example_with_keyspace:orders": 2,
        }
