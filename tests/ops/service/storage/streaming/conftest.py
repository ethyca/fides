from unittest.mock import MagicMock, Mock, create_autospec

import pytest

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.service.storage.streaming.smart_open_client import SmartOpenStorageClient


@pytest.fixture
def mock_smart_open_client():
    """Create a mock smart-open storage client."""
    client = create_autospec(SmartOpenStorageClient)

    # Mock streaming methods
    mock_upload_stream = MagicMock()
    mock_upload_stream.__enter__ = Mock(return_value=mock_upload_stream)
    mock_upload_stream.__exit__ = Mock(return_value=None)
    mock_upload_stream.write = Mock()

    # Create a more realistic read stream that yields chunks
    mock_read_stream = MagicMock()
    mock_read_stream.__enter__ = Mock(return_value=mock_read_stream)
    mock_read_stream.__exit__ = Mock(return_value=None)

    # Simulate chunked reading - first call returns content, subsequent calls return empty
    chunk_content = b"mock_attachment_content"
    mock_read_stream.read = Mock(side_effect=[chunk_content, b""])

    # Ensure stream_upload returns the mock with context manager methods
    client.stream_upload.return_value = mock_upload_stream
    client.stream_read.return_value = mock_read_stream

    # Mock the generate_presigned_url method with a default return value
    client.generate_presigned_url = Mock(return_value="https://example.com/test.zip")

    return client


@pytest.fixture
def mock_smart_open_client_s3(mock_smart_open_client):
    """Create a mock SmartOpenStorageClient."""
    client = mock_smart_open_client
    client.storage_type = "s3"

    # Mock the generate_presigned_url method
    client.generate_presigned_url = Mock(return_value="https://example.com/test.zip")

    return client


@pytest.fixture
def mock_smart_open_client_gcs():
    """Create a mock SmartOpenStorageClient for GCS."""
    client = create_autospec(spec=SmartOpenStorageClient)
    client.storage_type = "gcs"

    # Mock the generate_presigned_url method to return a proper presigned URL
    client.generate_presigned_url = Mock(
        return_value="https://storage.googleapis.com/test-bucket/test.zip"
    )

    return client


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
def sample_data():
    """Sample data for testing."""
    return {
        "test_dataset": [
            {
                "id": "1",
                "name": "Test User",
                "email": "test@example.com",
                "attachments": [
                    {"filename": "doc1.pdf", "url": "https://example.com/doc1.pdf"},
                    {"filename": "doc2.pdf", "url": "https://example.com/doc2.pdf"},
                ],
            }
        ]
    }
