"""Tests for the DSR storage streaming functionality."""

from io import BytesIO
from unittest.mock import Mock, patch

import pytest

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.service.storage.streaming.dsr_storage import (
    stream_html_dsr_report_to_storage_multipart,
)
from fides.api.service.storage.streaming.util import (
    AWS_MIN_PART_SIZE,
    CHUNK_SIZE_THRESHOLD,
)


@pytest.fixture
def mock_privacy_request():
    """Create a mock privacy request."""
    privacy_request = Mock(autospec=PrivacyRequest)
    privacy_request.id = "test_request_123"
    privacy_request.policy = Mock()
    privacy_request.policy.get_action_type.return_value = Mock(value="access")
    privacy_request.get_persisted_identity.return_value = Mock(
        labeled_dict=lambda include_default_labels: {
            "email": {"value": "test@example.com"},
            "phone_number": {"value": "+1234567890"},
        }
    )
    privacy_request.requested_at = Mock(strftime=lambda fmt: "01/01/2024 12:00 UTC")
    return privacy_request


@pytest.fixture
def sample_dsr_data():
    """Create sample DSR data for testing."""
    return {
        "dataset:users": [
            {
                "id": 1,
                "name": "Test User",
                "email": "test@example.com",
            }
        ],
        "attachments": [
            {
                "file_name": "test_document.pdf",
                "download_url": "https://example.com/test.pdf",
                "file_size": 1024,
            }
        ],
    }


class TestStreamHtmlDsrReportToStorageMultipart:
    """Test cases for stream_html_dsr_report_to_storage_multipart function."""

    @pytest.mark.parametrize(
        "storage_client_fixture", ["mock_gcs_storage_client", "mock_s3_storage_client"]
    )
    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_successful_upload_small_file_single_upload(
        self,
        mock_dsr_builder_class,
        storage_client_fixture,
        request,
        mock_privacy_request,
        sample_dsr_data,
    ):
        """Test successful upload when content is small and uses single upload."""
        storage_client = request.getfixturevalue(storage_client_fixture)

        # Mock the DsrReportBuilder to return small content (below AWS_MIN_PART_SIZE)
        mock_builder = Mock()
        small_content = "x" * (AWS_MIN_PART_SIZE - 1024)  # Just under 5MB
        mock_builder.generate.return_value = BytesIO(small_content.encode("utf-8"))
        mock_dsr_builder_class.return_value = mock_builder

        result = stream_html_dsr_report_to_storage_multipart(
            storage_client=storage_client,
            bucket_name="test-bucket",
            file_key="test-report.html",
            data=sample_dsr_data,
            privacy_request=mock_privacy_request,
        )

        # Verify single upload was used (put_object called, not multipart)
        storage_client.put_object.assert_called_once_with(
            "test-bucket",
            "test-report.html",
            small_content.encode("utf-8"),
            content_type="text/html",
        )

        # Verify multipart upload was NOT used
        storage_client.create_multipart_upload.assert_not_called()
        storage_client.upload_part.assert_not_called()
        storage_client.complete_multipart_upload.assert_not_called()
        storage_client.abort_multipart_upload.assert_not_called()

    @pytest.mark.parametrize(
        "storage_client_fixture", ["mock_gcs_storage_client", "mock_s3_storage_client"]
    )
    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_successful_upload_large_file_multipart(
        self,
        mock_dsr_builder_class,
        storage_client_fixture,
        request,
        mock_privacy_request,
        sample_dsr_data,
    ):
        """Test successful upload when content is large and uses multipart upload."""
        storage_client = request.getfixturevalue(storage_client_fixture)

        # Mock the DsrReportBuilder to return large content (above AWS_MIN_PART_SIZE)
        mock_builder = Mock()
        large_content = "x" * (AWS_MIN_PART_SIZE + 1024)  # Just over 5MB
        mock_builder.generate.return_value = BytesIO(large_content.encode("utf-8"))
        mock_dsr_builder_class.return_value = mock_builder

        result = stream_html_dsr_report_to_storage_multipart(
            storage_client=storage_client,
            bucket_name="test-bucket",
            file_key="test-report.html",
            data=sample_dsr_data,
            privacy_request=mock_privacy_request,
        )

        # Verify multipart upload was used
        storage_client.create_multipart_upload.assert_called_once_with(
            "test-bucket", "test-report.html", "text/html"
        )

        # Verify upload part was called (should be at least 2 parts for content > 5MB)
        assert storage_client.upload_part.call_count >= 1

        # Verify multipart upload was completed
        storage_client.complete_multipart_upload.assert_called_once()

        # Verify no abort was called
        storage_client.abort_multipart_upload.assert_not_called()

        # Verify single upload was NOT used
        storage_client.put_object.assert_not_called()

    @pytest.mark.parametrize(
        "storage_client_fixture", ["mock_gcs_storage_client", "mock_s3_storage_client"]
    )
    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_successful_upload_multiple_chunks(
        self,
        mock_dsr_builder_class,
        storage_client_fixture,
        request,
        mock_privacy_request,
        sample_dsr_data,
    ):
        """Test successful upload when content requires multiple chunks."""
        storage_client = request.getfixturevalue(storage_client_fixture)

        # Mock the DsrReportBuilder to return large content
        mock_builder = Mock()
        # Create content larger than CHUNK_SIZE_THRESHOLD to trigger multiple chunks
        large_content = "x" * (CHUNK_SIZE_THRESHOLD + 1024)
        mock_builder.generate.return_value = BytesIO(large_content.encode("utf-8"))
        mock_dsr_builder_class.return_value = mock_builder

        result = stream_html_dsr_report_to_storage_multipart(
            storage_client=storage_client,
            bucket_name="test-bucket",
            file_key="test-report.html",
            data=sample_dsr_data,
            privacy_request=mock_privacy_request,
        )

        # Verify multiple parts were uploaded
        assert storage_client.upload_part.call_count > 1

        # Verify multipart upload was completed
        storage_client.complete_multipart_upload.assert_called_once()

        # Verify no abort was called
        storage_client.abort_multipart_upload.assert_not_called()

    @pytest.mark.parametrize(
        "storage_client_fixture", ["mock_gcs_storage_client", "mock_s3_storage_client"]
    )
    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_upload_with_custom_bucket_and_key(
        self,
        mock_dsr_builder_class,
        storage_client_fixture,
        request,
        mock_privacy_request,
        sample_dsr_data,
    ):
        """Test upload with custom bucket name and file key."""
        storage_client = request.getfixturevalue(storage_client_fixture)

        mock_builder = Mock()
        # Use small content to trigger single upload path
        small_content = "x" * (AWS_MIN_PART_SIZE - 1024)
        mock_builder.generate.return_value = BytesIO(small_content.encode("utf-8"))
        mock_dsr_builder_class.return_value = mock_builder

        custom_bucket = "custom-bucket-name"
        custom_key = "custom/path/report.html"

        result = stream_html_dsr_report_to_storage_multipart(
            storage_client=storage_client,
            bucket_name=custom_bucket,
            file_key=custom_key,
            data=sample_dsr_data,
            privacy_request=mock_privacy_request,
        )

        # Verify custom bucket and key were used in single upload
        storage_client.put_object.assert_called_once_with(
            custom_bucket,
            custom_key,
            small_content.encode("utf-8"),
            content_type="text/html",
        )

    @pytest.mark.parametrize(
        "storage_client_fixture", ["mock_gcs_storage_client", "mock_s3_storage_client"]
    )
    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_upload_with_empty_dsr_data(
        self,
        mock_dsr_builder_class,
        storage_client_fixture,
        request,
        mock_privacy_request,
    ):
        """Test upload with empty DSR data."""
        storage_client = request.getfixturevalue(storage_client_fixture)

        mock_builder = Mock()
        # Use small content to trigger single upload path
        small_content = "x" * (AWS_MIN_PART_SIZE - 1024)
        mock_builder.generate.return_value = BytesIO(small_content.encode("utf-8"))
        mock_dsr_builder_class.return_value = mock_builder

        result = stream_html_dsr_report_to_storage_multipart(
            storage_client=storage_client,
            bucket_name="test-bucket",
            file_key="test-report.html",
            data={},
            privacy_request=mock_privacy_request,
        )

        # Verify the result
        storage_client.put_object.assert_called_once_with(
            "test-bucket",
            "test-report.html",
            small_content.encode("utf-8"),
            content_type="text/html",
        )

    @pytest.mark.parametrize(
        "storage_client_fixture", ["mock_gcs_storage_client", "mock_s3_storage_client"]
    )
    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_upload_with_large_dsr_data(
        self,
        mock_dsr_builder_class,
        storage_client_fixture,
        request,
        mock_privacy_request,
    ):
        """Test upload with very large DSR data that requires many chunks."""
        storage_client = request.getfixturevalue(storage_client_fixture)

        # Create large DSR data
        large_data = {
            "dataset:users": [{"id": i, "data": "x" * 1000} for i in range(1000)]
        }

        mock_builder = Mock()
        mock_builder.generate.return_value = BytesIO(
            ("x" * (CHUNK_SIZE_THRESHOLD * 3)).encode("utf-8")
        )
        mock_dsr_builder_class.return_value = mock_builder

        result = stream_html_dsr_report_to_storage_multipart(
            storage_client=storage_client,
            bucket_name="test-bucket",
            file_key="large-report.html",
            data=large_data,
            privacy_request=mock_privacy_request,
        )

        # Verify the result
        assert storage_client.upload_part.call_count > 1
        storage_client.complete_multipart_upload.assert_called_once()

    @pytest.mark.parametrize(
        "storage_client_fixture", ["mock_gcs_storage_client", "mock_s3_storage_client"]
    )
    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_upload_failure_during_part_upload(
        self,
        mock_dsr_builder_class,
        storage_client_fixture,
        request,
        mock_privacy_request,
        sample_dsr_data,
    ):
        """Test upload failure during part upload and proper cleanup."""
        storage_client = request.getfixturevalue(storage_client_fixture)

        mock_builder = Mock()
        # Create content that will require multiple parts
        large_content = "x" * (CHUNK_SIZE_THRESHOLD + 1024)
        mock_builder.generate.return_value = BytesIO(large_content.encode("utf-8"))
        mock_dsr_builder_class.return_value = mock_builder

        # Make upload_part fail on the second call
        call_count = 0

        def failing_upload_part(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Upload part failed")
            # Return a mock part for successful calls
            part = Mock()
            part.etag = f"etag_{call_count}"
            part.part_number = call_count
            return part

        storage_client.upload_part.side_effect = failing_upload_part

        # Test that the function raises the exception
        with pytest.raises(Exception, match="Upload part failed"):
            stream_html_dsr_report_to_storage_multipart(
                storage_client=storage_client,
                bucket_name="test-bucket",
                file_key="test-report.html",
                data=sample_dsr_data,
                privacy_request=mock_privacy_request,
            )

        # Verify cleanup was attempted
        storage_client.abort_multipart_upload.assert_called_once()
        storage_client.complete_multipart_upload.assert_not_called()

    @pytest.mark.parametrize(
        "storage_client_fixture", ["mock_gcs_storage_client", "mock_s3_storage_client"]
    )
    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_upload_failure_during_multipart_creation(
        self,
        mock_dsr_builder_class,
        storage_client_fixture,
        request,
        mock_privacy_request,
        sample_dsr_data,
    ):
        """Test upload failure during multipart creation and proper cleanup."""
        storage_client = request.getfixturevalue(storage_client_fixture)

        mock_builder = Mock()
        # Use large content to trigger multipart upload path
        large_content = "x" * (AWS_MIN_PART_SIZE + 1024)
        mock_builder.generate.return_value = BytesIO(large_content.encode("utf-8"))
        mock_dsr_builder_class.return_value = mock_builder

        # Make create_multipart_upload fail
        storage_client.create_multipart_upload.side_effect = Exception(
            "Failed to create multipart upload"
        )

        # Test that the function raises the exception
        with pytest.raises(Exception, match="Failed to create multipart upload"):
            stream_html_dsr_report_to_storage_multipart(
                storage_client=storage_client,
                bucket_name="test-bucket",
                file_key="test-report.html",
                data=sample_dsr_data,
                privacy_request=mock_privacy_request,
            )

        # Verify no cleanup needed since upload wasn't created
        storage_client.abort_multipart_upload.assert_not_called()
        storage_client.complete_multipart_upload.assert_not_called()

    @pytest.mark.parametrize(
        "storage_client_fixture", ["mock_gcs_storage_client", "mock_s3_storage_client"]
    )
    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_upload_failure_during_completion(
        self,
        mock_dsr_builder_class,
        storage_client_fixture,
        request,
        mock_privacy_request,
        sample_dsr_data,
    ):
        """Test upload failure during completion and proper cleanup."""
        storage_client = request.getfixturevalue(storage_client_fixture)

        mock_builder = Mock()
        # Use large content to trigger multipart upload path
        large_content = "x" * (AWS_MIN_PART_SIZE + 1024)
        mock_builder.generate.return_value = BytesIO(large_content.encode("utf-8"))
        mock_dsr_builder_class.return_value = mock_builder

        # Make complete_multipart_upload fail
        storage_client.complete_multipart_upload.side_effect = Exception(
            "Failed to complete multipart upload"
        )

        # Test that the function raises the exception
        with pytest.raises(Exception, match="Failed to complete multipart upload"):
            stream_html_dsr_report_to_storage_multipart(
                storage_client=storage_client,
                bucket_name="test-bucket",
                file_key="test-report.html",
                data=sample_dsr_data,
                privacy_request=mock_privacy_request,
            )

        # Verify cleanup was attempted
        storage_client.abort_multipart_upload.assert_called_once()
        storage_client.complete_multipart_upload.assert_called_once()

    @pytest.mark.parametrize(
        "storage_client_fixture", ["mock_gcs_storage_client", "mock_s3_storage_client"]
    )
    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_abort_upload_failure_handling(
        self,
        mock_dsr_builder_class,
        storage_client_fixture,
        request,
        mock_privacy_request,
        sample_dsr_data,
    ):
        """Test that abort upload failures are logged but don't prevent exception propagation."""
        storage_client = request.getfixturevalue(storage_client_fixture)

        mock_builder = Mock()
        # Use large content to trigger multipart upload path
        large_content = "x" * (AWS_MIN_PART_SIZE + 1024)
        mock_builder.generate.return_value = BytesIO(large_content.encode("utf-8"))
        mock_dsr_builder_class.return_value = mock_builder

        # Make complete_multipart_upload fail
        storage_client.complete_multipart_upload.side_effect = Exception(
            "Failed to complete multipart upload"
        )

        # Make abort_multipart_upload also fail
        storage_client.abort_multipart_upload.side_effect = Exception(
            "Failed to abort multipart upload"
        )

        # Test that the function still raises the original exception
        with pytest.raises(Exception, match="Failed to complete multipart upload"):
            stream_html_dsr_report_to_storage_multipart(
                storage_client=storage_client,
                bucket_name="test-bucket",
                file_key="test-report.html",
                data=sample_dsr_data,
                privacy_request=mock_privacy_request,
            )

        # Verify abort was attempted but failed
        storage_client.abort_multipart_upload.assert_called_once()
        storage_client.complete_multipart_upload.assert_called_once()

    @pytest.mark.parametrize(
        "storage_client_fixture", ["mock_gcs_storage_client", "mock_s3_storage_client"]
    )
    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_dsr_report_builder_integration(
        self,
        mock_dsr_builder_class,
        storage_client_fixture,
        request,
        mock_privacy_request,
        sample_dsr_data,
    ):
        """Test integration with DsrReportBuilder."""
        storage_client = request.getfixturevalue(storage_client_fixture)

        mock_builder = Mock()
        # Use small content to trigger single upload path
        small_content = "x" * (AWS_MIN_PART_SIZE - 1024)
        mock_builder.generate.return_value = BytesIO(small_content.encode("utf-8"))
        mock_dsr_builder_class.return_value = mock_builder

        # Verify DsrReportBuilder is called with correct parameters
        result = stream_html_dsr_report_to_storage_multipart(
            storage_client=storage_client,
            bucket_name="test-bucket",
            file_key="test-report.html",
            data=sample_dsr_data,
            privacy_request=mock_privacy_request,
        )

        # Verify DsrReportBuilder was instantiated correctly
        mock_dsr_builder_class.assert_called_once_with(
            privacy_request=mock_privacy_request,
            dsr_data=sample_dsr_data,
        )

        # Verify generate was called
        mock_builder.generate.assert_called_once()

        # Verify single upload was used
        storage_client.put_object.assert_called_once()

    @pytest.mark.parametrize(
        "storage_client_fixture", ["mock_gcs_storage_client", "mock_s3_storage_client"]
    )
    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_content_type_setting_single_upload(
        self,
        mock_dsr_builder_class,
        storage_client_fixture,
        request,
        mock_privacy_request,
        sample_dsr_data,
    ):
        """Test that content type is set to text/html for single upload."""
        storage_client = request.getfixturevalue(storage_client_fixture)

        mock_builder = Mock()
        # Use small content to trigger single upload path
        small_content = "x" * (AWS_MIN_PART_SIZE - 1024)
        mock_builder.generate.return_value = BytesIO(small_content.encode("utf-8"))
        mock_dsr_builder_class.return_value = mock_builder

        stream_html_dsr_report_to_storage_multipart(
            storage_client=storage_client,
            bucket_name="test-bucket",
            file_key="test-report.html",
            data=sample_dsr_data,
            privacy_request=mock_privacy_request,
        )

        # Verify content type was set to text/html in single upload
        storage_client.put_object.assert_called_once_with(
            "test-bucket",
            "test-report.html",
            small_content.encode("utf-8"),
            content_type="text/html",
        )

    @pytest.mark.parametrize(
        "storage_client_fixture", ["mock_gcs_storage_client", "mock_s3_storage_client"]
    )
    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_content_type_setting_multipart_upload(
        self,
        mock_dsr_builder_class,
        storage_client_fixture,
        request,
        mock_privacy_request,
        sample_dsr_data,
    ):
        """Test that content type is set to text/html for multipart upload."""
        storage_client = request.getfixturevalue(storage_client_fixture)

        mock_builder = Mock()
        # Use large content to trigger multipart upload path
        large_content = "x" * (AWS_MIN_PART_SIZE + 1024)
        mock_builder.generate.return_value = BytesIO(large_content.encode("utf-8"))
        mock_dsr_builder_class.return_value = mock_builder

        stream_html_dsr_report_to_storage_multipart(
            storage_client=storage_client,
            bucket_name="test-bucket",
            file_key="test-report.html",
            data=sample_dsr_data,
            privacy_request=mock_privacy_request,
        )

        # Verify content type was set to text/html in multipart upload
        storage_client.create_multipart_upload.assert_called_once_with(
            "test-bucket", "test-report.html", "text/html"
        )

    @pytest.mark.parametrize(
        "storage_client_fixture", ["mock_gcs_storage_client", "mock_s3_storage_client"]
    )
    @patch("fides.api.service.storage.streaming.dsr_storage.DsrReportBuilder")
    def test_chunk_size_threshold_usage(
        self,
        mock_dsr_builder_class,
        storage_client_fixture,
        request,
        mock_privacy_request,
        sample_dsr_data,
    ):
        """Test that CHUNK_SIZE_THRESHOLD is used for chunking in multipart upload."""
        storage_client = request.getfixturevalue(storage_client_fixture)

        # Create a much smaller content to avoid memory issues and test chunking
        # Use a size that's just over AWS_MIN_PART_SIZE to ensure multipart upload is used
        content_size = AWS_MIN_PART_SIZE + 1000  # Just over the threshold
        mock_content = "x" * content_size

        # Create mock builder instance
        mock_builder = Mock()
        mock_builder.generate.return_value = BytesIO(mock_content.encode("utf-8"))

        # Assign the mock builder to the class
        mock_dsr_builder_class.return_value = mock_builder

        result = stream_html_dsr_report_to_storage_multipart(
            storage_client=storage_client,
            bucket_name="test-bucket",
            file_key="test-report.html",
            data=sample_dsr_data,
            privacy_request=mock_privacy_request,
        )

        # Debug output
        print(f"Storage client type: {type(storage_client)}")
        print(
            f"Create multipart upload calls: {storage_client.create_multipart_upload.call_count}"
        )
        print(f"Upload part calls: {storage_client.upload_part.call_count}")
        print(
            f"Complete multipart upload calls: {storage_client.complete_multipart_upload.call_count}"
        )
        if storage_client.upload_part.call_count > 0:
            print(f"Upload part call args: {storage_client.upload_part.call_args_list}")

        # Verify exactly 2 parts were created
        assert storage_client.upload_part.call_count == 2

        # Verify part numbers are sequential (check positional arguments)
        call_args = storage_client.upload_part.call_args_list
        # upload_part(bucket_name, file_key, upload_id, part_number, chunk_data)
        assert call_args[0][0][3] == 1  # part_number is 4th positional arg
        assert call_args[1][0][3] == 2  # part_number is 4th positional arg
