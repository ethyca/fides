import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fides.api.service.storage.streaming.schemas import ProcessingMetrics


class TestProcessingMetrics:
    """Test cases for the ProcessingMetrics Pydantic model."""



    def test_processing_metrics_default_values(self):
        """Test that ProcessingMetrics can be instantiated with default values."""
        metrics = ProcessingMetrics()

        assert metrics.total_attachments == 0
        assert metrics.processed_attachments == 0
        assert metrics.total_bytes == 0
        assert metrics.processed_bytes == 0
        assert isinstance(metrics.start_time, datetime)
        assert metrics.current_attachment is None
        assert metrics.current_attachment_progress == 0.0
        assert metrics.errors == []

    def test_processing_metrics_with_custom_values(self):
        """Test creating ProcessingMetrics with custom values."""
        start_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        metrics = ProcessingMetrics(
            total_attachments=100,
            processed_attachments=50,
            total_bytes=1024,
            processed_bytes=512,
            start_time=start_time,
            current_attachment="test.pdf",
            current_attachment_progress=75.5,
            errors=["Error 1", "Error 2"]
        )

        assert metrics.total_attachments == 100
        assert metrics.processed_attachments == 50
        assert metrics.total_bytes == 1024
        assert metrics.processed_bytes == 512
        assert metrics.start_time == start_time
        assert metrics.current_attachment == "test.pdf"
        assert metrics.current_attachment_progress == 75.5
        assert metrics.errors == ["Error 1", "Error 2"]


    @pytest.mark.parametrize("field, value, expected_error", [
        pytest.param("total_attachments", -1, "Input should be greater than or equal to 0", id="total_attachments_negative"),
        pytest.param("processed_attachments", -5, "Input should be greater than or equal to 0", id="processed_attachments_negative"),
        pytest.param("total_bytes", -100, "Input should be greater than or equal to 0", id="total_bytes_negative"),
        pytest.param("processed_bytes", -50, "Input should be greater than or equal to 0", id="processed_bytes_negative"),
        pytest.param("current_attachment_progress", -10.0, "Input should be greater than or equal to 0", id="current_attachment_progress_negative"),
        pytest.param("current_attachment_progress", 150.0, "Input should be less than or equal to 100", id="current_attachment_progress_too_high")
    ])
    def test_processing_metrics_validation_constraints(self, field, value, expected_error):
        """Test that field validation constraints are enforced."""
        # Test non-negative constraints
        with pytest.raises(ValueError, match=expected_error):
            ProcessingMetrics(**{field: value})


    def test_processed_attachments_cannot_exceed_total(self):
        """Test that processed_attachments cannot exceed total_attachments."""
        with pytest.raises(ValueError, match="processed_attachments cannot exceed total_attachments"):
            ProcessingMetrics(
                total_attachments=10,
                processed_attachments=15
            )

    def test_processed_bytes_cannot_exceed_total(self):
        """Test that processed_bytes cannot exceed total_bytes."""
        with pytest.raises(ValueError, match="processed_bytes cannot exceed total_bytes"):
            ProcessingMetrics(
                total_bytes=1000,
                processed_bytes=1500
            )

    def test_validation_on_assignment(self):
        """Test that validation occurs when fields are reassigned."""
        metrics = ProcessingMetrics(total_attachments=10, total_bytes=1000)

        # Valid assignment
        metrics.processed_attachments = 5
        assert metrics.processed_attachments == 5

        # Invalid assignment should raise error
        with pytest.raises(ValueError, match="processed_attachments cannot exceed total_attachments"):
            metrics.processed_attachments = 15

    def test_overall_progress_calculation(self):
        """Test the overall_progress computed field calculation."""
        metrics = ProcessingMetrics(
            total_attachments=100,
            processed_attachments=75
        )

        assert metrics.overall_progress == 75.0

        # Test edge case: no attachments
        metrics_no_attachments = ProcessingMetrics()
        assert metrics_no_attachments.overall_progress == 100.0

        # Test edge case: all processed
        metrics_all_processed = ProcessingMetrics(
            total_attachments=50,
            processed_attachments=50
        )
        assert metrics_all_processed.overall_progress == 100.0

    def test_bytes_progress_calculation(self):
        """Test the bytes_progress computed field calculation."""
        metrics = ProcessingMetrics(
            total_bytes=1024,
            processed_bytes=512
        )

        assert metrics.bytes_progress == 50.0

        # Test edge case: no bytes
        metrics_no_bytes = ProcessingMetrics()
        assert metrics_no_bytes.bytes_progress == 100.0

        # Test edge case: all processed
        metrics_all_processed = ProcessingMetrics(
            total_bytes=1000,
            processed_bytes=1000
        )
        assert metrics_all_processed.bytes_progress == 100.0

    def test_elapsed_time_calculation(self):
        """Test the elapsed_time computed field calculation."""
        past_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        metrics = ProcessingMetrics(start_time=past_time)

        elapsed = metrics.elapsed_time
        assert elapsed >= 29.0  # Allow for small timing variations
        assert elapsed <= 31.0

    def test_estimated_remaining_time_calculation(self):
        """Test the estimated_remaining_time computed field calculation."""
        past_time = datetime.now(timezone.utc) - timedelta(seconds=10)
        metrics = ProcessingMetrics(
            total_attachments=100,
            processed_attachments=50,
            start_time=past_time
        )

        remaining = metrics.estimated_remaining_time
        assert remaining >= 9.0  # Allow for small timing variations
        assert remaining <= 11.0

        # Test edge case: no progress
        metrics_no_progress = ProcessingMetrics(start_time=past_time)
        assert metrics_no_progress.estimated_remaining_time == 0.0

        # Test edge case: completed
        metrics_completed = ProcessingMetrics(
            total_attachments=100,
            processed_attachments=100,
            start_time=past_time
        )
        assert metrics_completed.estimated_remaining_time == 0.0

    def test_json_serialization(self):
        """Test that the model can be serialized to JSON."""
        start_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        metrics = ProcessingMetrics(
            total_attachments=100,
            processed_attachments=50,
            total_bytes=1024,
            processed_bytes=512,
            start_time=start_time,
            current_attachment="test.pdf",
            current_attachment_progress=75.5,
            errors=["Error 1"]
        )

        json_data = metrics.model_dump_json()
        assert isinstance(json_data, str)

        # Verify datetime is serialized as ISO format (Pydantic v2 uses 'Z' for UTC)
        # Check for the date/time information rather than exact format
        assert "2023-01-01T12:00:00" in json_data
        # Verify it's timezone-aware (either +00:00 or Z)
        assert "+00:00" in json_data or "Z" in json_data

    def test_model_validation_with_partial_data(self):
        """Test that the model works with partial data updates."""
        metrics = ProcessingMetrics()

        # Update only some fields
        metrics.total_attachments = 50
        metrics.processed_attachments = 25

        assert metrics.total_attachments == 50
        assert metrics.processed_attachments == 25
        assert metrics.overall_progress == 50.0

    def test_error_list_handling(self):
        """Test that the errors list is properly handled."""
        metrics = ProcessingMetrics()

        # Add errors
        metrics.errors.append("First error")
        metrics.errors.append("Second error")

        assert len(metrics.errors) == 2
        assert "First error" in metrics.errors
        assert "Second error" in metrics.errors

        # Clear errors
        metrics.errors.clear()
        assert len(metrics.errors) == 0

    def test_current_attachment_progress_boundaries(self):
        """Test that current_attachment_progress respects 0-100 boundaries."""
        # Test valid values
        ProcessingMetrics(current_attachment_progress=0.0)
        ProcessingMetrics(current_attachment_progress=50.0)
        ProcessingMetrics(current_attachment_progress=100.0)

        # Test invalid values
        with pytest.raises(ValueError):
            ProcessingMetrics(current_attachment_progress=-0.1)

        with pytest.raises(ValueError):
            ProcessingMetrics(current_attachment_progress=100.1)

    def test_schema_extra_example(self):
        """Test that the schema_extra example is properly configured."""
        metrics = ProcessingMetrics()
        schema = metrics.model_json_schema()

        assert "example" in schema
        example = schema["example"]
        assert example["total_attachments"] == 100
        assert example["processed_attachments"] == 45
        assert example["total_bytes"] == 1073741824
        assert example["processed_bytes"] == 483183820
        assert example["current_attachment"] == "document.pdf"
        assert example["current_attachment_progress"] == 67.5
        assert example["errors"] == []

    @patch('fides.api.service.storage.schemas.datetime')
    def test_utcnow_usage(self, mock_datetime):
        """Test that datetime.now(timezone.utc) is used for default start_time."""
        mock_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now

        metrics = ProcessingMetrics()
        assert metrics.start_time == mock_now
        mock_datetime.now.assert_called_once_with(timezone.utc)

    def test_computed_fields_are_computed(self):
        """Test that computed fields are properly computed."""
        metrics = ProcessingMetrics()

        # These should return computed values, not be callable
        assert isinstance(metrics.overall_progress, float)
        assert isinstance(metrics.bytes_progress, float)
        assert isinstance(metrics.elapsed_time, float)
        assert isinstance(metrics.estimated_remaining_time, float)

        # They should return the expected default values
        assert metrics.overall_progress == 100.0  # No attachments = 100% progress
        assert metrics.bytes_progress == 100.0    # No bytes = 100% progress
        assert metrics.elapsed_time >= 0.0        # Should be non-negative
        assert metrics.estimated_remaining_time == 0.0  # No progress = 0 remaining time
