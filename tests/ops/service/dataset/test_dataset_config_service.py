import datetime
from typing import List, Set

import pytest
from pytest import FixtureRequest
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.policy import Policy
from fides.api.schemas.policy import ActionType
from fides.service.dataset.dataset_config_service import DatasetConfigService
from tests.conftest import wait_for_tasks_to_complete


def make_dataset_invalid(db: Session, dataset_config: DatasetConfig) -> None:
    """Helper function to make a dataset invalid by setting an invalid data type in its collections"""
    ctl_dataset = dataset_config.ctl_dataset

    # Set an invalid data type on the first field
    ctl_dataset.collections[0]["fields"][0]["fides_meta"] = {
        "data_type": "invalid_type"
    }
    flag_modified(ctl_dataset, "collections")

    db.add(ctl_dataset)
    db.commit()


@pytest.fixture
def dataset_config_service(db: Session) -> DatasetConfigService:
    return DatasetConfigService(db)

class TestGetDatasetReachability:

    @pytest.mark.parametrize(
        "dataset_config, expected",
        [
            ("single_identity_dataset_config", (True, None)),
            (
                "single_identity_with_internal_dependency_dataset_config",
                (True, None),
            ),
            (
                "multiple_identities_dataset_config",
                (True, None),
            ),
            (
                "multiple_identities_with_external_dependencies_dataset_config",
                (
                    False,
                    'The following dataset references do not exist "single_identity:customer:id"',
                ),
            ),
            (
                "optional_identities_dataset_config",
                (True, None),
            ),
            (
                "no_identities_dataset_config",
                (
                    False,
                    'The following collections are not reachable "no_identities:customer"',
                ),
            ),
        ],
    )
    def test_get_dataset_reachability(
        self,
        dataset_config_service: DatasetConfigService,
        dataset_config: List[str],
        expected: bool,
        connection_config: ConnectionConfig,
        request: pytest.FixtureRequest,
    ):
        request.getfixturevalue(dataset_config)

        reachable = dataset_config_service.get_dataset_reachability(
            connection_config.datasets[0],
        )
        assert reachable == expected

    @pytest.mark.usefixtures(
        "single_identity_dataset_config", "unreachable_dataset_on_different_connection"
    )
    def test_get_dataset_reachability_ignores_additional_connections(
        self,
        dataset_config_service: DatasetConfigService,
        connection_config: ConnectionConfig,
    ):
        """Verify that the reachability check ignores unreachable datasets on other connections"""

        reachable = dataset_config_service.get_dataset_reachability(
            connection_config.datasets[0],
        )
        assert reachable == (True, None)

    @pytest.mark.usefixtures(
        "single_identity_dataset_config", "no_identities_dataset_config"
    )
    def test_get_dataset_reachability_ignores_sibling_datasets(
        self,
        dataset_config_service: DatasetConfigService,
        connection_config: ConnectionConfig,
    ):
        """Verify that the reachability check ignores unreachable sibling datasets (on the same connection)"""

        reachable = dataset_config_service.get_dataset_reachability(
            connection_config.datasets[0],
        )
        assert reachable == (True, None)

    def test_get_dataset_reachability_invalid_dataset_config(
        self,
        dataset_config_service: DatasetConfigService,
        single_identity_dataset_config: DatasetConfig,
        db: Session,
    ):
        """Test that dataset with invalid datatype fails validation by directly modifying the database"""
        make_dataset_invalid(db, single_identity_dataset_config)

        reachable = dataset_config_service.get_dataset_reachability(
            single_identity_dataset_config,
        )
        assert reachable == (
            False,
            [
                {
                    "type": "value_error",
                    "loc": ["collections", 0, "fields", 0, "fides_meta", "data_type"],
                    "msg": "Value error, The data type invalid_type is not supported.",
                }
            ],
        )

    def test_get_dataset_reachability_ignores_validation_error_on_other_connection(
        self,
        dataset_config_service: DatasetConfigService,
        single_identity_dataset_config: DatasetConfig,
        unreachable_dataset_on_different_connection: DatasetConfig,
        db: Session,
    ):
        """Test that validation errors on other connections are ignored"""
        make_dataset_invalid(db, unreachable_dataset_on_different_connection)

        reachable = dataset_config_service.get_dataset_reachability(
            single_identity_dataset_config,
        )
        assert reachable == (True, None)

    def test_get_dataset_reachability_ignores_sibling_validation_error(
        self,
        db: Session,
        dataset_config_service: DatasetConfigService,
        single_identity_dataset_config: DatasetConfig,
        no_identities_dataset_config: DatasetConfig,
        connection_config: ConnectionConfig,
    ):
        """Test that validation errors on sibling datasets are ignored"""
        # Disable the connection
        connection_config.disabled = True
        db.commit()

        # Make the sibling dataset invalid
        make_dataset_invalid(db, no_identities_dataset_config)

        reachable = dataset_config_service.get_dataset_reachability(
            single_identity_dataset_config,
        )
        assert reachable == (True, None)


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
                {"loyalty_id", "single_identity:customer:id"},
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

        required_identities = connection_config.datasets[
            0
        ].get_identities_and_references()
        assert required_identities == expected_required_identities


@pytest.mark.integration
@pytest.mark.integration_postgres
class TestRunTestAccessRequest:
    """
    Run test requests against the postgres_example database
    """

    @pytest.mark.usefixtures("postgres_integration_db")
    def test_run_test_access_request(
        self,
        db: Session,
        dataset_config_service: DatasetConfigService,
        policy: Policy,
        postgres_example_test_dataset_config: DatasetConfig,
    ):
        dataset_config = postgres_example_test_dataset_config
        privacy_request = dataset_config_service.run_test_access_request(
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
        dataset_config_service: DatasetConfigService,
        policy: Policy,
        postgres_example_test_extended_dataset_config: DatasetConfig,
    ):
        dataset_config = postgres_example_test_extended_dataset_config
        privacy_request = dataset_config_service.run_test_access_request(
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
        dataset_config_service: DatasetConfigService,
        policy: Policy,
        multiple_identities_with_external_dependencies_dataset_config: DatasetConfig,
    ):
        dataset_config = multiple_identities_with_external_dependencies_dataset_config
        privacy_request = dataset_config_service.run_test_access_request(
            policy,
            dataset_config,
            {"loyalty_id": "CH-1", "single_identity:customer:id": 1},
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
