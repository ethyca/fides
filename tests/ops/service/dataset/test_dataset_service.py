import datetime
from typing import List, Set

import pytest
from pytest import FixtureRequest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import Policy
from fides.api.schemas.policy import ActionType
from fides.api.service.dataset.dataset_service import (
    get_dataset_reachability,
    get_identities_and_references,
    run_test_access_request,
)
from tests.conftest import wait_for_tasks_to_complete


class TestGetDatasetReachability:

    @pytest.mark.parametrize(
        "dataset_config, expected",
        [
            ("single_identity_dataset_config", True),
            (
                "single_identity_with_internal_dependency_dataset_config",
                True,
            ),
            (
                "multiple_identities_dataset_config",
                True,
            ),
            (
                "multiple_identities_with_external_dependencies_dataset_config",
                False,
            ),
            (
                "optional_identities_dataset_config",
                True,
            ),
            (
                "no_identities_dataset_config",
                False,
            ),
        ],
    )
    def test_get_dataset_reachability(
        self,
        db: Session,
        dataset_config: List[str],
        expected: bool,
        connection_config: ConnectionConfig,
        request: pytest.FixtureRequest,
    ):
        request.getfixturevalue(dataset_config)

        reachable = get_dataset_reachability(
            db,
            connection_config.datasets[0],
        )
        assert reachable == expected


class TestGetIdentitiesAndReferences:

    @pytest.mark.parametrize(
        "dataset_config, expected_required_identities",
        [
            ("single_identity_dataset_config", {"email"}),
            (
                "single_identity_with_internal_dependency_dataset_config",
                {"email"},
            ),
            (
                "multiple_identities_dataset_config",
                {"email", "loyalty_id"},
            ),
            (
                "multiple_identities_with_external_dependencies_dataset_config",
                {"loyalty_id", "single_identity.customer.id"},
            ),
            (
                "optional_identities_dataset_config",
                {"email", "user_id"},
            ),
            (
                "no_identities_dataset_config",
                set(),
            ),
        ],
    )
    def test_get_identities_and_references(
        self,
        dataset_config: List[str],
        expected_required_identities: Set[str],
        connection_config: ConnectionConfig,
        request: FixtureRequest,
    ):
        request.getfixturevalue(dataset_config)

        required_identities = get_identities_and_references(
            connection_config.datasets[0],
        )
        assert required_identities == expected_required_identities


class TestRunTestAccessRequest:
    @pytest.mark.usefixtures("postgres_integration_db")
    def test_run_test_access_request(
        self,
        db: Session,
        policy: Policy,
        postgres_example_test_dataset_config: DatasetConfig,
    ):
        dataset_config = postgres_example_test_dataset_config
        privacy_request = run_test_access_request(
            db,
            policy,
            dataset_config,
            {"email": "jane@example.com"},
        )
        wait_for_tasks_to_complete(db, privacy_request, ActionType.access)
        assert privacy_request.get_raw_access_results() == {
            "postgres_example_test_dataset:customer": [
                {
                    "address_id": 4,
                    "created": datetime.datetime(2020, 4, 1, 11, 47, 42),
                    "email": "jane@example.com",
                    "id": 3,
                    "name": "Jane Customer",
                }
            ],
            "postgres_example_test_dataset:employee": [],
            "postgres_example_test_dataset:report": [],
            "postgres_example_test_dataset:visit": [],
            "postgres_example_test_dataset:orders": [
                {"customer_id": 3, "id": "ord_ddd-eee", "shipping_address_id": 4}
            ],
            "postgres_example_test_dataset:login": [
                {"customer_id": 3, "id": 8, "time": datetime.datetime(2021, 1, 6, 1, 0)}
            ],
            "postgres_example_test_dataset:payment_card": [
                {
                    "billing_address_id": 4,
                    "ccn": 373719391,
                    "code": 222,
                    "customer_id": 3,
                    "id": "pay_ccc-ccc",
                    "name": "Example Card 3",
                    "preferred": False,
                }
            ],
            "postgres_example_test_dataset:service_request": [],
            "postgres_example_test_dataset:order_item": [],
            "postgres_example_test_dataset:address": [
                {
                    "city": "Example Mountain",
                    "house": 1111,
                    "id": 4,
                    "state": "TX",
                    "street": "Example Place",
                    "zip": "54321",
                }
            ],
            "postgres_example_test_dataset:product": [],
        }

    @pytest.mark.usefixtures("postgres_integration_db")
    def test_run_sample_access_request_with_custom_id(
        self,
        db: Session,
        policy: Policy,
        postgres_example_test_extended_dataset_config: DatasetConfig,
    ):
        dataset_config = postgres_example_test_extended_dataset_config
        privacy_request = run_test_access_request(
            db,
            policy,
            dataset_config,
            {"loyalty_id": "CH-1"},
        )
        wait_for_tasks_to_complete(db, privacy_request, ActionType.access)
        assert privacy_request.get_raw_access_results() == {
            "postgres_example_test_extended_dataset:loyalty": [
                {
                    "id": "CH-1",
                    "name": "Jane Customer",
                    "points": 100,
                    "tier": "Cookie Rookie",
                }
            ]
        }

    @pytest.mark.usefixtures(
        "postgres_integration_db",
    )
    def test_run_test_access_request_with_dataset_reference(
        self,
        db: Session,
        policy: Policy,
        multiple_identities_with_external_dependencies_dataset_config: DatasetConfig,
    ):
        dataset_config = multiple_identities_with_external_dependencies_dataset_config
        privacy_request = run_test_access_request(
            db,
            policy,
            dataset_config,
            {"loyalty_id": "CH-1", "single_identity.customer.id": 1},
        )
        wait_for_tasks_to_complete(db, privacy_request, ActionType.access)
        assert privacy_request.get_raw_access_results() == {
            "multiple_identities_with_external_dependency:loyalty": [
                {
                    "id": "CH-1",
                    "name": "Jane Customer",
                    "points": 100,
                    "tier": "Cookie Rookie",
                }
            ],
            "multiple_identities_with_external_dependency:orders": [
                {"customer_id": 1, "id": "ord_aaa-aaa", "shipping_address_id": 2},
                {"customer_id": 1, "id": "ord_ccc-ccc", "shipping_address_id": 1},
                {"customer_id": 1, "id": "ord_ddd-ddd", "shipping_address_id": 1},
            ],
        }
