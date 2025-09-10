"""
Tests for the ClassificationBenchmark database model.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from fides.api.models.detection_discovery.classification_benchmark import (
    ClassificationBenchmark,
)


class TestClassificationBenchmark:
    """Test cases for ClassificationBenchmark database model."""

    def test_store_benchmark_success(self, db: Session) -> None:
        """Test successful benchmark storage."""
        benchmark_data = {
            "monitor_config_key": "test_monitor",
            "dataset_fides_key": "test_dataset",
            "resource_urn": "database.schema.table",
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
        }

        stored_benchmark = ClassificationBenchmark.create(
            db,
            data=benchmark_data,
        )

        assert stored_benchmark is not None
        assert (
            stored_benchmark.monitor_config_key == benchmark_data["monitor_config_key"]
        )
        assert stored_benchmark.dataset_fides_key == benchmark_data["dataset_fides_key"]
        assert stored_benchmark.resource_urn == benchmark_data["resource_urn"]
        assert stored_benchmark.created_at is not None
        assert stored_benchmark.updated_at is not None
        assert stored_benchmark.overall_metrics == benchmark_data["overall_metrics"]
        assert (
            stored_benchmark.field_accuracy_details
            == benchmark_data["field_accuracy_details"]
        )
        assert stored_benchmark.id is not None

    def test_store_benchmark_with_minimal_data(self, db: Session) -> None:
        """Test benchmark storage with minimal required data."""
        minimal_data = {
            "monitor_config_key": "minimal_monitor",
            "dataset_fides_key": "minimal_dataset",
            "resource_urn": "minimal.urn",
            "overall_metrics": {},
            "field_accuracy_details": [],
        }

        stored_benchmark = ClassificationBenchmark.create(
            db,
            data=minimal_data,
        )

        assert stored_benchmark is not None
        assert stored_benchmark.monitor_config_key == minimal_data["monitor_config_key"]
        assert stored_benchmark.dataset_fides_key == minimal_data["dataset_fides_key"]
        assert stored_benchmark.resource_urn == minimal_data["resource_urn"]
        assert stored_benchmark.overall_metrics == {}
        assert stored_benchmark.field_accuracy_details == []

    def test_get_benchmark_found(self, db: Session) -> None:
        """Test retrieving an existing benchmark."""
        benchmark_data = {
            "monitor_config_key": "get_test_monitor",
            "dataset_fides_key": "get_test_dataset",
            "resource_urn": "get.test.urn",
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
        assert (
            retrieved_benchmark.monitor_config_key
            == benchmark_data["monitor_config_key"]
        )
        assert (
            retrieved_benchmark.dataset_fides_key == benchmark_data["dataset_fides_key"]
        )

    def test_get_benchmark_not_found(self, db: Session) -> None:
        """Test retrieving a non-existent benchmark."""
        result = ClassificationBenchmark.get(db, object_id="non-existent-id")
        assert result is None

    def test_delete_benchmark_success(self, db: Session) -> None:
        """Test successful benchmark deletion."""
        benchmark_data = {
            "monitor_config_key": "delete_test_monitor",
            "dataset_fides_key": "delete_test_dataset",
            "resource_urn": "delete.test.urn",
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

    def test_benchmark_with_complex_data(self, db: Session) -> None:
        """Test storing and retrieving benchmark with complex nested data."""
        complex_data = {
            "monitor_config_key": "complex_monitor",
            "dataset_fides_key": "complex_dataset",
            "resource_urn": "complex.database.schema.complex_table",
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

    def test_list_benchmarks_basic(self, db: Session) -> None:
        """Test basic listing of benchmarks with query filtering."""
        # Create test benchmarks
        benchmark_data_1 = {
            "monitor_config_key": "list_test_monitor_1",
            "dataset_fides_key": "list_test_dataset_1",
            "resource_urn": "list.test.1",
            "overall_metrics": {"precision": 0.8},
            "field_accuracy_details": [],
        }

        benchmark_data_2 = {
            "monitor_config_key": "list_test_monitor_2",
            "dataset_fides_key": "list_test_dataset_2",
            "resource_urn": "list.test.2",
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

    def test_list_benchmarks_with_monitor_filter(self, db: Session) -> None:
        """Test listing benchmarks filtered by monitor config key."""
        # Create benchmarks with different monitor keys
        benchmark_data_1 = {
            "monitor_config_key": "filter_monitor_1",
            "dataset_fides_key": "filter_dataset",
            "resource_urn": "filter.test.1",
            "overall_metrics": {"precision": 0.8},
            "field_accuracy_details": [],
        }

        benchmark_data_2 = {
            "monitor_config_key": "filter_monitor_2",
            "dataset_fides_key": "filter_dataset",
            "resource_urn": "filter.test.2",
            "overall_metrics": {"precision": 0.9},
            "field_accuracy_details": [],
        }

        benchmark_1 = ClassificationBenchmark.create(db, data=benchmark_data_1)
        benchmark_2 = ClassificationBenchmark.create(db, data=benchmark_data_2)
        db.commit()

        # Test filtering by monitor config key
        query = ClassificationBenchmark.list_benchmarks(
            db, monitor_config_key="filter_monitor_1"
        )
        results = query.all()

        assert len(results) >= 1

        # Verify only the correct benchmark is returned
        benchmark_ids = [b.id for b in results]
        assert benchmark_1.id in benchmark_ids
        assert benchmark_2.id not in benchmark_ids

    def test_list_benchmarks_with_dataset_filter(self, db: Session) -> None:
        """Test listing benchmarks filtered by dataset fides key."""
        # Create benchmarks with different dataset keys
        benchmark_data_1 = {
            "monitor_config_key": "filter_monitor",
            "dataset_fides_key": "filter_dataset_1",
            "resource_urn": "filter.test.1",
            "overall_metrics": {"precision": 0.8},
            "field_accuracy_details": [],
        }

        benchmark_data_2 = {
            "monitor_config_key": "filter_monitor",
            "dataset_fides_key": "filter_dataset_2",
            "resource_urn": "filter.test.2",
            "overall_metrics": {"precision": 0.9},
            "field_accuracy_details": [],
        }

        benchmark_1 = ClassificationBenchmark.create(db, data=benchmark_data_1)
        benchmark_2 = ClassificationBenchmark.create(db, data=benchmark_data_2)
        db.commit()

        # Test filtering by dataset fides key
        query = ClassificationBenchmark.list_benchmarks(
            db, dataset_fides_key="filter_dataset_1"
        )
        results = query.all()

        assert len(results) >= 1

        # Verify only the correct benchmark is returned
        benchmark_ids = [b.id for b in results]
        assert benchmark_1.id in benchmark_ids
        assert benchmark_2.id not in benchmark_ids

    def test_list_benchmarks_with_date_filters(self, db: Session) -> None:
        """Test listing benchmarks filtered by date range."""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)

        # Create benchmarks with different dates
        benchmark_data_1 = {
            "monitor_config_key": "date_monitor",
            "dataset_fides_key": "date_dataset",
            "resource_urn": "date.test.1",
            "created_at": yesterday,
            "overall_metrics": {"precision": 0.8},
            "field_accuracy_details": [],
        }

        benchmark_data_2 = {
            "monitor_config_key": "date_monitor",
            "dataset_fides_key": "date_dataset",
            "resource_urn": "date.test.2",
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

    def test_list_benchmarks_with_combined_filters(self, db: Session) -> None:
        """Test listing benchmarks with multiple filters combined."""
        now = datetime.utcnow()

        # Create benchmarks with different combinations
        benchmark_data_1 = {
            "monitor_config_key": "combined_monitor_1",
            "dataset_fides_key": "combined_dataset_1",
            "resource_urn": "combined.test.1",
            "created_at": now,
            "overall_metrics": {"precision": 0.8},
            "field_accuracy_details": [],
        }

        benchmark_data_2 = {
            "monitor_config_key": "combined_monitor_1",
            "dataset_fides_key": "combined_dataset_2",
            "resource_urn": "combined.test.2",
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
            monitor_config_key="combined_monitor_1",
            dataset_fides_key="combined_dataset_1",
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

    def test_list_benchmarks_ordering(self, db: Session) -> None:
        """Test that benchmarks are ordered by created_at desc."""
        now = datetime.utcnow()

        # Create benchmarks with different timestamps
        benchmark_data_1 = {
            "monitor_config_key": "order_monitor",
            "dataset_fides_key": "order_dataset",
            "resource_urn": "order.test.1",
            "created_at": now - timedelta(hours=2),
            "overall_metrics": {"precision": 0.8},
            "field_accuracy_details": [],
        }

        benchmark_data_2 = {
            "monitor_config_key": "order_monitor",
            "dataset_fides_key": "order_dataset",
            "resource_urn": "order.test.2",
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
