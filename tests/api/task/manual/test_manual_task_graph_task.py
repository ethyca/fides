from unittest.mock import Mock, patch

import pytest

from fides.api.models.attachment import AttachmentType
from fides.api.models.manual_task import (
    ManualTaskFieldType,
    ManualTaskInstance,
    ManualTaskSubmission,
)
from fides.api.task.manual.manual_task_graph_task import ManualTaskGraphTask


class TestManualTaskDataAggregation:
    """Test the data aggregation methods in ManualTaskGraphTask"""

    @pytest.fixture
    def manual_task_instance_with_field(
        self, db, access_privacy_request, connection_with_manual_access_task
    ):
        """Create a manual task instance with proper field setup"""
        _, manual_task, config, field = connection_with_manual_access_task
        return ManualTaskInstance.create(
            db=db,
            data={
                "task_id": manual_task.id,
                "config_id": config.id,
                "entity_id": access_privacy_request.id,
                "entity_type": "privacy_request",
                "status": "pending",
            },
        )

    def test_aggregate_submission_data_empty_instances(self, manual_task_graph_task):
        """Test aggregation with empty instances list"""
        result = manual_task_graph_task._aggregate_submission_data([])
        assert result == {}

    def test_aggregate_submission_data_no_submissions(
        self, manual_task_graph_task, manual_task_instance_with_field
    ):
        """Test aggregation with instances that have no submissions"""
        result = manual_task_graph_task._aggregate_submission_data(
            [manual_task_instance_with_field]
        )
        assert result == {}

    def test_aggregate_submission_data_text_field(
        self, manual_task_graph_task, manual_task_submission_text
    ):
        """Test aggregation with text field submission"""
        # Get the instance from the submission
        instance = manual_task_submission_text.instance

        result = manual_task_graph_task._aggregate_submission_data([instance])

        assert "user_email" in result
        assert result["user_email"] == "user@example.com"

    def test_aggregate_submission_data_checkbox_field(
        self, manual_task_graph_task, manual_task_submission_checkbox
    ):
        """Test aggregation with checkbox field submission"""
        # Get the instance from the submission
        instance = manual_task_submission_checkbox.instance

        result = manual_task_graph_task._aggregate_submission_data([instance])

        assert "user_email" in result
        assert result["user_email"] is True

    def test_aggregate_submission_data_multiple_instances(
        self,
        manual_task_graph_task,
        manual_task_submission_text,
        manual_task_submission_checkbox,
    ):
        """Test aggregation with multiple instances"""
        instance1 = manual_task_submission_text.instance
        instance2 = manual_task_submission_checkbox.instance

        result = manual_task_graph_task._aggregate_submission_data(
            [instance1, instance2]
        )

        # Should have data from both instances
        assert "user_email" in result
        # The last instance processed will overwrite the first one with the same field_key
        assert result["user_email"] is True

    def test_aggregate_submission_data_invalid_submission_data(
        self,
        manual_task_graph_task,
        manual_task_instance_with_field,
        connection_with_manual_access_task,
    ):
        """Test aggregation with invalid submission data"""
        # Get the field from the connection setup
        _, _, config, field = connection_with_manual_access_task

        # Create a submission with invalid data structure
        submission = ManualTaskSubmission(
            task_id=manual_task_instance_with_field.task_id,
            config_id=manual_task_instance_with_field.config_id,
            field_id=field.id,
            instance_id=manual_task_instance_with_field.id,
            submitted_by=None,
            data="invalid_data",  # Not a dict
        )
        manual_task_instance_with_field.submissions = [submission]

        result = manual_task_graph_task._aggregate_submission_data(
            [manual_task_instance_with_field]
        )
        assert result == {}

    def test_aggregate_submission_data_missing_field_key(
        self,
        manual_task_graph_task,
        manual_task_instance_with_field,
        connection_with_manual_access_task,
    ):
        """Test aggregation with submission missing field_key"""
        # Get the field from the connection setup
        _, _, config, field = connection_with_manual_access_task

        # Create a submission with field but no field_key
        submission = ManualTaskSubmission(
            task_id=manual_task_instance_with_field.task_id,
            config_id=manual_task_instance_with_field.config_id,
            field_id=field.id,
            instance_id=manual_task_instance_with_field.id,
            submitted_by=None,
            data={"field_type": ManualTaskFieldType.text.value, "value": "test"},
        )
        # Temporarily set field_key to None for testing (will be restored)
        original_field_key = field.field_key
        field.field_key = None
        submission.field = field
        manual_task_instance_with_field.submissions = [submission]

        result = manual_task_graph_task._aggregate_submission_data(
            [manual_task_instance_with_field]
        )
        assert result == {}

        # Restore the original field_key
        field.field_key = original_field_key

    @patch("fides.api.task.manual.manual_task_graph_task.format_size")
    def test_process_attachment_field_success(
        self,
        mock_format_size,
        manual_task_graph_task,
        manual_task_submission_attachment,
        attachment_for_access_package,
    ):
        """Test successful attachment field processing"""
        mock_format_size.return_value = "1.2 KB"

        # Mock the attachment retrieval
        with patch.object(
            attachment_for_access_package, "retrieve_attachment"
        ) as mock_retrieve:
            mock_retrieve.return_value = (1234, "https://example.com/file.pdf")

            result = manual_task_graph_task._process_attachment_field(
                manual_task_submission_attachment
            )

            assert result is not None
            assert "test_document.pdf" in result
            assert result["test_document.pdf"]["url"] == "https://example.com/file.pdf"
            assert result["test_document.pdf"]["size"] == "1.2 KB"

    def test_process_attachment_field_no_attachments(
        self, manual_task_graph_task, manual_task_submission_attachment
    ):
        """Test attachment field processing with no attachments"""
        # Clear attachments
        manual_task_submission_attachment.attachments = []

        result = manual_task_graph_task._process_attachment_field(
            manual_task_submission_attachment
        )
        assert result is None

    def test_process_attachment_field_wrong_attachment_type(
        self,
        manual_task_graph_task,
        manual_task_submission_attachment,
        attachment_for_access_package,
    ):
        """Test attachment field processing with wrong attachment type"""
        # Change the attachment type to internal_use_only (not include_with_access_package)
        attachment_for_access_package.attachment_type = "internal_use_only"

        result = manual_task_graph_task._process_attachment_field(
            manual_task_submission_attachment
        )
        assert result is None

    @patch("fides.api.task.manual.manual_task_graph_task.logger")
    def test_process_attachment_field_retrieval_error(
        self,
        mock_logger,
        manual_task_graph_task,
        manual_task_submission_attachment,
        attachment_for_access_package,
    ):
        """Test attachment field processing with retrieval error"""
        # Mock the attachment retrieval to raise an exception
        with patch.object(
            attachment_for_access_package, "retrieve_attachment"
        ) as mock_retrieve:
            mock_retrieve.side_effect = Exception("Storage error")

            result = manual_task_graph_task._process_attachment_field(
                manual_task_submission_attachment
            )

            # Should log warning and continue
            mock_logger.warning.assert_called_once()
            assert result is None

    @patch("fides.api.task.manual.manual_task_graph_task.format_size")
    def test_process_attachment_field_multiple_attachments(
        self,
        mock_format_size,
        manual_task_graph_task,
        manual_task_submission_attachment,
        multiple_attachments_for_access,
    ):
        """Test attachment field processing with multiple attachments"""
        mock_format_size.return_value = "2.5 KB"

        # Mock the attachment retrieval for multiple attachments
        with (
            patch.object(
                multiple_attachments_for_access[0], "retrieve_attachment"
            ) as mock_retrieve1,
            patch.object(
                multiple_attachments_for_access[1], "retrieve_attachment"
            ) as mock_retrieve2,
        ):

            mock_retrieve1.return_value = (2560, "https://example.com/doc1.pdf")
            mock_retrieve2.return_value = (1024, "https://example.com/doc2.pdf")

            result = manual_task_graph_task._process_attachment_field(
                manual_task_submission_attachment
            )

            assert result is not None
            assert "document1.pdf" in result
            assert "document2.pdf" in result
            assert result["document1.pdf"]["url"] == "https://example.com/doc1.pdf"
            assert result["document2.pdf"]["url"] == "https://example.com/doc2.pdf"
            assert result["document1.pdf"]["size"] == "2.5 KB"
            assert result["document2.pdf"]["size"] == "2.5 KB"

    def test_aggregate_submission_data_with_attachment_field(
        self,
        manual_task_graph_task,
        manual_task_submission_attachment,
        attachment_for_access_package,
    ):
        """Test aggregation with attachment field submission"""
        # Get the instance from the submission
        instance = manual_task_submission_attachment.instance

        # Mock the attachment retrieval
        with patch.object(
            attachment_for_access_package, "retrieve_attachment"
        ) as mock_retrieve:
            mock_retrieve.return_value = (1234, "https://example.com/file.pdf")

            result = manual_task_graph_task._aggregate_submission_data([instance])

            # Should process attachment field
            assert "user_email" in result
            assert isinstance(result["user_email"], dict)
            assert "test_document.pdf" in result["user_email"]

    def test_aggregate_submission_data_mixed_field_types(
        self,
        manual_task_graph_task,
        manual_task_submission_text,
        manual_task_submission_attachment,
        attachment_for_access_package,
    ):
        """Test aggregation with mixed field types (text and attachment)"""
        instance1 = manual_task_submission_text.instance
        instance2 = manual_task_submission_attachment.instance

        # Mock the attachment retrieval
        with patch.object(
            attachment_for_access_package, "retrieve_attachment"
        ) as mock_retrieve:
            mock_retrieve.return_value = (1234, "https://example.com/file.pdf")

            result = manual_task_graph_task._aggregate_submission_data(
                [instance1, instance2]
            )

            # Should have both text and attachment data
            assert "user_email" in result
            # The last instance processed will overwrite the first one with the same field_key
            assert isinstance(result["user_email"], dict)
            assert "test_document.pdf" in result["user_email"]

    def test_aggregate_submission_data_attachment_field_no_attachments(
        self, manual_task_graph_task, manual_task_submission_attachment
    ):
        """Test aggregation with attachment field but no attachments"""
        # Get the instance from the submission
        instance = manual_task_submission_attachment.instance

        # Clear attachments
        manual_task_submission_attachment.attachments = []

        result = manual_task_graph_task._aggregate_submission_data([instance])

        # Should return None for attachment field with no attachments
        assert "user_email" in result
        assert result["user_email"] is None
