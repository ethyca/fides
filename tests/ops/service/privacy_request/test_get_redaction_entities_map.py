import io
import zipfile

import pytest

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.privacy_request_redaction_pattern import (
    PrivacyRequestRedactionPattern,
)
from fides.api.models.sql_models import Dataset as CtlDataset
from fides.api.service.privacy_request.dsr_package.dsr_report_builder import (
    DSRReportBuilder,
)
from fides.api.service.privacy_request.dsr_package.utils import (
    get_redaction_entities_map,
    get_redaction_entities_map_db,
)
from tests.ops.service.privacy_request.test_dsr_report_builder import (
    TestDSRReportBuilderBase,
)


@pytest.mark.integration_postgres
class TestGetRedactionEntitiesMap:
    """Tests for both get_redaction_entities_map implementations (Python and DB-based)"""

    @pytest.mark.parametrize(
        "redaction_func",
        [get_redaction_entities_map, get_redaction_entities_map_db],
        ids=["python_implementation", "db_implementation"],
    )
    def test_get_redaction_entities_map_empty_dataset(self, db, redaction_func):
        """Test get_redaction_entities_map with no dataset configurations"""
        result = redaction_func(db)
        assert result == set()

    @pytest.mark.parametrize(
        "redaction_func",
        [get_redaction_entities_map, get_redaction_entities_map_db],
        ids=["python_implementation", "db_implementation"],
    )
    def test_get_redaction_entities_map_no_redaction_meta(
        self, db, postgres_example_test_dataset_config, redaction_func
    ):
        """Test get_redaction_entities_map with dataset config but no redaction meta"""
        result = redaction_func(db)
        assert result == set()

    @pytest.mark.parametrize(
        "redaction_func",
        [get_redaction_entities_map, get_redaction_entities_map_db],
        ids=["python_implementation", "db_implementation"],
    )
    def test_get_redaction_entities_map_dataset_level_redaction(
        self, db, redaction_func
    ):
        """Test get_redaction_entities_map with dataset-level redaction"""

        # Create a connection config first (ensure it's not disabled)
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_redaction_connection",
                "name": "Test Redaction Connection",
                "connection_type": ConnectionType.manual,
                "access": AccessLevel.read,
                "disabled": False,
            },
        )

        # Create a dataset with dataset-level redaction
        dataset_dict = {
            "fides_key": "test_dataset_redacted",
            "name": "Test Dataset Redacted",
            "collections": [],
            "fides_meta": {"redact": "name"},
        }

        ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset_dict)
        DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": "test_dataset_redacted",
                "ctl_dataset_id": ctl_dataset.id,
            },
        )

        result = redaction_func(db)
        assert "test_dataset_redacted" in result

    @pytest.mark.parametrize(
        "redaction_func",
        [get_redaction_entities_map, get_redaction_entities_map_db],
        ids=["python_implementation", "db_implementation"],
    )
    def test_get_redaction_entities_map_collection_level_redaction(
        self, db, redaction_func
    ):
        """Test get_redaction_entities_map with collection-level redaction"""

        # Create a connection config first (ensure it's not disabled)
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_collection_redaction_connection",
                "name": "Test Collection Redaction Connection",
                "connection_type": ConnectionType.manual,
                "access": AccessLevel.read,
                "disabled": False,
            },
        )

        # Create a dataset with collection-level redaction
        dataset_dict = {
            "fides_key": "test_dataset",
            "name": "Test Dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [],
                    "fides_meta": {"redact": "name"},
                },
                {
                    "name": "orders",
                    "fields": [],
                    # No redaction meta
                },
            ],
        }

        ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset_dict)
        DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": "test_dataset",
                "ctl_dataset_id": ctl_dataset.id,
            },
        )

        result = redaction_func(db)
        assert "test_dataset.users" in result
        assert "test_dataset.orders" not in result

    @pytest.mark.parametrize(
        "redaction_func",
        [get_redaction_entities_map, get_redaction_entities_map_db],
        ids=["python_implementation", "db_implementation"],
    )
    def test_get_redaction_entities_map_field_level_redaction(self, db, redaction_func):
        """Test get_redaction_entities_map with field-level redaction"""

        # Create a connection config first (ensure it's not disabled)
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_field_redaction_connection",
                "name": "Test Field Redaction Connection",
                "connection_type": ConnectionType.manual,
                "access": AccessLevel.read,
                "disabled": False,
            },
        )

        # Create a dataset with field-level redaction
        dataset_dict = {
            "fides_key": "test_dataset",
            "name": "Test Dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                            "fides_meta": {"redact": "name"},
                        },
                        {
                            "name": "name",
                            "data_categories": ["user.name"],
                            # No redaction meta
                        },
                    ],
                }
            ],
        }

        ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset_dict)

        DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": "test_dataset",
                "ctl_dataset_id": ctl_dataset.id,
            },
        )

        result = redaction_func(db)
        assert "test_dataset.users.email" in result
        assert "test_dataset.users.name" not in result

    @pytest.mark.parametrize(
        "redaction_func",
        [get_redaction_entities_map, get_redaction_entities_map_db],
        ids=["python_implementation", "db_implementation"],
    )
    def test_get_redaction_entities_map_hierarchical_redaction(
        self, db, redaction_func
    ):
        """Test get_redaction_entities_map with redaction at multiple levels"""

        # Create a connection config first (ensure it's not disabled)
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_hierarchical_redaction_connection",
                "name": "Test Hierarchical Redaction Connection",
                "connection_type": ConnectionType.manual,
                "access": AccessLevel.read,
                "disabled": False,
            },
        )

        # Create a dataset with redaction at dataset, collection, and field levels
        dataset_dict = {
            "fides_key": "test_dataset",
            "name": "Test Dataset",
            "fides_meta": {"redact": "name"},  # Dataset level
            "collections": [
                {
                    "name": "users",
                    "fides_meta": {"redact": "name"},  # Collection level
                    "fields": [
                        {
                            "name": "email",
                            "data_categories": ["user.contact.email"],
                            "fides_meta": {"redact": "name"},  # Field level
                        },
                        {
                            "name": "phone",
                            "data_categories": ["user.contact.phone_number"],
                            # No redaction meta
                        },
                    ],
                },
                {
                    "name": "orders",
                    "fields": [
                        {
                            "name": "order_id",
                            "data_categories": ["system.operations"],
                            "fides_meta": {"redact": "name"},  # Field level only
                        },
                    ],
                },
            ],
        }

        ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset_dict)
        DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": "test_dataset",
                "ctl_dataset_id": ctl_dataset.id,
            },
        )

        result = redaction_func(db)
        # Dataset level
        assert "test_dataset" in result
        # Collection level
        assert "test_dataset.users" in result
        assert "test_dataset.orders" not in result
        # Field level
        assert "test_dataset.users.email" in result
        assert "test_dataset.users.phone" not in result
        assert "test_dataset.orders.order_id" in result

    def test_nested_field_regex_pattern_redaction(
        self, privacy_request: PrivacyRequest, db
    ):
        """Test that nested JSON fields get redacted when regex pattern is configured."""
        # Set up redaction patterns
        PrivacyRequestRedactionPattern.replace_patterns(
            db=db, patterns=["full_name", "email.*"]
        )

        # Create connection config
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_nested_redaction",
                "name": "Test Nested Redaction",
                "connection_type": ConnectionType.manual,
                "access": AccessLevel.read,
                "disabled": False,
            },
        )

        # Create dataset with JSON field
        dataset_dict = {
            "fides_key": "nested_test",
            "name": "Nested Test",
            "collections": [
                {
                    "name": "profiles",
                    "fields": [
                        {"name": "id", "data_categories": ["system.operations"]},
                        {"name": "user_info", "data_categories": ["user"]},
                    ],
                }
            ],
        }

        ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset_dict)
        DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": "nested_test",
                "ctl_dataset_id": ctl_dataset.id,
            },
        )

        # Create DSR data with nested JSON
        dsr_data = {
            "nested_test:profiles": [
                {
                    "id": 1,
                    "user_info": {
                        "full_name": "John Doe",
                        "email_address": "john@example.com",
                        "phone": "555-1234",
                    },
                },
            ],
        }

        # Generate report
        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        # Check redaction
        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            content = zip_file.read("data/nested_test/profiles/index.html").decode(
                "utf-8"
            )

            # Nested fields matching regex patterns should be redacted
            assert "full_name" not in content
            assert "email_address" not in content
            # Non-matching fields should remain
            assert "phone" in content
            # Data values should be preserved
            assert "John Doe" in content
            assert "john@example.com" in content

    @pytest.mark.parametrize(
        "redaction_func",
        [get_redaction_entities_map, get_redaction_entities_map_db],
        ids=["python_implementation", "db_implementation"],
    )
    def test_get_redaction_entities_map_multiple_datasets(self, db, redaction_func):
        """Test get_redaction_entities_map with multiple datasets"""

        connection_configs = []

        # Create multiple datasets with different redaction configurations
        for dataset_index in range(1, 4):
            # Create a connection config for each dataset
            connection_config = ConnectionConfig.create(
                db=db,
                data={
                    "key": f"test_multiple_datasets_connection_{dataset_index}",
                    "name": f"Test Multiple Datasets Connection {dataset_index}",
                    "connection_type": ConnectionType.manual,
                    "access": AccessLevel.read,
                    "disabled": False,
                },
            )
            connection_configs.append(connection_config)

            dataset_dict = {
                "fides_key": f"dataset_{dataset_index}",
                "name": f"Dataset {dataset_index}",
                "collections": [
                    {
                        "name": "users",
                        "fields": [
                            {
                                "name": "email",
                                "data_categories": ["user.contact.email"],
                                "fides_meta": (
                                    {"redact": "name"} if dataset_index % 2 == 1 else {}
                                ),
                            },
                        ],
                        "fides_meta": {"redact": "name"} if dataset_index == 2 else {},
                    }
                ],
                "fides_meta": {"redact": "name"} if dataset_index == 3 else {},
            }

            ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset_dict)
            DatasetConfig.create(
                db=db,
                data={
                    "connection_config_id": connection_config.id,
                    "fides_key": f"dataset_{dataset_index}",
                    "ctl_dataset_id": ctl_dataset.id,
                },
            )

        result = redaction_func(db)

        # Dataset 1: field-level redaction only
        assert "dataset_1.users.email" in result
        assert "dataset_1.users" not in result
        assert "dataset_1" not in result

        # Dataset 2: collection-level redaction
        assert "dataset_2.users" in result
        assert "dataset_2" not in result

        # Dataset 3: dataset-level redaction
        assert "dataset_3" in result

    @pytest.mark.parametrize(
        "redaction_func",
        [get_redaction_entities_map, get_redaction_entities_map_db],
        ids=["python_implementation", "db_implementation"],
    )
    def test_get_redaction_entities_map_nested_fields(self, db, redaction_func):
        """Test get_redaction_entities_map with deeply nested fields"""

        # Create a connection config first (ensure it's not disabled)
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_nested_connection",
                "name": "Test Nested Connection",
                "connection_type": ConnectionType.manual,
                "access": AccessLevel.read,
                "disabled": False,
            },
        )

        # Create a dataset with deeply nested fields
        dataset_dict = {
            "fides_key": "test_nested_dataset",
            "name": "Test Nested Dataset",
            "collections": [
                {
                    "name": "users",
                    "fields": [
                        {
                            "name": "profile",
                            "fides_meta": {"redact": "name"},  # Level 1 redaction
                            "fields": [
                                {
                                    "name": "personal_info",
                                    "fides_meta": {
                                        "redact": "name"
                                    },  # Level 2 redaction
                                    "fields": [
                                        {
                                            "name": "ssn",
                                            "fides_meta": {
                                                "redact": "name"
                                            },  # Level 3 redaction
                                            "fields": [],
                                        },
                                        {
                                            "name": "passport_info",
                                            "fides_meta": {},  # No redaction
                                            "fields": [
                                                {
                                                    "name": "passport_number",
                                                    "fides_meta": {
                                                        "redact": "name"
                                                    },  # Level 4 redaction
                                                    "fields": [],
                                                }
                                            ],
                                        },
                                    ],
                                }
                            ],
                        },
                        {
                            "name": "email",
                            "fides_meta": {},  # No redaction
                            "fields": [],
                        },
                    ],
                }
            ],
        }

        ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset_dict)
        DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": "test_nested_dataset",
                "ctl_dataset_id": ctl_dataset.id,
            },
        )

        result = redaction_func(db)

        # Verify all nested redaction entities are found
        assert "test_nested_dataset.users.profile" in result
        assert "test_nested_dataset.users.profile.personal_info" in result
        assert "test_nested_dataset.users.profile.personal_info.ssn" in result
        assert (
            "test_nested_dataset.users.profile.personal_info.passport_info.passport_number"
            in result
        )

        # Verify non-redacted entities are not included
        assert "test_nested_dataset.users.email" not in result
        assert (
            "test_nested_dataset.users.profile.personal_info.passport_info"
            not in result
        )

    def test_both_implementations_return_same_results(self, db):
        """Test that both implementations return identical results for complex dataset"""

        # Create a connection config
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_comparison_connection",
                "name": "Test Comparison Connection",
                "connection_type": ConnectionType.manual,
                "access": AccessLevel.read,
                "disabled": False,
            },
        )

        # Create a complex dataset with redaction at all levels
        dataset_dict = {
            "fides_key": "comparison_dataset",
            "name": "Comparison Dataset",
            "fides_meta": {"redact": "name"},
            "collections": [
                {
                    "name": "collection_one",
                    "fields": [
                        {
                            "name": "field_one",
                            "data_categories": ["user"],
                            "fides_meta": {"redact": "name"},
                        },
                        {
                            "name": "field_two",
                            "data_categories": ["user"],
                            "fields": [
                                {
                                    "name": "nested_field",
                                    "data_categories": ["user"],
                                    "fides_meta": {"redact": "name"},
                                }
                            ],
                        },
                    ],
                    "fides_meta": {"redact": "name"},
                },
                {
                    "name": "collection_two",
                    "fields": [
                        {
                            "name": "another_field",
                            "data_categories": ["user"],
                        }
                    ],
                },
            ],
        }

        ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset_dict)
        DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": "comparison_dataset",
                "ctl_dataset_id": ctl_dataset.id,
            },
        )

        # Get results from both implementations
        python_result = get_redaction_entities_map(db)
        db_result = get_redaction_entities_map_db(db)

        # Both should return the same entities
        assert python_result == db_result

        # Verify specific entities are present in both
        expected_entities = {
            "comparison_dataset",  # Dataset level
            "comparison_dataset.collection_one",  # Collection level
            "comparison_dataset.collection_one.field_one",  # Field level
            "comparison_dataset.collection_one.field_two.nested_field",  # Nested field
        }

        for entity in expected_entities:
            assert entity in python_result
            assert entity in db_result


@pytest.mark.integration_postgres
class TestDsrReportBuilderRedactionEntitiesIntegration(TestDSRReportBuilderBase):
    """Tests for DSR report builder integration with redaction entities map"""

    def test_redaction_by_entities_map_dataset_level(
        self, privacy_request: PrivacyRequest, db
    ):
        """Test dataset-level redaction using entities map"""

        # Create a connection config first (ensure it's not disabled)
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_integration_dataset_redaction_connection",
                "name": "Test Integration Dataset Redaction Connection",
                "connection_type": ConnectionType.manual,
                "access": AccessLevel.read,
                "disabled": False,
            },
        )

        # Create a dataset with dataset-level redaction
        dataset_dict = {
            "fides_key": "customer_database",
            "name": "Customer Database",
            "collections": [],
            "fides_meta": {"redact": "name"},
        }

        ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset_dict)

        DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": "customer_database",
                "ctl_dataset_id": ctl_dataset.id,
            },
        )

        dsr_data = {
            "customer_database:users": [
                {"id": 1, "name": "John Doe", "email": "john@example.com"},
            ],
            "public_data:articles": [
                {"id": 1, "title": "Public Article"},
            ],
        }

        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            welcome_content = zip_file.read("welcome.html").decode("utf-8")

            # customer_database should be redacted to dataset_1
            assert "dataset_1" in welcome_content
            assert "customer_database" not in welcome_content

            # public_data should not be redacted (no redaction configuration)
            assert "public_data" in welcome_content

            # Verify file structure uses redacted names
            assert "data/dataset_1/index.html" in zip_file.namelist()
            assert "data/public_data/index.html" in zip_file.namelist()

    def test_redaction_by_entities_map_collection_level(
        self, privacy_request: PrivacyRequest, db
    ):
        """Test collection-level redaction using entities map"""

        # Create a connection config first (ensure it's not disabled)
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_integration_collection_redaction_connection",
                "name": "Test Integration Collection Redaction Connection",
                "connection_type": ConnectionType.manual,
                "access": AccessLevel.read,
                "disabled": False,
            },
        )

        # Create a dataset with collection-level redaction
        dataset_dict = {
            "fides_key": "customer_data",
            "name": "Customer Data",
            "collections": [
                {
                    "name": "user_profiles",
                    "fields": [],
                    "fides_meta": {"redact": "name"},
                },
                {
                    "name": "orders",
                    "fields": [],
                    # No redaction meta
                },
            ],
        }

        ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset_dict)

        DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": "customer_data",
                "ctl_dataset_id": ctl_dataset.id,
            },
        )

        dsr_data = {
            "customer_data:user_profiles": [
                {"id": 1, "name": "John Doe"},
            ],
            "customer_data:orders": [
                {"id": 101, "amount": 49.99},
            ],
        }

        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            dataset_content = zip_file.read("data/customer_data/index.html").decode(
                "utf-8"
            )

            # user_profiles should be redacted to collection_1
            assert "collection_1" in dataset_content
            assert "user_profiles" not in dataset_content

            # orders should not be redacted
            assert "orders" in dataset_content

            # Verify file structure
            assert "data/customer_data/collection_1/index.html" in zip_file.namelist()
            assert "data/customer_data/orders/index.html" in zip_file.namelist()

    def test_redaction_by_entities_map_field_level(
        self, privacy_request: PrivacyRequest, db
    ):
        """Test field-level redaction using entities map"""

        # Create a connection config first (ensure it's not disabled)
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_integration_field_redaction_connection",
                "name": "Test Integration Field Redaction Connection",
                "connection_type": ConnectionType.manual,
                "access": AccessLevel.read,
                "disabled": False,
            },
        )

        # Create a dataset with field-level redaction
        dataset_dict = {
            "fides_key": "user_data",
            "name": "User Data",
            "collections": [
                {
                    "name": "profiles",
                    "fields": [
                        {
                            "name": "email_address",
                            "data_categories": ["user.contact.email"],
                            "fides_meta": {"redact": "name"},
                        },
                        {
                            "name": "full_name",
                            "data_categories": ["user.name"],
                            # No redaction meta
                        },
                    ],
                }
            ],
        }

        ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset_dict)

        DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": "user_data",
                "ctl_dataset_id": ctl_dataset.id,
            },
        )

        dsr_data = {
            "user_data:profiles": [
                {"id": 1, "email_address": "john@example.com", "full_name": "John Doe"},
            ],
        }

        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            collection_content = zip_file.read(
                "data/user_data/profiles/index.html"
            ).decode("utf-8")

            # email_address should be redacted to field_N
            assert "field_" in collection_content
            assert "email_address" not in collection_content

            # full_name should not be redacted
            assert "full_name" in collection_content

            # Verify the data values are still present
            assert "john@example.com" in collection_content
            assert "John Doe" in collection_content

    def test_redaction_entities_map_priority_over_regex(
        self, privacy_request: PrivacyRequest, db
    ):
        """Test that entities map redaction takes priority over regex patterns"""

        # Create a connection config first (ensure it's not disabled)
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_integration_regex_priority_connection",
                "name": "Test Integration Regex Priority Connection",
                "connection_type": ConnectionType.manual,
                "access": AccessLevel.read,
                "disabled": False,
            },
        )

        # Create dataset config with specific redaction for one collection
        dataset_dict = {
            "fides_key": "test_data",
            "name": "Test Data",
            "collections": [
                {
                    "name": "user_accounts",  # Would match regex .*user.* but has specific redaction
                    "fields": [],
                    "fides_meta": {"redact": "name"},
                },
                {
                    "name": "user_sessions",  # Would match regex .*user.* but no specific redaction
                    "fields": [],
                },
            ],
        }

        ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset_dict)

        DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": "test_data",
                "ctl_dataset_id": ctl_dataset.id,
            },
        )

        # Set up regex patterns that would match both collections
        PrivacyRequestRedactionPattern.replace_patterns(db=db, patterns=[r".*user.*"])

        dsr_data = {
            "test_data:user_accounts": [{"id": 1}],
            "test_data:user_sessions": [{"id": 2}],
        }

        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            dataset_content = zip_file.read("data/test_data/index.html").decode("utf-8")

            # user_accounts has specific redaction config, so uses collection_1
            assert "collection_1" in dataset_content

            # user_sessions has no specific config but matches regex, so uses collection_2
            assert "collection_2" in dataset_content

            # Neither original name should appear
            assert "user_accounts" not in dataset_content
            assert "user_sessions" not in dataset_content

    def test_redaction_entities_map_with_mixed_hierarchical_levels(
        self, privacy_request: PrivacyRequest, db
    ):
        """Test redaction with entities at different hierarchical levels including nested data structures"""

        # Create a connection config first (ensure it's not disabled)
        connection_config = ConnectionConfig.create(
            db=db,
            data={
                "key": "test_integration_mixed_hierarchical_connection",
                "name": "Test Integration Mixed Hierarchical Connection",
                "connection_type": ConnectionType.manual,
                "access": AccessLevel.read,
                "disabled": False,
            },
        )

        # Create dataset with redaction at multiple levels including nested fields
        dataset_dict = {
            "fides_key": "mixed_data",
            "name": "Mixed Data",
            "fides_meta": {"redact": "name"},  # Dataset level
            "collections": [
                {
                    "name": "public_info",
                    "fields": [
                        {
                            "name": "description",
                            "data_categories": ["system.operations"],
                        },
                        {
                            "name": "metadata",
                            "data_categories": ["system.operations"],
                            "fields": [
                                {
                                    "name": "created_by",
                                    "data_categories": ["user.name"],
                                    "fides_meta": {"redact": "name"},
                                },
                                {
                                    "name": "tags",
                                    "data_categories": ["system.operations"],
                                    "fields": [
                                        {
                                            "name": "category",
                                            "data_categories": ["system.operations"],
                                        }
                                    ],
                                },
                            ],
                        },
                    ],
                    # No collection-level redaction (should inherit from dataset)
                },
                {
                    "name": "sensitive_data",
                    "fields": [
                        {
                            "name": "ssn",
                            "data_categories": ["user.government_id"],
                            "fides_meta": {
                                "redact": "name"
                            },  # Field level (redundant with dataset)
                        },
                        {
                            "name": "personal_details",
                            "data_categories": ["user"],
                            "fields": [
                                {
                                    "name": "address",
                                    "data_categories": ["user.contact.address"],
                                    "fides_meta": {"redact": "name"},
                                    "fields": [
                                        {
                                            "name": "street",
                                            "data_categories": [
                                                "user.contact.address.street"
                                            ],
                                        },
                                        {
                                            "name": "postal_code",
                                            "data_categories": [
                                                "user.contact.address.postal_code"
                                            ],
                                            "fides_meta": {"redact": "name"},
                                        },
                                    ],
                                },
                                {
                                    "name": "phone_numbers",
                                    "data_categories": ["user.contact.phone_number"],
                                },
                            ],
                        },
                    ],
                    "fides_meta": {
                        "redact": "name"
                    },  # Collection level (redundant with dataset)
                },
            ],
        }

        ctl_dataset = CtlDataset.create_from_dataset_dict(db, dataset_dict)

        DatasetConfig.create(
            db=db,
            data={
                "connection_config_id": connection_config.id,
                "fides_key": "mixed_data",
                "ctl_dataset_id": ctl_dataset.id,
            },
        )

        dsr_data = {
            "mixed_data:public_info": [
                {
                    "description": "public data",
                    "metadata": {
                        "created_by": "john_doe",
                        "tags": {"category": "general"},
                    },
                }
            ],
            "mixed_data:sensitive_data": [
                {
                    "ssn": "123-45-6789",
                    "personal_details": {
                        "address": {"street": "123 Main St", "postal_code": "12345"},
                        "phone_numbers": ["555-1234", "555-5678"],
                    },
                }
            ],
        }

        builder = DSRReportBuilder(privacy_request=privacy_request, dsr_data=dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(io.BytesIO(report.getvalue())) as zip_file:
            welcome_content = zip_file.read("welcome.html").decode("utf-8")

            # Dataset is redacted due to dataset-level config
            assert "dataset_1" in welcome_content
            assert "mixed_data" not in welcome_content

            # Check that file structure uses redacted dataset name
            assert "data/dataset_1/index.html" in zip_file.namelist()

            # Verify nested data is properly included in the generated report
            dataset_content = zip_file.read("data/dataset_1/index.html").decode("utf-8")

            # Based on the actual output, public_info is not redacted but sensitive_data is
            # This is because only sensitive_data has explicit collection-level redaction
            assert (
                "public_info" in dataset_content
            )  # public_info not redacted (no collection-level config)
            assert (
                "collection_2" in dataset_content
            )  # sensitive_data redacted due to collection-level config
            assert "sensitive_data" not in dataset_content

            # Check that nested data structure is preserved in the report
            # Look for collection detail pages
            public_info_files = [
                f
                for f in zip_file.namelist()
                if "public_info" in f and f.endswith(".html")
            ]
            sensitive_data_files = [
                f
                for f in zip_file.namelist()
                if "collection_2" in f and f.endswith(".html")
            ]

            assert (
                len(public_info_files) > 0
            ), "Should have public_info collection files"
            assert (
                len(sensitive_data_files) > 0
            ), "Should have sensitive_data collection files"

            # Verify nested data appears in the collection content
            if public_info_files:
                public_content = zip_file.read(public_info_files[0]).decode("utf-8")

                # Verify that nested field names are redacted in the JSON content
                # Only "created_by" has explicit redaction config, so only it should be redacted
                assert (
                    "created_by" not in public_content
                )  # field name should be redacted in JSON
                assert "field_" in public_content  # should contain redacted field names

                # The "tags" field should NOT be redacted, it has no explicit redaction config
                assert "tags" in public_content  # tags should remain unredacted

            if sensitive_data_files:
                sensitive_content = zip_file.read(sensitive_data_files[0]).decode(
                    "utf-8"
                )

                # Verify that nested field names with explicit redaction configs are redacted
                assert (
                    "address" not in sensitive_content
                )  # address field has explicit redaction config
                assert (
                    "postal_code" not in sensitive_content
                )  # postal_code field has explicit redaction config
                assert (
                    "field_" in sensitive_content
                )  # should contain redacted field names

                # Fields without explicit redaction should remain unredacted
                assert (
                    "street" in sensitive_content
                )  # street has no explicit redaction config
                assert (
                    "phone_numbers" in sensitive_content
                )  # phone_numbers has no explicit redaction config
