"""
Tests for the ClassificationBenchmark database model.
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from fides.api.models.connectionconfig import (
    AccessLevel,
    ConnectionConfig,
    ConnectionType,
)
from fides.api.models.detection_discovery.classification_benchmark import (
    ClassificationBenchmark,
)
from fides.api.models.detection_discovery.core import MonitorConfig
from fides.api.models.sql_models import Dataset


@pytest.fixture
def test_connection_config(db: Session) -> ConnectionConfig:
    """Create a test ConnectionConfig for use in tests."""
    connection_config = ConnectionConfig(
        key="test_connection",
        name="Test Connection",
        connection_type=ConnectionType.postgres,
        access=AccessLevel.read,
    )
    db.add(connection_config)
    db.commit()
    return connection_config


@pytest.fixture
def test_monitor_config(
    db: Session, test_connection_config: ConnectionConfig
) -> MonitorConfig:
    """Create a test MonitorConfig for use in tests."""
    monitor_config = MonitorConfig(
        key="test_monitor",
        name="Test Monitor",
        connection_config_id=test_connection_config.id,
        databases=["test_db"],
        excluded_databases=[],
    )
    db.add(monitor_config)
    db.commit()
    return monitor_config


@pytest.fixture
def test_dataset(db: Session) -> Dataset:
    """Create a test Dataset for use in tests."""
    dataset = Dataset(
        fides_key="test_dataset",
        name="Test Dataset",
        organization_fides_key="test_org",
        collections=[],
    )
    db.add(dataset)
    db.commit()
    return dataset


# Additional fixtures for list tests - reuse the same ones
@pytest.fixture
def test_monitor_config_1(
    db: Session, test_connection_config: ConnectionConfig
) -> MonitorConfig:
    """Create a test MonitorConfig for list tests."""
    monitor_config = MonitorConfig(
        key="list_test_monitor_1",
        name="List Test Monitor 1",
        connection_config_id=test_connection_config.id,
        databases=["test_db_1"],
        excluded_databases=[],
    )
    db.add(monitor_config)
    db.commit()
    return monitor_config


@pytest.fixture
def test_dataset_1(db: Session) -> Dataset:
    """Create a test Dataset for list tests."""
    dataset = Dataset(
        fides_key="list_test_dataset_1",
        name="List Test Dataset 1",
        organization_fides_key="test_org_1",
        collections=[],
    )
    db.add(dataset)
    db.commit()
    return dataset


@pytest.fixture
def test_monitor_config_2(
    db: Session, test_connection_config: ConnectionConfig
) -> MonitorConfig:
    """Create a second test MonitorConfig for list tests."""
    monitor_config = MonitorConfig(
        key="list_test_monitor_2",
        name="List Test Monitor 2",
        connection_config_id=test_connection_config.id,
        databases=["test_db_2"],
        excluded_databases=[],
    )
    db.add(monitor_config)
    db.commit()
    return monitor_config


@pytest.fixture
def test_dataset_2(db: Session) -> Dataset:
    """Create a second test Dataset for list tests."""
    dataset = Dataset(
        fides_key="list_test_dataset_2",
        name="List Test Dataset 2",
        organization_fides_key="test_org_2",
        collections=[],
    )
    db.add(dataset)
    db.commit()
    return dataset


# Additional datasets for filter tests
@pytest.fixture
def filter_dataset_1(db: Session) -> Dataset:
    """Create a Dataset for dataset filter tests."""
    dataset = Dataset(
        fides_key="filter_dataset_1",
        name="Filter Dataset 1",
        organization_fides_key="filter_org_1",
        collections=[],
    )
    db.add(dataset)
    db.commit()
    return dataset


@pytest.fixture
def filter_dataset_2(db: Session) -> Dataset:
    """Create a second Dataset for dataset filter tests."""
    dataset = Dataset(
        fides_key="filter_dataset_2",
        name="Filter Dataset 2",
        organization_fides_key="filter_org_2",
        collections=[],
    )
    db.add(dataset)
    db.commit()
    return dataset


class TestClassificationBenchmark:
    """Test cases for ClassificationBenchmark database model."""

    def test_store_benchmark_success(
        self, db: Session, test_monitor_config: MonitorConfig, test_dataset: Dataset
    ) -> None:
        """Test successful benchmark storage."""
        benchmark_data = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["database.schema.table1", "database.schema.table2"],
            "overall_metrics": {
                "precision": 0.8,
                "recall": 0.7,
                "f1_score": 0.75,
                "total_ground_truth": 100,
                "total_classified": 90,
                "true_positives": 70,
                "false_positives": 20,
                "false_negatives": 30,
            },
            "field_accuracy_details": [
                {
                    "field_urn": "database.schema.table.field1",
                    "ground_truth_categories": ["user.contact.email"],
                    "classified_categories": ["user.contact.email"],
                    "is_correct": True,
                    "missing_categories": [],
                    "extra_categories": [],
                }
            ],
            "status": "completed",
            "messages": [],
        }

        stored_benchmark = ClassificationBenchmark.create(
            db,
            data=benchmark_data,
        )

        assert stored_benchmark is not None
        assert stored_benchmark.monitor_config_key == test_monitor_config.key
        assert stored_benchmark.dataset_fides_key == test_dataset.fides_key
        assert stored_benchmark.resource_urns == benchmark_data["resource_urns"]
        assert stored_benchmark.created_at is not None
        assert stored_benchmark.updated_at is not None
        assert stored_benchmark.overall_metrics == benchmark_data["overall_metrics"]
        assert (
            stored_benchmark.field_accuracy_details
            == benchmark_data["field_accuracy_details"]
        )
        assert stored_benchmark.status == "completed"
        assert stored_benchmark.messages == []
        assert stored_benchmark.id is not None

    def test_store_benchmark_with_minimal_data(
        self, db: Session, test_monitor_config: MonitorConfig, test_dataset: Dataset
    ) -> None:
        """Test benchmark storage with minimal required data."""
        minimal_data = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["minimal.urn"],
            "overall_metrics": None,
            "field_accuracy_details": [],
            "status": "failed",
            "messages": ["Benchmark failed: Dataset not found"],
        }

        stored_benchmark = ClassificationBenchmark.create(
            db,
            data=minimal_data,
        )

        assert stored_benchmark is not None
        assert stored_benchmark.monitor_config_key == test_monitor_config.key
        assert stored_benchmark.dataset_fides_key == test_dataset.fides_key
        assert stored_benchmark.resource_urns == minimal_data["resource_urns"]
        assert stored_benchmark.overall_metrics is None
        assert stored_benchmark.field_accuracy_details == []
        assert stored_benchmark.status == "failed"
        assert stored_benchmark.messages == ["Benchmark failed: Dataset not found"]

    def test_get_benchmark_found(
        self, db: Session, test_monitor_config: MonitorConfig, test_dataset: Dataset
    ) -> None:
        """Test retrieving an existing benchmark."""
        benchmark_data = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["get.test.urn"],
            "overall_metrics": {"precision": 0.9},
            "field_accuracy_details": [],
        }

        stored_benchmark = ClassificationBenchmark.create(
            db,
            data=benchmark_data,
        )
        benchmark_id = stored_benchmark.id

        retrieved_benchmark = ClassificationBenchmark.get(db, object_id=benchmark_id)

        assert retrieved_benchmark is not None
        assert retrieved_benchmark.id == benchmark_id
        assert retrieved_benchmark.monitor_config_key == test_monitor_config.key
        assert retrieved_benchmark.dataset_fides_key == test_dataset.fides_key

    def test_get_benchmark_not_found(self, db: Session) -> None:
        """Test retrieving a non-existent benchmark."""
        result = ClassificationBenchmark.get(db, object_id="non-existent-id")
        assert result is None

    def test_delete_benchmark_success(
        self, db: Session, test_monitor_config: MonitorConfig, test_dataset: Dataset
    ) -> None:
        """Test successful benchmark deletion."""
        benchmark_data = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["delete.test.urn"],
            "created_at": datetime.utcnow(),
            "overall_metrics": {"precision": 0.85},
            "field_accuracy_details": [],
        }

        stored_benchmark = ClassificationBenchmark.create(
            db,
            data=benchmark_data,
        )
        benchmark_id = stored_benchmark.id

        stored_benchmark.delete(db)

        # Verify deletion
        deleted_benchmark = ClassificationBenchmark.get(db, object_id=benchmark_id)
        assert deleted_benchmark is None

    def test_benchmark_with_complex_data(
        self, db: Session, test_monitor_config: MonitorConfig, test_dataset: Dataset
    ) -> None:
        """Test storing and retrieving benchmark with complex nested data."""
        complex_data = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["complex.database.schema.complex_table"],
            "created_at": datetime(2024, 2, 1, 12, 30, 45),
            "overall_metrics": {
                "precision": 0.95,
                "recall": 0.88,
                "f1_score": 0.91,
                "total_ground_truth": 1000,
                "total_classified": 950,
                "true_positives": 850,
                "false_positives": 100,
                "false_negatives": 150,
            },
            "field_accuracy_details": [
                {
                    "field_urn": "complex.database.schema.complex_table.email_field",
                    "ground_truth_categories": [
                        "user.contact.email",
                        "user.personal.email",
                    ],
                    "classified_categories": ["user.contact.email"],
                    "is_correct": False,
                    "missing_categories": ["user.personal.email"],
                    "extra_categories": [],
                },
                {
                    "field_urn": "complex.database.schema.complex_table.phone_field",
                    "ground_truth_categories": ["user.contact.phone"],
                    "classified_categories": ["user.contact.phone"],
                    "is_correct": True,
                    "missing_categories": [],
                    "extra_categories": [],
                },
            ],
        }

        stored_benchmark = ClassificationBenchmark.create(
            db,
            data=complex_data,
        )
        db.commit()

        # Retrieve and verify
        retrieved_benchmark = ClassificationBenchmark.get(
            db, object_id=stored_benchmark.id
        )

        assert retrieved_benchmark is not None
        assert retrieved_benchmark.overall_metrics == complex_data["overall_metrics"]
        assert len(retrieved_benchmark.field_accuracy_details) == 2
        assert (
            retrieved_benchmark.field_accuracy_details[0]["field_urn"]
            == "complex.database.schema.complex_table.email_field"
        )
        assert retrieved_benchmark.field_accuracy_details[1]["is_correct"] is True
        assert retrieved_benchmark.field_accuracy_details[0]["is_correct"] is False


class TestClassificationBenchmarkList:
    """Test cases for listing classification benchmarks."""

    def test_list_benchmarks_basic(
        self,
        db: Session,
        test_monitor_config_1: MonitorConfig,
        test_dataset_1: Dataset,
        test_monitor_config_2: MonitorConfig,
        test_dataset_2: Dataset,
    ) -> None:
        """Test basic listing of benchmarks with query filtering."""
        # Create test benchmarks
        benchmark_data_1 = {
            "monitor_config_key": test_monitor_config_1.key,
            "dataset_fides_key": test_dataset_1.fides_key,
            "resource_urns": ["list.test.1"],
            "overall_metrics": {"precision": 0.8},
            "field_accuracy_details": [],
        }

        benchmark_data_2 = {
            "monitor_config_key": test_monitor_config_2.key,
            "dataset_fides_key": test_dataset_2.fides_key,
            "resource_urns": ["list.test.2"],
            "overall_metrics": {"precision": 0.9},
            "field_accuracy_details": [],
        }

        benchmark_1 = ClassificationBenchmark.create(db, data=benchmark_data_1)
        benchmark_2 = ClassificationBenchmark.create(db, data=benchmark_data_2)
        db.commit()

        # Test listing with query
        query = ClassificationBenchmark.list_benchmarks(db)
        results = query.all()

        assert len(results) >= 2

        # Verify benchmarks are in the results
        benchmark_ids = [b.id for b in results]
        assert benchmark_1.id in benchmark_ids
        assert benchmark_2.id in benchmark_ids

    def test_list_benchmarks_with_monitor_filter(
        self,
        db: Session,
        test_monitor_config: MonitorConfig,
        test_monitor_config_1: MonitorConfig,
        test_dataset: Dataset,
    ) -> None:
        """Test listing benchmarks filtered by monitor config key."""
        # Create benchmarks with different monitor keys
        benchmark_data_1 = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["filter.test.1"],
            "overall_metrics": {"precision": 0.8},
            "field_accuracy_details": [],
        }

        benchmark_data_2 = {
            "monitor_config_key": test_monitor_config_1.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["filter.test.2"],
            "overall_metrics": {"precision": 0.9},
            "field_accuracy_details": [],
        }

        benchmark_1 = ClassificationBenchmark.create(db, data=benchmark_data_1)
        benchmark_2 = ClassificationBenchmark.create(db, data=benchmark_data_2)
        db.commit()

        # Test filtering by monitor config key
        query = ClassificationBenchmark.list_benchmarks(
            db, monitor_config_key=test_monitor_config.key
        )
        results = query.all()

        assert len(results) >= 1

        # Verify only the correct benchmark is returned
        benchmark_ids = [b.id for b in results]
        assert benchmark_1.id in benchmark_ids
        assert benchmark_2.id not in benchmark_ids

    def test_list_benchmarks_with_dataset_filter(
        self,
        db: Session,
        test_monitor_config: MonitorConfig,
        test_dataset: Dataset,
        test_dataset_1: Dataset,
    ) -> None:
        """Test listing benchmarks filtered by dataset fides key."""
        # Create benchmarks with different dataset keys
        benchmark_data_1 = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["filter.test.1"],
            "overall_metrics": {"precision": 0.8},
            "field_accuracy_details": [],
        }

        benchmark_data_2 = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset_1.fides_key,
            "resource_urns": ["filter.test.2"],
            "overall_metrics": {"precision": 0.9},
            "field_accuracy_details": [],
        }

        benchmark_1 = ClassificationBenchmark.create(db, data=benchmark_data_1)
        benchmark_2 = ClassificationBenchmark.create(db, data=benchmark_data_2)
        db.commit()

        # Test filtering by dataset fides key
        query = ClassificationBenchmark.list_benchmarks(
            db, dataset_fides_key=test_dataset.fides_key
        )
        results = query.all()

        assert len(results) >= 1

        # Verify only the correct benchmark is returned
        benchmark_ids = [b.id for b in results]
        assert benchmark_1.id in benchmark_ids
        assert benchmark_2.id not in benchmark_ids

    def test_list_benchmarks_with_date_filters(
        self, db: Session, test_monitor_config: MonitorConfig, test_dataset: Dataset
    ) -> None:
        """Test listing benchmarks filtered by date range."""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)

        # Create benchmarks with different dates
        benchmark_data_1 = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["date.test.1"],
            "created_at": yesterday,
            "overall_metrics": {"precision": 0.8},
            "field_accuracy_details": [],
        }

        benchmark_data_2 = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["date.test.2"],
            "created_at": now,
            "overall_metrics": {"precision": 0.9},
            "field_accuracy_details": [],
        }

        benchmark_1 = ClassificationBenchmark.create(db, data=benchmark_data_1)
        benchmark_2 = ClassificationBenchmark.create(db, data=benchmark_data_2)
        db.commit()

        # Test filtering by created_after
        query = ClassificationBenchmark.list_benchmarks(db, created_after=now)
        results = query.all()

        assert len(results) >= 1

        # Verify only the recent benchmark is returned
        benchmark_ids = [b.id for b in results]
        assert benchmark_2.id in benchmark_ids
        assert benchmark_1.id not in benchmark_ids

        # Test filtering by created_before
        query = ClassificationBenchmark.list_benchmarks(db, created_before=now)
        results = query.all()

        assert len(results) >= 1

        # Verify only the older benchmark is returned
        benchmark_ids = [b.id for b in results]
        assert benchmark_1.id in benchmark_ids
        assert benchmark_2.id not in benchmark_ids

    def test_list_benchmarks_with_status_filter(
        self, db: Session, test_monitor_config: MonitorConfig, test_dataset: Dataset
    ) -> None:
        """Test listing benchmarks filtered by status."""
        now = datetime.utcnow()
        benchmark_data = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["status.test"],
            "status": "completed",
            "created_at": now,
            "overall_metrics": {"precision": 0.8},
            "field_accuracy_details": [],
        }

        benchmark_data_2 = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["status.test.2"],
            "status": "failed",
            "created_at": now,
            "overall_metrics": {"precision": 0.9},
            "field_accuracy_details": [],
        }
        benchmark = ClassificationBenchmark.create(db, data=benchmark_data)
        benchmark_2 = ClassificationBenchmark.create(db, data=benchmark_data_2)
        db.commit()
        benchmark_id = benchmark.id
        query = ClassificationBenchmark.list_benchmarks(db, status="completed")
        results = query.all()
        assert len(results) == 1
        assert results[0].id == benchmark_id

    def test_list_benchmarks_with_combined_filters(
        self,
        db: Session,
        test_monitor_config: MonitorConfig,
        test_dataset: Dataset,
        test_dataset_1: Dataset,
    ) -> None:
        """Test listing benchmarks with multiple filters combined."""
        now = datetime.utcnow()

        # Create benchmarks with different combinations
        benchmark_data_1 = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["combined.test.1"],
            "created_at": now,
            "overall_metrics": {"precision": 0.8},
            "field_accuracy_details": [],
        }

        benchmark_data_2 = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset_1.fides_key,
            "resource_urns": ["combined.test.2"],
            "created_at": now,
            "overall_metrics": {"precision": 0.9},
            "field_accuracy_details": [],
        }

        benchmark_1 = ClassificationBenchmark.create(db, data=benchmark_data_1)
        benchmark_2 = ClassificationBenchmark.create(db, data=benchmark_data_2)
        db.commit()

        # Test with multiple filters
        query = ClassificationBenchmark.list_benchmarks(
            db,
            monitor_config_key=test_monitor_config.key,
            dataset_fides_key=test_dataset.fides_key,
            created_after=now - timedelta(hours=1),
        )
        results = query.all()

        assert len(results) >= 1

        # Verify only the matching benchmark is returned
        benchmark_ids = [b.id for b in results]
        assert benchmark_1.id in benchmark_ids
        assert benchmark_2.id not in benchmark_ids

    def test_list_benchmarks_empty_result(self, db: Session) -> None:
        """Test listing benchmarks when no results match filters."""
        # Test with non-existent monitor config key
        query = ClassificationBenchmark.list_benchmarks(
            db, monitor_config_key="non_existent_monitor"
        )
        results = query.all()

        assert len(results) == 0

    def test_list_benchmarks_ordering(
        self, db: Session, test_monitor_config: MonitorConfig, test_dataset: Dataset
    ) -> None:
        """Test that benchmarks are ordered by created_at desc."""
        now = datetime.utcnow()

        # Create benchmarks with different timestamps
        benchmark_data_1 = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["order.test.1"],
            "created_at": now - timedelta(hours=2),
            "overall_metrics": {"precision": 0.8},
            "field_accuracy_details": [],
        }

        benchmark_data_2 = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["order.test.2"],
            "created_at": now - timedelta(hours=1),
            "overall_metrics": {"precision": 0.9},
            "field_accuracy_details": [],
        }

        benchmark_1 = ClassificationBenchmark.create(db, data=benchmark_data_1)
        benchmark_2 = ClassificationBenchmark.create(db, data=benchmark_data_2)
        db.commit()

        # Test ordering
        query = ClassificationBenchmark.list_benchmarks(db)
        results = query.all()

        assert len(results) >= 2

        # Verify ordering (newest first)
        created_times = [b.created_at for b in results]
        assert created_times == sorted(created_times, reverse=True)

    def test_relationship_properties(
        self, db: Session, test_monitor_config: MonitorConfig, test_dataset: Dataset
    ) -> None:
        """Test that relationship properties work correctly."""
        # Create benchmark with relationships
        benchmark_data = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["test.relationship.urn"],
            "overall_metrics": {"precision": 0.9},
            "field_accuracy_details": [],
        }

        benchmark = ClassificationBenchmark.create(db, data=benchmark_data)
        db.commit()

        # Test relationship properties
        assert benchmark.monitor_config is not None
        assert benchmark.monitor_config.key == test_monitor_config.key
        assert benchmark.monitor_config.name == test_monitor_config.name

        assert benchmark.dataset is not None
        assert benchmark.dataset.fides_key == test_dataset.fides_key
        assert benchmark.dataset.name == test_dataset.name

        # Test that we can access related object properties
        assert (
            benchmark.monitor_config.connection_config_id
            == test_monitor_config.connection_config_id
        )
        assert (
            benchmark.dataset.organization_fides_key
            == test_dataset.organization_fides_key
        )

    def test_cannot_create_benchmark_with_nonexistent_keys(self, db: Session) -> None:
        """Test that we cannot create benchmarks with nonexistent foreign keys."""
        # Create benchmark with non-existent foreign keys
        benchmark_data = {
            "monitor_config_key": "nonexistent_monitor",
            "dataset_fides_key": "nonexistent_dataset",
            "resource_urns": ["test.nonexistent.urn"],
            "overall_metrics": {"precision": 0.8},
            "field_accuracy_details": [],
        }

        # This should raise an IntegrityError due to foreign key constraints
        with pytest.raises(Exception):  # Should be IntegrityError or similar
            ClassificationBenchmark.create(db, data=benchmark_data)
            db.commit()

    def test_cascade_delete_when_monitor_config_deleted(
        self, db: Session, test_monitor_config: MonitorConfig, test_dataset: Dataset
    ) -> None:
        """Test that benchmark records are deleted when associated monitor config is deleted."""
        # Create a benchmark
        benchmark_data = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["cascade.test.urn"],
            "overall_metrics": {"precision": 0.9},
            "field_accuracy_details": [],
        }

        benchmark = ClassificationBenchmark.create(db, data=benchmark_data)
        db.commit()
        benchmark_id = benchmark.id

        # Verify benchmark exists
        assert ClassificationBenchmark.get(db, object_id=benchmark_id) is not None

        # Delete the monitor config
        db.delete(test_monitor_config)
        db.commit()

        # Verify benchmark is also deleted due to CASCADE
        assert ClassificationBenchmark.get(db, object_id=benchmark_id) is None

    def test_cascade_delete_when_dataset_deleted(
        self, db: Session, test_monitor_config: MonitorConfig, test_dataset: Dataset
    ) -> None:
        """Test that benchmark records are deleted when associated dataset is deleted."""
        # Create a benchmark
        benchmark_data = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["cascade.test.urn"],
            "overall_metrics": {"precision": 0.9},
            "field_accuracy_details": [],
        }

        benchmark = ClassificationBenchmark.create(db, data=benchmark_data)
        db.commit()
        benchmark_id = benchmark.id

        # Verify benchmark exists
        assert ClassificationBenchmark.get(db, object_id=benchmark_id) is not None

        # Delete the dataset
        db.delete(test_dataset)
        db.commit()

        # Verify benchmark is also deleted due to CASCADE
        assert ClassificationBenchmark.get(db, object_id=benchmark_id) is None

    def test_cascade_delete_multiple_benchmarks(
        self, db: Session, test_monitor_config: MonitorConfig, test_dataset: Dataset
    ) -> None:
        """Test that multiple benchmark records are deleted when associated monitor config is deleted."""
        # Create multiple benchmarks with the same monitor config
        benchmark_data_1 = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["cascade.test.1"],
            "overall_metrics": {"precision": 0.8},
            "field_accuracy_details": [],
        }

        benchmark_data_2 = {
            "monitor_config_key": test_monitor_config.key,
            "dataset_fides_key": test_dataset.fides_key,
            "resource_urns": ["cascade.test.2"],
            "overall_metrics": {"precision": 0.9},
            "field_accuracy_details": [],
        }

        benchmark_1 = ClassificationBenchmark.create(db, data=benchmark_data_1)
        benchmark_2 = ClassificationBenchmark.create(db, data=benchmark_data_2)
        db.commit()

        benchmark_1_id = benchmark_1.id
        benchmark_2_id = benchmark_2.id

        # Verify both benchmarks exist
        assert ClassificationBenchmark.get(db, object_id=benchmark_1_id) is not None
        assert ClassificationBenchmark.get(db, object_id=benchmark_2_id) is not None

        # Delete the monitor config
        db.delete(test_monitor_config)
        db.commit()

        # Verify both benchmarks are deleted due to CASCADE
        assert ClassificationBenchmark.get(db, object_id=benchmark_1_id) is None
        assert ClassificationBenchmark.get(db, object_id=benchmark_2_id) is None
